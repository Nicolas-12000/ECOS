#!/usr/bin/env python3

import argparse
import os
import re
import sys
import shutil
import subprocess
import unicodedata
import datetime as dt
from pathlib import Path

# Use the active interpreter inside the current environment.
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql import Window

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "full"
DEFAULT_SIVIGILA = REPO_ROOT / "data/raw/sivigila_4hyg-wa9d.csv"
DEFAULT_CLIMATE = REPO_ROOT / "data/raw/clima_normales_ideam_nsz2-kzcq.csv"
DEFAULT_VACCINATION = REPO_ROOT / "data/raw/vacunacion_6i25-2hdt.csv"
DEFAULT_FRESH_PARQUET = REPO_ROOT / "data/processed/curated_weekly_fresh_parquet"
DEFAULT_FRESH_CSV = REPO_ROOT / "data/processed/curated_weekly_fresh_csv"

FEATURES_ALL = {"vaccination"}

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

LAT_LON_MAP = {
    "05": (6.2518, -75.5636),   # Antioquia
    "08": (10.9685, -74.7813),  # Atlantico
    "11": (4.6097, -74.0817),   # Bogota
    "13": (10.3997, -75.4762),  # Bolivar
    "15": (5.5353, -73.3678),   # Boyaca
    "17": (5.0689, -75.5174),   # Caldas
    "18": (1.6144, -75.6062),   # Caqueta
    "19": (2.4454, -76.6132),   # Cauca
    "20": (10.4631, -73.2532),  # Cesar
    "23": (8.7480, -75.8814),   # Cordoba
    "25": (4.5981, -74.0758),   # Cundinamarca
    "27": (5.6947, -76.6611),   # Choco
    "41": (2.9273, -75.2819),   # Huila
    "44": (11.5440, -72.9069),  # La Guajira
    "47": (11.2408, -74.1990),  # Magdalena
    "50": (4.1420, -73.6266),   # Meta
    "52": (1.2136, -77.2811),   # Nariño
    "54": (7.8939, -72.5078),   # Norte de Santander
    "63": (4.5339, -75.6811),   # Quindio
    "66": (4.8133, -75.6961),   # Risaralda
    "68": (7.1193, -73.1227),   # Santander
    "70": (9.3047, -75.3978),   # Sucre
    "73": (4.4389, -75.2322),   # Tolima
    "76": (3.4516, -76.5320),   # Valle del Cauca
    "81": (7.0847, -70.7591),   # Arauca
    "85": (5.3378, -72.3959),   # Casanare
    "86": (1.1478, -76.6478),   # Putumayo
    "88": (12.5847, -81.7006),  # San Andres
    "91": (-4.2153, -69.9406),  # Amazonas
    "94": (3.8653, -67.9239),   # Guainia
    "95": (2.5729, -72.6459),   # Guaviare
    "97": (1.2503, -70.2339),   # Vaupes
    "99": (6.1822, -67.4815),   # Vichada
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


def clear_output_path(path_str: str) -> None:
    path = Path(path_str)
    if path.exists():
        shutil.rmtree(path)
    if path.exists():
        subprocess.run(["rm", "-rf", str(path)], check=True)


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
    period_filtered = base.filter(F.trim(F.col("periodo")) == F.lit(period))
    # Si no hay datos para el periodo pedido, usar todos los periodos disponibles (fallback)
    if period_filtered.count() > 0:
        base = period_filtered
    else:
        print(f"[warn] climate: period {period} not found; using all available periods")

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
            "raw_val",
            F.regexp_replace(F.col(coverage_col), ",", ".").cast("double"),
        )
        .withColumn(
            "norm_val",
            F.when(F.col("raw_val") <= 1.05, F.col("raw_val") * 100.0)
            .otherwise(F.col("raw_val"))
        )
        .withColumn(
            "vaccination_coverage_pct",
            F.when(F.col("norm_val") > 100.0, F.lit(100.0))
            .when(F.col("norm_val") < 0.0, F.lit(0.0))
            .otherwise(F.col("norm_val"))
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





def enrich_and_write(
    sivigila,
    climate,
    vaccination,
    version: str,
    features: set[str],
    out_parquet: str,
    out_csv_prefix: str,
):
    climate_muni, climate_dept, climate_region = climate
    
    # Cachear sivigila ya que se usa como base
    sivigila = sivigila.cache()
    
    # --- 1. DIMENSIONES (Star Schema) ---
    print("[info] Generando Dimensiones (Departamentos y Municipios)...")
    
    # Añadir región geográfica a sivigila
    region_items = []
    for dept, region in REGION_MAP.items():
        region_items.extend([F.lit(dept), F.lit(region)])
    region_map_col = F.create_map(*region_items)
    sivigila = sivigila.withColumn("region_norm", region_map_col[F.col("departamento_norm")])
    
    dim_departamentos = sivigila.select(
        "departamento_code", "departamento_name", "region_norm"
    ).distinct().filter(F.col("departamento_code").isNotNull())
    
    # Inyectar Latitud y Longitud de forma nativa para evitar fallos de memoria
    lat_map_items = []
    lon_map_items = []
    for code, (lat, lon) in LAT_LON_MAP.items():
        lat_map_items.extend([F.lit(code), F.lit(lat)])
        lon_map_items.extend([F.lit(code), F.lit(lon)])
    
    lat_map_col = F.create_map(*lat_map_items)
    lon_map_col = F.create_map(*lon_map_items)
    
    dim_departamentos = dim_departamentos.withColumn("latitude", lat_map_col[F.col("departamento_code")])
    dim_departamentos = dim_departamentos.withColumn("longitude", lon_map_col[F.col("departamento_code")])
    
    dim_municipios = sivigila.select(
        "municipio_code", "municipio_name", "departamento_code"
    ).distinct().filter(F.col("municipio_code").isNotNull())


    # --- 2. FACT: CORE WEEKLY (SIVIGILA + Vaccination + Climate) ---
    print("[info] Generando Fact Table: Core Weekly...")
    core_df = sivigila

    # --- Join climate by municipio/departamento + month if available (avoid missing climate values later) ---
    try:
        if climate_muni is not None:
            core_df = core_df.join(
                climate_muni,
                on=["departamento_norm", "municipio_norm", "month_num"],
                how="left",
            )
    except Exception:
        # defensive: keep core_df as-is if climate_muni is not joinable
        print("[warn] climate: could not join climate_muni to core_df")

    # Join vaccination by departamento + year
    if vaccination is not None:
        core_df = core_df.join(
            vaccination,
            on=["departamento_code", "epi_year"],
            how="left"
        )



    # Limpieza de columnas para la tabla de hechos (eliminar nombres, dejar solo códigos foráneos)
    core_df = core_df.drop("departamento_name", "municipio_name", "departamento_norm", "municipio_norm", "region_norm")

    for climate_col in ["precipitation_mm", "temp_avg_c", "temp_min_c", "temp_max_c"]:
        core_df = ensure_column(core_df, climate_col, "double")
    core_df = ensure_column(core_df, "vaccination_coverage_pct", "double")

    # Evitar valores nulos en columnas exógenas: aplicar coalesce con defaults razonables


    # Coalesce climate columns (si fueron añadidas por el join). Usar 0.0 como fallback.
    climate_cols = ["precipitation_mm", "temp_avg_c", "temp_min_c", "temp_max_c"]
    for c in climate_cols:
        core_df = core_df.withColumn(c, F.coalesce(F.col(c), F.lit(0.0)).cast("double"))

    # Coalesce vaccination coverage if present
    core_df = core_df.withColumn("vaccination_coverage_pct", F.coalesce(F.col("vaccination_coverage_pct"), F.lit(0.0)).cast("double"))



    event_code = (
        F.when(F.col("disease") == "dengue", F.lit(CANONICAL_EVENT["dengue"][0]))
        .when(F.col("disease") == "chikungunya", F.lit(CANONICAL_EVENT["chikungunya"][0]))
        .when(F.col("disease") == "zika", F.lit(CANONICAL_EVENT["zika"][0]))
        .when(F.col("disease") == "malaria", F.lit(CANONICAL_EVENT["malaria"][0]))
    )

    fact_core_weekly = (
        core_df.withColumn("event_code", event_code)
        .select(
            "epi_year",
            "epi_week",
            "week_start_date",
            "week_end_date",
            "month_num",
            "departamento_code",
            "municipio_code",
            "event_code",
            "disease",
            "cases_total",
            "temp_avg_c",
            "temp_min_c",
            "temp_max_c",
            "precipitation_mm",
            "vaccination_coverage_pct",
        )
    )

    # Deduplicate: group by key columns and aggregate with sensible defaults to ensure unique primary keys
    dedup_keys = ["epi_year", "epi_week", "month_num", "departamento_code", "municipio_code", "event_code", "disease"]
    fact_core_weekly = (
        fact_core_weekly.groupBy(*dedup_keys)
        .agg(
            F.first("week_start_date").alias("week_start_date"),
            F.first("week_end_date").alias("week_end_date"),
            F.sum("cases_total").alias("cases_total"),
            F.avg("temp_avg_c").alias("temp_avg_c"),
            F.avg("temp_min_c").alias("temp_min_c"),
            F.avg("temp_max_c").alias("temp_max_c"),
            F.avg("precipitation_mm").alias("precipitation_mm"),
            F.avg("vaccination_coverage_pct").alias("vaccination_coverage_pct"),
        )
        .select(
            "epi_year",
            "epi_week",
            "week_start_date",
            "week_end_date",
            "month_num",
            "departamento_code",
            "municipio_code",
            "event_code",
            "disease",
            "cases_total",
            "temp_avg_c",
            "temp_min_c",
            "temp_max_c",
            "precipitation_mm",
            "vaccination_coverage_pct",
        )
    )

    # --- 3. FACT: AVG CASES (Annual by Dept) ---
    print("[info] Generando Fact Table: Promedios Anuales...")
    fact_avg_cases = (
        sivigila.groupBy("departamento_code", "epi_year", "disease")
        .agg(F.avg("cases_total").alias("avg_weekly_cases"))
        .filter(F.col("departamento_code").isNotNull())
    )

    # --- 4. FACT: CLIMATE (Monthly by Dept) ---
    print("[info] Generando Fact Table: Clima Mensual...")
    dept_map = sivigila.select("departamento_norm", "departamento_code").distinct()
    fact_climate = (
        climate_dept.join(dept_map, on="departamento_norm", how="left")
        .filter(F.col("departamento_code").isNotNull())
        .drop("departamento_norm")
    )

    # --- 5. FACT: VACCINATION (Annual by Dept) ---
    fact_vaccination = None
    if vaccination is not None:
        print("[info] Generando Fact Table: Vacunación Anual...")
        fact_vaccination = vaccination.filter(F.col("departamento_code").isNotNull())

    # --- 6. EXPORTAR TODO EN FORMATO STAR SCHEMA ---
    print(f"[info] Exportando Modelo de Estrella a {out_csv_prefix}_* ...")

    clear_output_path(out_parquet)
    clear_output_path(f"{out_csv_prefix}_dim_departamentos")
    clear_output_path(f"{out_csv_prefix}_dim_municipios")
    clear_output_path(f"{out_csv_prefix}_fact_core_weekly")
    clear_output_path(f"{out_csv_prefix}_fact_climate_monthly")
    clear_output_path(f"{out_csv_prefix}_fact_avg_cases_annual")
    clear_output_path(f"{out_csv_prefix}_fact_vaccination_annual")
    
    fact_core_weekly.write.mode("overwrite").parquet(out_parquet)
    
    dim_departamentos.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{out_csv_prefix}_dim_departamentos")
    dim_municipios.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{out_csv_prefix}_dim_municipios")
    fact_core_weekly.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{out_csv_prefix}_fact_core_weekly")
    fact_climate.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{out_csv_prefix}_fact_climate_monthly")
    fact_avg_cases.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{out_csv_prefix}_fact_avg_cases_annual")

    if fact_vaccination is not None:
        fact_vaccination.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{out_csv_prefix}_fact_vaccination_annual")

    sivigila.unpersist()






def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build curated weekly dataset with PySpark"
    )
    parser.add_argument("--version", default=DEFAULT_VERSION, choices=["v0", "v1", "v2", "full"])
    parser.add_argument(
        "--features",
        default="",
        help="Comma-separated list: vaccination | all | none",
    )
    parser.add_argument("--sivigila", default=str(DEFAULT_SIVIGILA))
    parser.add_argument("--climate", default=str(DEFAULT_CLIMATE))
    parser.add_argument("--vaccination", default=str(DEFAULT_VACCINATION))
    parser.add_argument("--out-parquet")
    parser.add_argument("--out-csv")
    parser.add_argument("--period", default="1991-2020")
    args = parser.parse_args()

    version = args.version.lower()
    features = resolve_features(args.features)
    use_dane = version != "v0"

    out_parquet = args.out_parquet or str(DEFAULT_FRESH_PARQUET)
    out_csv = args.out_csv or str(DEFAULT_FRESH_CSV)

    spark = build_spark(f"curated_weekly_{version}")

    sivigila = load_sivigila(spark, args.sivigila, use_dane)
    climate = load_climate(spark, args.climate, args.period)

    if "vaccination" in features:
        vaccination = load_vaccination(spark, args.vaccination, use_dane)
        if vaccination is None:
            print("[warn] vaccination feature disabled (missing columns or file)")

    enrich_and_write(
        sivigila,
        climate,
        vaccination,
        version,
        features,
        out_parquet,
        out_csv.replace(".csv", ""), # Usar como prefijo
    )

    count = sivigila.count()
    print(f"[ok] curated dataset rows: {count}")

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
