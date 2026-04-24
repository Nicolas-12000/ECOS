#!/usr/bin/env python3

import argparse
import datetime as dt
import re
import unicodedata
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql import Window

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "full"
DEFAULT_SIVIGILA = REPO_ROOT / "data/raw/sivigila_4hyg-wa9d.csv"
DEFAULT_CLIMATE = REPO_ROOT / "data/raw/clima_normales_ideam_nsz2-kzcq.csv"
DEFAULT_VACCINATION = REPO_ROOT / "data/raw/vacunacion_6i25-2hdt.csv"
DEFAULT_RIPS = REPO_ROOT / "data/raw/rips_5e6c-5p2c.csv"
DEFAULT_MOBILITY = REPO_ROOT / "data/raw/movilidad_nacional_eh75-8ah6.csv"

FEATURES_ALL = {"vaccination", "rips", "mobility", "signals"}

MONTHS = [
    ("ene", 1),
    ("feb", 2),
    ("mar", 3),
    ("abr", 4),
    ("may", 5),
    ("jun", 6),
    ("jul", 7),
    ("ago", 8),
    ("sep", 9),
    ("oct", 10),
    ("nov", 11),
    ("dic", 12),
]

PARAM_MAP = {
    "PRECIPITACION": "precipitation_mm",
    "TEMPERATURA MINIMA": "temp_min_c",
    "TEMPERATURA MEDIA": "temp_avg_c",
    "TEMPERATURA MAXIMA": "temp_max_c",
    "HUMEDAD RELATIVA": "humidity_avg_pct",
}

CANONICAL_EVENT = {
    "dengue": (210, "DENGUE"),
    "chikungunya": (895, "CHIKUNGUNYA"),
    "zika": (862, "ZIKA"),
    "malaria": (830, "MALARIA"),
}

REGION_MAP = {
    # Caribe
    "ATLANTICO": "CARIBE", "BOLIVAR": "CARIBE", "CESAR": "CARIBE", "CORDOBA": "CARIBE", 
    "LA GUAJIRA": "CARIBE", "MAGDALENA": "CARIBE", "SUCRE": "CARIBE", 
    "ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA": "CARIBE",
    # Pacifico
    "CAUCA": "PACIFICO", "CHOCO": "PACIFICO", "NARINO": "PACIFICO", "VALLE DEL CAUCA": "PACIFICO",
    # Andina
    "ANTIOQUIA": "ANDINA", "BOYACA": "ANDINA", "CALDAS": "ANDINA", "CUNDINAMARCA": "ANDINA", 
    "HUILA": "ANDINA", "NORTE DE SANTANDER": "ANDINA", "QUINDIO": "ANDINA", "RISARALDA": "ANDINA", 
    "SANTANDER": "ANDINA", "TOLIMA": "ANDINA", "BOGOTA": "ANDINA",
    # Orinoquia
    "ARAUCA": "ORINOQUIA", "CASANARE": "ORINOQUIA", "META": "ORINOQUIA", "VICHADA": "ORINOQUIA",
    # Amazonia
    "AMAZONAS": "AMAZONIA", "CAQUETA": "AMAZONIA", "GUAINIA": "AMAZONIA", "GUAVIARE": "AMAZONIA", 
    "PUTUMAYO": "AMAZONIA", "VAUPES": "AMAZONIA"
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace(".", " ")
    value = " ".join(value.upper().split())
    return value


def normalize_dane_code(value: str | None, size: int) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    if not digits:
        return None
    if len(digits) > size:
        digits = digits[-size:]
    return digits.zfill(size)


def normalize_column_name(value: str) -> str:
    normalized = normalize_text(value)
    cleaned = []
    for ch in normalized:
        if ch.isalnum():
            cleaned.append(ch.lower())
        else:
            cleaned.append("_")
    result = "".join(cleaned)
    while "__" in result:
        result = result.replace("__", "_")
    return result.strip("_")


def spark_normalize_text(col):
    """Native PySpark string normalization (no Python UDF)"""
    # Lista extendida de acentos y caracteres especiales comunes en datasets de Colombia
    accents = "ÁÉÍÓÚáéíóúÀÈÌÒÙàèìòùÄËÏÖÜäëïöüÂÊÎÔÛâêôûÑñ"
    replacements = "AEIOUaeiouAEIOUaeiouAEIOUaeiouAEIOUaeiouNn"
    c = F.translate(col, accents, replacements)
    c = F.regexp_replace(c, r"\.", " ")
    # Eliminar cualquier carácter que no sea A-Z, 0-9 o espacio (esto limpia  y otros fallos de encoding)
    c = F.regexp_replace(c, r"[^a-zA-Z0-9\s]", "")
    c = F.trim(F.regexp_replace(c, r"\s+", " "))
    c = F.upper(c)
    
    # Manejar variaciones específicas de nombres de departamentos
    c = F.when(c.contains("VALLE"), F.lit("VALLE DEL CAUCA")) \
         .when(c.isin("BOGOTA DC", "BOGOTA D C", "SANTAFE DE BOGOTA"), F.lit("BOGOTA")) \
         .when(c.contains("SAN ANDRES"), F.lit("ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA")) \
         .when(c == "NORTE SANTANDER", F.lit("NORTE DE SANTANDER")) \
         .otherwise(c)
    return c


def spark_iso_week_start(year_col_name, week_col_name):
    """Native PySpark ISO week start date parsing (robust to Spark 3.x)"""
    jan4 = F.to_date(F.concat(F.col(year_col_name).cast("string"), F.lit("-01-04")))
    # Monday of the week containing Jan 4th is the start of ISO week 1
    week1_monday = F.next_day(F.date_sub(jan4, 7), "Monday")
    return F.date_add(week1_monday, (F.col(week_col_name).cast("int") - 1) * 7)


def spark_iso_week_end(year_col_name, week_col_name):
    """Native PySpark ISO week end date parsing"""
    return F.date_add(spark_iso_week_start(year_col_name, week_col_name), 6)


def build_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
        .config("spark.sql.ansi.enabled", "false")
        .getOrCreate()
    )


def default_output(_version: str, suffix: str) -> str:
    # Single canonical output to avoid excessive dataset versioning.
    return str(REPO_ROOT / f"data/processed/curated_weekly_{suffix}")


def resolve_features(raw_features: str | None) -> set[str]:
    if not raw_features:
        return set(FEATURES_ALL)

    tokens = {item.strip().lower() for item in raw_features.split(",") if item.strip()}
    if "all" in tokens:
        return set(FEATURES_ALL)
    if "none" in tokens:
        return set()

    unknown = tokens - FEATURES_ALL
    if unknown:
        print(f"[warn] unknown features ignored: {sorted(unknown)}")
    return tokens & FEATURES_ALL


def read_csv_if_exists(spark: SparkSession, path: str, encoding: str = "utf-8"):
    if not path:
        return None
    if not Path(path).exists():
        print(f"[skip] missing file: {path}")
        return None
    return (
        spark.read
        .option("header", True)
        .option("inferSchema", False)
        .option("encoding", encoding)
        .csv(path)
    )


def resolve_col(columns: list[str], candidates: list[str]) -> str | None:
    for name in candidates:
        if name in columns:
            return name
    # Case insensitive fallback
    lower_cols = {c.lower(): c for c in columns}
    for name in candidates:
        if name.lower() in lower_cols:
            return lower_cols[name.lower()]
    return None


def parse_date(col_name):
    # Use to_date fallbacks for broad compatibility across Spark builds.
    raw = F.split(F.trim(F.col(col_name).cast("string")), " ").getItem(0)
    return F.coalesce(
        F.to_date(raw, "yyyy-MM-dd"),
        F.to_date(raw, "MM/dd/yyyy"),
        F.to_date(raw, "dd/MM/yyyy"),
        F.to_date(raw, "yyyy/MM/dd"),
    )


def ensure_column(df, name: str, dtype: str):
    if name in df.columns:
        return df
    return df.withColumn(name, F.lit(None).cast(dtype))


def log_sivigila_quality(df, use_dane: bool) -> int:
    valid_year = F.col("epi_year").between(1900, 2100)
    valid_week = F.col("epi_week").between(1, 53)
    has_muni = (F.col("municipio_code").isNotNull()) & (
        F.length(F.col("municipio_code")) > 0
    )
    has_depto = (F.col("departamento_code").isNotNull()) & (
        F.length(F.col("departamento_code")) > 0
    )

    metrics = df.agg(
        F.count(F.lit(1)).alias("total_rows"),
        F.sum(F.when(~valid_year, 1).otherwise(0)).alias("invalid_year"),
        F.sum(F.when(~valid_week, 1).otherwise(0)).alias("invalid_week"),
        F.sum(F.when(~has_muni, 1).otherwise(0)).alias("missing_muni"),
        F.sum(F.when(~has_depto, 1).otherwise(0)).alias("missing_depto"),
        (
            F.sum(F.when(F.length(F.col("departamento_code")) != 2, 1).otherwise(0))
            if use_dane
            else F.lit(0)
        ).alias("invalid_depto_len"),
        (
            F.sum(F.when(F.length(F.col("municipio_code")) != 5, 1).otherwise(0))
            if use_dane
            else F.lit(0)
        ).alias("invalid_muni_len"),
    ).first()

    total = int(metrics["total_rows"] or 0)
    invalid_year = int(metrics["invalid_year"] or 0)
    invalid_week = int(metrics["invalid_week"] or 0)
    missing_muni = int(metrics["missing_muni"] or 0)
    missing_depto = int(metrics["missing_depto"] or 0)
    invalid_depto_len = int(metrics["invalid_depto_len"] or 0)
    invalid_muni_len = int(metrics["invalid_muni_len"] or 0)

    print(
        "[info] sivigila quality: "
        f"total={total} invalid_year={invalid_year} invalid_week={invalid_week} "
        f"missing_muni={missing_muni} missing_depto={missing_depto} "
        f"invalid_depto_len={invalid_depto_len} invalid_muni_len={invalid_muni_len}"
    )
    return total


def log_feature_coverage(df, columns: list[str]) -> None:
    if not columns:
        return

    total_rows = df.count()
    if total_rows == 0:
        print("[info] coverage: dataset empty")
        return

    metrics = df.agg(*[F.count(F.col(col)).alias(col) for col in columns]).first()
    for col in columns:
        non_null = int(metrics[col] or 0)
        pct = (non_null / total_rows) * 100
        print(f"[info] coverage {col}: {non_null}/{total_rows} ({pct:.1f}%)")


def maybe_dane(col, size: int, use_dane: bool):
    if use_dane:
        digits = F.regexp_replace(col, r"\D", "")
        padded = F.lpad(digits, size, "0")
        return F.when(
            F.length(digits) > 0,
            F.substring(padded, -size, size)
        ).otherwise(F.lit(None).cast("string"))
    return F.trim(col)


def normalize_muni_code(col):
    digits = F.regexp_replace(col, r"\D", "")
    return F.when(F.length(digits) > 0, F.substring(F.lpad(digits, 5, "0"), -5, 5))


def load_sivigila(spark: SparkSession, path: str, use_dane: bool):
    base = spark.read.option("header", True).option("inferSchema", False).csv(path)

    event_upper = F.upper(F.trim(F.col("Nombre_evento")))
    disease = (
        F.when(event_upper.contains("DENGUE"), F.lit("dengue"))
        .when(event_upper.contains("CHIKUNGUNYA"), F.lit("chikungunya"))
        .when(event_upper.contains("ZIKA"), F.lit("zika"))
        .when(event_upper.contains("MALARIA"), F.lit("malaria"))
    )

    base = (
        base.withColumn("epi_year", F.col("ANO").cast("int"))
        .withColumn("epi_week", F.col("SEMANA").cast("int"))
        .withColumn("cases", F.col("conteo").cast("int"))
        .withColumn("disease", disease)
        .filter(F.col("disease").isNotNull())
        .withColumn("departamento_code", maybe_dane(F.col("COD_DPTO_O"), 2, use_dane))
        .withColumn("departamento_name", F.trim(F.col("Departamento_ocurrencia")))
        .withColumn(
            "municipio_code",
            F.when(
                F.lit(use_dane),
                F.concat(
                    maybe_dane(F.col("COD_DPTO_O"), 2, True),
                    F.lpad(F.regexp_replace(F.col("COD_MUN_O"), r"\D", ""), 3, "0"),
                ),
            ).otherwise(F.trim(F.col("COD_MUN_O"))),
        )
        .withColumn("municipio_name", F.trim(F.col("Municipio_ocurrencia")))
    )

    total_rows = log_sivigila_quality(base, use_dane)

    base = base.filter(
        (F.col("epi_year").between(1900, 2100))
        & (F.col("epi_week").between(1, 53))
        & (F.col("municipio_code").isNotNull())
        & (F.length(F.col("municipio_code")) > 0)
    )

    if use_dane:
        base = base.filter(
            (F.col("departamento_code").isNotNull())
            & (F.length(F.col("departamento_code")) == 2)
            & (F.length(F.col("municipio_code")) == 5)
        )

    kept_rows = base.count()
    if total_rows:
        pct = (kept_rows / total_rows) * 100
        print(f"[info] sivigila kept: {kept_rows}/{total_rows} ({pct:.1f}%)")

    agg = (
        base.groupBy(
            "epi_year",
            "epi_week",
            "departamento_code",
            "departamento_name",
            "municipio_code",
            "municipio_name",
            "disease",
        )
        .agg(F.sum(F.coalesce(F.col("cases"), F.lit(0))).alias("cases_total"))
    )

    agg = (
        agg.withColumn("week_start_date", spark_iso_week_start("epi_year", "epi_week"))
        .withColumn("week_end_date", spark_iso_week_end("epi_year", "epi_week"))
        .withColumn("departamento_norm", spark_normalize_text(F.col("departamento_name")))
        .withColumn("municipio_norm", spark_normalize_text(F.col("municipio_name")))
        .withColumn("month_num", F.month(F.col("week_start_date")))
    )

    missing_week = agg.filter(F.col("week_start_date").isNull()).count()
    if missing_week:
        print(f"[info] sivigila missing week_start_date: {missing_week}")

    agg = agg.filter(F.col("week_start_date").isNotNull())

    return agg


def load_climate(spark: SparkSession, path: str, period: str):
    base = spark.read.option("header", True).option("inferSchema", False).csv(path)
    for col_name in base.columns:
        base = base.withColumnRenamed(col_name, normalize_column_name(col_name))

    base = (
        base.withColumn("periodo_norm", spark_normalize_text(F.col("periodo")))
        .withColumn("param_norm", spark_normalize_text(F.col("parametro")))
        .withColumn("departamento_norm", spark_normalize_text(F.col("departamento")))
        .withColumn("municipio_norm", spark_normalize_text(F.col("municipio")))
    )

    # Añadir región geográfica
    region_items = []
    for dept, region in REGION_MAP.items():
        region_items.extend([F.lit(dept), F.lit(region)])
    region_map_col = F.create_map(*region_items)
    base = base.withColumn("region_norm", region_map_col[F.col("departamento_norm")])

    # Filtrar por periodo exacto (evitando la normalización agresiva de spark_normalize_text que quita guiones)
    base = base.filter(F.trim(F.col("periodo")) == F.lit(period))

    param_items = []
    for key, value in PARAM_MAP.items():
        param_items.extend([F.lit(key), F.lit(value)])
    param_key = F.create_map(*param_items)

    base = base.withColumn("param_key", param_key[F.col("param_norm")])
    base = base.filter(F.col("param_key").isNotNull())

    stack_expr = "stack(12, " + ", ".join(
        [f"'{m}', {m}" for m, _ in MONTHS]
    ) + ") as (month_key, raw_value)"

    melted = base.select(
        "region_norm",
        "departamento_norm",
        "municipio_norm",
        "param_key",
        F.expr(stack_expr),
    )

    month_items = []
    for month_key, month_idx in MONTHS:
        month_items.extend([F.lit(month_key), F.lit(month_idx)])
    month_map = F.create_map(*month_items)

    melted = (
        melted.withColumn("month_num", month_map[F.col("month_key")])
        .withColumn("value", F.regexp_replace("raw_value", ",", ".").cast("double"))
        .filter(F.col("value").isNotNull())
    )

    avg_values = (
        melted.groupBy("region_norm", "departamento_norm", "municipio_norm", "month_num", "param_key")
        .agg(F.avg("value").alias("avg_value"))
    )

    climate_muni = (
        avg_values.groupBy("departamento_norm", "municipio_norm", "month_num")
        .pivot("param_key", list(PARAM_MAP.values()))
        .agg(F.first("avg_value"))
    )

    climate_dept = (
        avg_values.groupBy("departamento_norm", "month_num")
        .pivot("param_key", list(PARAM_MAP.values()))
        .agg(F.avg("avg_value"))
    )

    climate_region = (
        avg_values.groupBy("region_norm", "month_num")
        .pivot("param_key", list(PARAM_MAP.values()))
        .agg(F.avg("avg_value"))
    )

    return climate_muni, climate_dept, climate_region


def load_vaccination(spark: SparkSession, path: str, use_dane: bool):
    # Raw file from datos.gov.co comes in Latin-1
    base = read_csv_if_exists(spark, path, encoding="iso-8859-1")
    if base is None:
        return None

    for col_name in base.columns:
        base = base.withColumnRenamed(col_name, normalize_column_name(col_name))

    print(f"[debug] vacunacion normalized columns: {base.columns}")
    code_col = resolve_col(
        base.columns,
        ["coddepto", "cod_depto", "codigo_departamento", "cod_departamento"],
    )
    name_col = resolve_col(
        base.columns,
        ["departamento", "departamento_nombre", "nombre_departamento"],
    )
    year_col = resolve_col(base.columns, ["ano", "anio", "year", "aa_o"])
    coverage_col = resolve_col(
        base.columns,
        [
            "cobertura_de_vacunacion",
            "cobertura_vacunacion",
            "cobertura",
            "cobertura_porcentaje",
            "cobertura_de_vacunacia3n",
        ],
    )

    if not code_col or not year_col or not coverage_col:
        print("[skip] vacunacion: missing required columns")
        return None

    dept_code = maybe_dane(F.col(code_col), 2, use_dane)

    vacunacion = (
        base.withColumn("departamento_code", dept_code)
        .withColumn("epi_year", F.col(year_col).cast("int"))
        .withColumn(
            "vaccination_coverage_pct",
            F.regexp_replace(F.col(coverage_col), ",", ".").cast("double"),
        )
        .filter(F.col("departamento_code").isNotNull())
        .select(
            "departamento_code",
            "epi_year",
            "vaccination_coverage_pct",
        )
    )

    return (
        vacunacion.groupBy("departamento_code", "epi_year")
        .agg(F.avg("vaccination_coverage_pct").alias("vaccination_coverage_pct"))
        .filter(F.col("epi_year").isNotNull())
    )


def load_rips(spark: SparkSession, path: str):
    # Raw file from datos.gov.co comes in Latin-1
    base = read_csv_if_exists(spark, path, encoding="iso-8859-1")
    if base is None:
        return None

    for col_name in base.columns:
        base = base.withColumnRenamed(col_name, normalize_column_name(col_name))

    print(f"[debug] rips normalized columns: {base.columns}")
    dept_col = resolve_col(base.columns, ["departamento"])
    muni_col = resolve_col(base.columns, ["municipio"])
    year_col = resolve_col(base.columns, ["ano", "anio", "year", "aa_o"])
    diag_col = resolve_col(base.columns, ["diagnostico", "cie10", "dx"])
    count_col = resolve_col(
        base.columns,
        ["numeroatenciones", "numero_atenciones", "atenciones", "conteo"],
    )

    if not dept_col or not muni_col or not year_col or not diag_col or not count_col:
        print("[skip] rips: missing required columns")
        return None

    # RIPS raw format: "05541 - Peñol" — extract leading digits as DANE codes
    dane_from_label = lambda col_name, size: F.lpad(
        F.regexp_extract(F.col(col_name), r"^\s*(\d+)", 1), size, "0"
    )

    # CIE10 code is prefixed before " - " description
    diag_code = F.upper(F.regexp_extract(F.trim(F.col(diag_col)), r"^([A-Z]\d+)", 1))
    disease = (
        F.when(diag_code.startswith("A90"), F.lit("dengue"))
        .when(diag_code.startswith("A91"), F.lit("dengue"))
        .when(diag_code.startswith("A920"), F.lit("chikungunya"))
        .when(diag_code.startswith("A925"), F.lit("zika"))
        .when(diag_code.startswith("B50"), F.lit("malaria"))
        .when(diag_code.startswith("B51"), F.lit("malaria"))
        .when(diag_code.startswith("B52"), F.lit("malaria"))
        .when(diag_code.startswith("B53"), F.lit("malaria"))
        .when(diag_code.startswith("B54"), F.lit("malaria"))
    )

    rips = (
        base.withColumn("departamento_code", dane_from_label(dept_col, 2))
        .withColumn("municipio_code", dane_from_label(muni_col, 5))
        .withColumn("epi_year", F.col(year_col).cast("int"))
        .withColumn("visits", F.col(count_col).cast("int"))
        .withColumn("disease", disease)
        .filter(F.col("disease").isNotNull())
        .filter(
            F.col("departamento_code").isNotNull()
            & (F.length(F.col("departamento_code")) == 2)
        )
        .select("departamento_code", "municipio_code", "epi_year", "disease", "visits")
    )

    return (
        rips.groupBy("departamento_code", "municipio_code", "epi_year", "disease")
        .agg(F.sum(F.coalesce("visits", F.lit(0))).alias("rips_visits_total"))
        .filter(F.col("epi_year").isNotNull())
    )


def load_mobility(spark: SparkSession, path: str):
    base = read_csv_if_exists(spark, path)
    if base is None:
        return None

    for col_name in base.columns:
        base = base.withColumnRenamed(col_name, normalize_column_name(col_name))

    origin_col = resolve_col(
        base.columns,
        ["municipio_origen_ruta", "municipio_origen"],
    )
    dest_col = resolve_col(
        base.columns,
        ["municipio_destino_ruta", "municipio_destino"],
    )
    date_col = resolve_col(base.columns, ["fecha_despacho", "fecha"])
    passengers_col = resolve_col(base.columns, ["pasajeros"])
    dispatches_col = resolve_col(base.columns, ["despachos"])

    if not origin_col or not dest_col or not date_col:
        print("[skip] movilidad: missing required columns")
        return None

    print("[warn] movilidad uses calendar year for epi_year")

    base = base.withColumn("fecha", parse_date(date_col)).filter(
        F.col("fecha").isNotNull()
    )

    base = (
        base.withColumn("epi_year", F.date_format(F.col("fecha"), "yyyy").cast("int"))
        .withColumn("epi_week", F.weekofyear(F.col("fecha")))
        .withColumn("origin_code", normalize_muni_code(F.col(origin_col)))
        .withColumn("dest_code", normalize_muni_code(F.col(dest_col)))
        .withColumn(
            "passengers",
            F.col(passengers_col).cast("int") if passengers_col else F.lit(0),
        )
        .withColumn(
            "dispatches",
            F.col(dispatches_col).cast("int") if dispatches_col else F.lit(0),
        )
    )

    outgoing = (
        base.groupBy("epi_year", "epi_week", "origin_code")
        .agg(
            F.sum(F.coalesce("passengers", F.lit(0))).alias("passengers_out"),
            F.sum(F.coalesce("dispatches", F.lit(0))).alias("dispatches_out"),
        )
        .withColumnRenamed("origin_code", "municipio_code")
    )

    incoming = (
        base.groupBy("epi_year", "epi_week", "dest_code")
        .agg(
            F.sum(F.coalesce("passengers", F.lit(0))).alias("passengers_in"),
            F.sum(F.coalesce("dispatches", F.lit(0))).alias("dispatches_in"),
        )
        .withColumnRenamed("dest_code", "municipio_code")
    )

    mobility = outgoing.join(
        incoming, on=["epi_year", "epi_week", "municipio_code"], how="full"
    )

    return mobility.select(
        "epi_year",
        "epi_week",
        "municipio_code",
        (
            F.coalesce("passengers_in", F.lit(0))
            + F.coalesce("passengers_out", F.lit(0))
        ).alias("mobility_index"),
    )


def load_signals(spark: SparkSession, trends_path: str, rss_path: str):
    trends = read_csv_if_exists(spark, trends_path)
    rss = read_csv_if_exists(spark, rss_path)

    if trends is None and rss is None:
        return None

    # Normalización de Trends
    if trends is not None:
        trends = (
            trends.withColumn("week_start_date", parse_date("week_start_date"))
            .withColumn("trends_score", F.col("trends_score").cast("double"))
            .withColumn("epi_year", F.date_format(F.col("week_start_date"), "xxxx").cast("int"))
            .withColumn("epi_week", F.weekofyear(F.col("week_start_date")))
            .select("epi_year", "epi_week", "disease", "trends_score")
        )

    # Normalización de RSS
    if rss is not None:
        rss = (
            rss.withColumn("week_start_date", parse_date("week_start_date"))
            .withColumn("rss_mentions", F.col("rss_mentions").cast("int"))
            .withColumn("epi_year", F.date_format(F.col("week_start_date"), "xxxx").cast("int"))
            .withColumn("epi_week", F.weekofyear(F.col("week_start_date")))
            .select("epi_year", "epi_week", "disease", "rss_mentions")
        )

    if trends is not None and rss is not None:
        joined = trends.join(rss, on=["epi_year", "epi_week", "disease"], how="full")
    else:
        joined = trends if trends is not None else rss

    return (
        joined.groupBy("epi_year", "epi_week", "disease")
        .agg(
            F.avg("trends_score").alias("trends_score"),
            F.sum("rss_mentions").alias("rss_mentions"),
        )
    )


def enrich_and_write(
    sivigila,
    climate,
    vaccination,
    rips,
    mobility,
    signals,
    version: str,
    features: set[str],
    out_parquet: str,
    out_csv: str,
):
    climate_muni, climate_dept, climate_region = climate
    
    # Añadir región geográfica a sivigila para el fallback de nivel 3
    region_items = []
    for dept, region in REGION_MAP.items():
        region_items.extend([F.lit(dept), F.lit(region)])
    region_map_col = F.create_map(*region_items)
    sivigila = sivigila.withColumn("region_norm", region_map_col[F.col("departamento_norm")])
    # 1. Join por municipio (primera opción)
    joined = sivigila.join(
        climate_muni, 
        on=["departamento_norm", "municipio_norm", "month_num"], 
        how="left"
    )

    # 2. Fallback por departamento (donde municipio es null)
    climate_cols = list(PARAM_MAP.values())
    for col in climate_cols:
        climate_dept = climate_dept.withColumnRenamed(col, f"{col}_dept")
    
    joined = joined.join(
        climate_dept,
        on=["departamento_norm", "month_num"],
        how="left"
    )

    for col in climate_cols:
        joined = joined.withColumn(
            col,
            F.coalesce(F.col(col), F.col(f"{col}_dept"))
        ).drop(f"{col}_dept")

    # 3. Fallback por región geográfica (donde departamento sigue siendo null)
    for col in climate_cols:
        climate_region = climate_region.withColumnRenamed(col, f"{col}_reg")
    
    joined = joined.join(
        climate_region,
        on=["region_norm", "month_num"],
        how="left"
    )

    for col in climate_cols:
        joined = joined.withColumn(
            col,
            F.coalesce(F.col(col), F.col(f"{col}_reg"))
        ).drop(f"{col}_reg")

    if "mobility" in features and mobility is not None:
        joined = joined.join(
            mobility,
            on=["epi_year", "epi_week", "municipio_code"],
            how="left",
        )

    if "rips" in features and rips is not None:
        # RIPS uses DANE codes extracted from "05541 - Peñol" format
        joined = joined.join(
            rips,
            on=["departamento_code", "municipio_code", "epi_year", "disease"],
            how="left",
        )

    if "vaccination" in features and vaccination is not None:
        joined = joined.join(
            vaccination,
            on=["departamento_code", "epi_year"],
            how="left",
        )

    if signals is not None:
        joined = joined.join(
            signals,
            on=["epi_year", "epi_week", "disease"],
            how="left",
        )

    joined = joined.drop("departamento_norm", "municipio_norm", "month_num", "region_norm")

    joined = ensure_column(joined, "vaccination_coverage_pct", "double")
    joined = ensure_column(joined, "rips_visits_total", "bigint")
    joined = ensure_column(joined, "mobility_index", "double")
    joined = ensure_column(joined, "trends_score", "double")
    joined = ensure_column(joined, "rss_mentions", "int")

    if "mobility" in features and mobility is not None:
        hotspot_window = Window.partitionBy("epi_year", "epi_week", "disease").orderBy(F.col("mobility_index"))
        joined = joined.withColumn(
            "mobility_hotspot_score",
            F.round(F.percent_rank().over(hotspot_window) * F.lit(100.0), 2),
        )
    else:
        joined = joined.withColumn("mobility_hotspot_score", F.lit(None).cast("double"))

    joined = joined.withColumn(
        "posibles_casos_index",
        F.coalesce(F.col("cases_total"), F.lit(0))
        + (F.coalesce(F.col("trends_score"), F.lit(0.0)) * F.lit(0.1))
        + (F.coalesce(F.col("rss_mentions").cast("double"), F.lit(0.0)) * F.lit(0.5)),
    )

    coverage_cols = [
        "temp_avg_c",
        "temp_min_c",
        "temp_max_c",
        "humidity_avg_pct",
        "precipitation_mm",
    ]
    coverage_cols.extend(
        [
            "vaccination_coverage_pct",
            "rips_visits_total",
            "mobility_index",
            "mobility_hotspot_score",
            "trends_score",
            "rss_mentions",
            "posibles_casos_index",
        ]
    )

    log_feature_coverage(joined, coverage_cols)

    event_code = (
        F.when(F.col("disease") == "dengue", F.lit(CANONICAL_EVENT["dengue"][0]))
        .when(
            F.col("disease") == "chikungunya",
            F.lit(CANONICAL_EVENT["chikungunya"][0]),
        )
        .when(F.col("disease") == "zika", F.lit(CANONICAL_EVENT["zika"][0]))
        .when(F.col("disease") == "malaria", F.lit(CANONICAL_EVENT["malaria"][0]))
    )

    event_name = (
        F.when(F.col("disease") == "dengue", F.lit(CANONICAL_EVENT["dengue"][1]))
        .when(
            F.col("disease") == "chikungunya",
            F.lit(CANONICAL_EVENT["chikungunya"][1]),
        )
        .when(F.col("disease") == "zika", F.lit(CANONICAL_EVENT["zika"][1]))
        .when(F.col("disease") == "malaria", F.lit(CANONICAL_EVENT["malaria"][1]))
    )

    columns = [
        "epi_year",
        "epi_week",
        "week_start_date",
        "week_end_date",
        "departamento_code",
        "departamento_name",
        "municipio_code",
        "municipio_name",
        "event_code",
        "event_name",
        "disease",
        "cases_total",
        "temp_avg_c",
        "temp_min_c",
        "temp_max_c",
        "humidity_avg_pct",
        "precipitation_mm",
    ]

    columns.extend(
        [
            "vaccination_coverage_pct",
            "rips_visits_total",
            "mobility_index",
            "mobility_hotspot_score",
            "trends_score",
            "rss_mentions",
            "posibles_casos_index",
        ]
    )

    final_df = (
        joined.withColumn("event_code", event_code)
        .withColumn("event_name", event_name)
        .select(*columns)
    )

    final_df.write.mode("overwrite").parquet(out_parquet)
    final_df.coalesce(1).write.mode("overwrite").option("header", True).csv(out_csv)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build curated weekly dataset with PySpark"
    )
    parser.add_argument("--version", default=DEFAULT_VERSION, choices=["v0", "v1", "v2", "full"])
    parser.add_argument(
        "--features",
        default="",
        help="Comma-separated list: vaccination,rips,mobility | all | none",
    )
    parser.add_argument("--sivigila", default=str(DEFAULT_SIVIGILA))
    parser.add_argument("--climate", default=str(DEFAULT_CLIMATE))
    parser.add_argument("--vaccination", default=str(DEFAULT_VACCINATION))
    parser.add_argument("--rips", default=str(DEFAULT_RIPS))
    parser.add_argument("--mobility", default=str(DEFAULT_MOBILITY))
    parser.add_argument("--out-parquet")
    parser.add_argument("--out-csv")
    parser.add_argument("--period", default="1991-2020")
    args = parser.parse_args()

    version = args.version.lower()
    features = resolve_features(args.features)
    use_dane = version != "v0"

    out_parquet = args.out_parquet or default_output(version, "parquet")
    out_csv = args.out_csv or default_output(version, "csv")

    spark = build_spark(f"curated_weekly_{version}")

    sivigila = load_sivigila(spark, args.sivigila, use_dane)
    climate = load_climate(spark, args.climate, args.period)

    vaccination = None
    rips = None
    mobility = None
    if "vaccination" in features:
        vaccination = load_vaccination(spark, args.vaccination, use_dane)
        if vaccination is None:
            print("[warn] vaccination feature disabled (missing columns or file)")
    if "rips" in features:
        rips = load_rips(spark, args.rips)
        if rips is None:
            print("[warn] rips feature disabled (missing columns or file)")
    if "mobility" in features:
        mobility = load_mobility(spark, args.mobility)
        if mobility is None:
            print("[warn] mobility feature disabled (missing columns or file)")

    signals = None
    if "signals" in features:
        signals = load_signals(spark, "data/raw/signals_trends.csv", "data/raw/signals_rss.csv")

    enrich_and_write(
        sivigila,
        climate,
        vaccination,
        rips,
        mobility,
        signals,
        version,
        features,
        out_parquet,
        out_csv,
    )

    count = sivigila.count()
    print(f"[ok] curated dataset rows: {count}")

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
