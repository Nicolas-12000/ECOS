#!/usr/bin/env python3
"""
Limpieza y agregación de señales tempranas (Trends/RSS) con PySpark.
Genera la base external en formato Parquet a nivel de semana y enfermedad (Nacional).
"""

import argparse
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRENDS = REPO_ROOT / "data/raw/signals_trends.csv"
DEFAULT_RSS = REPO_ROOT / "data/raw/signals_rss.csv"
DEFAULT_OUT_PARQUET = REPO_ROOT / "data/external/signals_weekly_v2_parquet"


def build_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def read_csv_if_exists(spark: SparkSession, path: str):
    if not path or not Path(path).exists():
        print(f"[skip] missing file: {path}")
        return None
    return spark.read.option("header", True).option("inferSchema", True).csv(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Curate early signals data (Trends/RSS)")
    parser.add_argument("--trends", default=str(DEFAULT_TRENDS))
    parser.add_argument("--rss", default=str(DEFAULT_RSS))
    parser.add_argument("--out-parquet", default=str(DEFAULT_OUT_PARQUET))
    args = parser.parse_args()

    spark = build_spark("curate_signals_v2")

    print("[info] Cargando data cruda de señales...")
    trends = read_csv_if_exists(spark, args.trends)
    rss = read_csv_if_exists(spark, args.rss)

    if trends is None and rss is None:
        print("[error] No signals data found. Run fetch_signals.py first.")
        return 1

    # Preparar df_trends (SIN geolocalización aún - Google Trends nacional)
    if trends is not None:
        df_trends = (
            trends.withColumn("week_start_date", F.to_date("week_start_date"))
            .withColumn("trends_score", F.col("trends_score").cast("double"))
            .withColumn("departamento", F.coalesce(F.col("departamento"), F.lit("NACIONAL")))
            .select("week_start_date", "disease", "departamento", "trends_score")
        )
    else:
        print("[warn] Trends is missing, creating empty df.")
        schema = "week_start_date DATE, disease STRING, departamento STRING, trends_score DOUBLE"
        df_trends = spark.createDataFrame([], schema)

    # Preparar df_rss (CON geolocalización)
    if rss is not None:
        df_rss = (
            rss.withColumn("week_start_date", F.to_date("week_start_date"))
            .withColumn("rss_mentions", F.col("rss_mentions").cast("double"))
            .withColumn("departamento", F.col("departamento"))
            .select("week_start_date", "disease", "departamento", "rss_mentions")
        )
    else:
        print("[warn] RSS is missing, creating empty df.")
        schema = "week_start_date DATE, disease STRING, departamento STRING, rss_mentions DOUBLE"
        df_rss = spark.createDataFrame([], schema)

    # Join Full Outer por semana, enfermedad y departamento
    signals = df_trends.join(
        df_rss,
        on=["week_start_date", "disease", "departamento"],
        how="full"
    )

    # Computar ISO Year and Week desde week_start_date (Lunes)
    signals = (
        signals.filter(F.col("week_start_date").isNotNull())
        .withColumn(
            "epi_year", 
            F.date_format(F.col("week_start_date"), "xxxx").cast("int")
        )
        .withColumn("epi_week", F.weekofyear(F.col("week_start_date")))
        .withColumn("departamento", F.coalesce(F.col("departamento"), F.lit("NACIONAL")))
        .withColumn("trends_score", F.coalesce("trends_score", F.lit(0.0)))
        .withColumn("rss_mentions", F.coalesce("rss_mentions", F.lit(0.0)))
    )

    # Validación: datos temporales consistentes
    signals_validated = (
        signals
        .filter(F.col("epi_year").between(2013, 2024))
        .filter(F.col("epi_week").between(1, 53))
        .filter((F.col("trends_score") >= 0) & (F.col("trends_score") <= 100))
        .filter(F.col("rss_mentions") >= 0)
    )

    # Agrupar a una sola fila por semana/enfermedad/departamento en caso de duplicados
    agg = (
        signals_validated.groupBy("epi_year", "epi_week", "disease", "departamento")
        .agg(
            F.max("trends_score").alias("trends_score"),
            F.sum("rss_mentions").alias("rss_mentions_sum")
        )
    )

    out_path = Path(args.out_parquet)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Escribir a Parquet
    agg.write.mode("overwrite").parquet(str(out_path))

    count = agg.count()
    print(f"[ok] processed signals into {out_path} ({count} rows)")

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
