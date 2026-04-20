#!/usr/bin/env python3

import argparse
import datetime as dt
import unicodedata
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIVIGILA = REPO_ROOT / "data/raw/sivigila_4hyg-wa9d.csv"
DEFAULT_CLIMA = REPO_ROOT / "data/raw/clima_normales_ideam_nsz2-kzcq.csv"
DEFAULT_OUT_PARQUET = REPO_ROOT / "data/processed/curated_weekly_v0_parquet"
DEFAULT_OUT_CSV = REPO_ROOT / "data/processed/curated_weekly_v0_csv"

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


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace(".", " ")
    value = " ".join(value.upper().split())
    return value


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


@F.udf(T.StringType())
def normalize_udf(value: str | None) -> str:
    return normalize_text(value)


@F.udf(T.DateType())
def iso_week_start(year: int | None, week: int | None):
    if year is None or week is None:
        return None
    try:
        return dt.date.fromisocalendar(int(year), int(week), 1)
    except ValueError:
        return None


@F.udf(T.DateType())
def iso_week_end(year: int | None, week: int | None):
    if year is None or week is None:
        return None
    try:
        return dt.date.fromisocalendar(int(year), int(week), 7)
    except ValueError:
        return None


def build_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def load_sivigila(spark: SparkSession, path: str):
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
        .withColumn("departamento_code", F.trim(F.col("COD_DPTO_O")))
        .withColumn("departamento_name", F.trim(F.col("Departamento_ocurrencia")))
        .withColumn("municipio_code", F.trim(F.col("COD_MUN_O")))
        .withColumn("municipio_name", F.trim(F.col("Municipio_ocurrencia")))
    )

    base = base.filter(
        (F.col("epi_year").between(1900, 2100))
        & (F.col("epi_week").between(1, 53))
        & (F.col("municipio_code").isNotNull())
        & (F.length(F.col("municipio_code")) > 0)
    )

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
        agg.withColumn("week_start_date", iso_week_start("epi_year", "epi_week"))
        .withColumn("week_end_date", iso_week_end("epi_year", "epi_week"))
        .withColumn("departamento_norm", normalize_udf("departamento_name"))
        .withColumn("municipio_norm", normalize_udf("municipio_name"))
        .withColumn("month_num", F.month(F.col("week_start_date")))
        .filter(F.col("week_start_date").isNotNull())
    )

    return agg


def load_clima(spark: SparkSession, path: str, periodo: str):
    base = spark.read.option("header", True).option("inferSchema", False).csv(path)
    for col_name in base.columns:
        base = base.withColumnRenamed(col_name, normalize_column_name(col_name))

    base = (
        base.withColumn("periodo_norm", normalize_udf("periodo"))
        .withColumn("param_norm", normalize_udf("parametro"))
        .withColumn("departamento_norm", normalize_udf("departamento"))
        .withColumn("municipio_norm", normalize_udf("municipio"))
    )

    periodo_norm = normalize_text(periodo)
    base = base.filter(F.col("periodo_norm") == F.lit(periodo_norm))

    param_items = []
    for key, value in PARAM_MAP.items():
        param_items.extend([F.lit(key), F.lit(value)])
    param_key = F.create_map(*param_items)

    base = base.withColumn("param_key", param_key.getItem(F.col("param_norm")))
    base = base.filter(F.col("param_key").isNotNull())

    stack_expr = "stack(12, " + ", ".join(
        [f"'{m}', {m}" for m, _ in MONTHS]
    ) + ") as (month_key, raw_value)"

    melted = base.select(
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
        melted.withColumn("month_num", month_map.getItem("month_key"))
        .withColumn("value", F.regexp_replace("raw_value", ",", ".").cast("double"))
        .filter(F.col("value").isNotNull())
    )

    avg_values = (
        melted.groupBy("departamento_norm", "municipio_norm", "month_num", "param_key")
        .agg(F.avg("value").alias("avg_value"))
    )

    climate = (
        avg_values.groupBy("departamento_norm", "municipio_norm", "month_num")
        .pivot("param_key", list(PARAM_MAP.values()))
        .agg(F.first("avg_value"))
    )

    return climate


def enrich_and_write(
    sivigila,
    clima,
    out_parquet: str,
    out_csv: str,
):
    joined = (
        sivigila.join(
            clima,
            on=["departamento_norm", "municipio_norm", "month_num"],
            how="left",
        )
        .drop("departamento_norm", "municipio_norm", "month_num")
    )

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

    final_df = (
        joined.withColumn("event_code", event_code)
        .withColumn("event_name", event_name)
        .select(
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
        )
    )

    final_df.write.mode("overwrite").parquet(out_parquet)
    final_df.coalesce(1).write.mode("overwrite").option("header", True).csv(out_csv)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build curated weekly dataset v0 with PySpark"
    )
    parser.add_argument("--sivigila", default=str(DEFAULT_SIVIGILA))
    parser.add_argument("--clima", default=str(DEFAULT_CLIMA))
    parser.add_argument("--out-parquet", default=str(DEFAULT_OUT_PARQUET))
    parser.add_argument("--out-csv", default=str(DEFAULT_OUT_CSV))
    parser.add_argument("--periodo", default="1991-2020")
    args = parser.parse_args()

    spark = build_spark("curated_weekly_v0")

    sivigila = load_sivigila(spark, args.sivigila)
    clima = load_clima(spark, args.clima, args.periodo)

    enrich_and_write(sivigila, clima, args.out_parquet, args.out_csv)

    count = sivigila.count()
    print(f"[ok] curated dataset rows: {count}")

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
