#!/usr/bin/env python3

import argparse
from functools import reduce
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_TMPL = "data/processed/curated_weekly_parquet"

REQUIRED_COLUMNS = [
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
    "vaccination_coverage_pct",
    "rips_visits_total",
    "mobility_index",
    "mobility_hotspot_score",
    "trends_score",
    "rss_mentions",
    "posibles_casos_index",
]

KEY_COLUMNS = [
    "epi_year",
    "epi_week",
    "municipio_code",
    "disease",
]


def build_spark(app_name: str) -> SparkSession:
    return SparkSession.builder.appName(app_name).getOrCreate()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate curated weekly dataset")
    parser.add_argument("--version", default="full", choices=["v0", "v1", "v2", "full"])
    parser.add_argument("--input", default="")
    args = parser.parse_args()

    if args.input:
        input_path = args.input
    elif args.version == "full":
        input_path = str(REPO_ROOT / DEFAULT_INPUT_TMPL)
    else:
        input_path = str(REPO_ROOT / f"data/processed/curated_weekly_{args.version}_parquet")

    spark = build_spark(f"validate_curated_{args.version}")
    df = spark.read.parquet(input_path)

    expected_cols = REQUIRED_COLUMNS.copy()

    missing = [col for col in expected_cols if col not in df.columns]
    if missing:
        print(f"[error] missing columns: {missing}")
        spark.stop()
        return 1

    null_checks = [F.col(col).isNull() for col in KEY_COLUMNS]
    null_count = df.filter(reduce(lambda a, b: a | b, null_checks)).count()
    if null_count:
        print(f"[error] nulls in key columns: {null_count}")
        spark.stop()
        return 1

    negative_count = df.filter(F.col("cases_total") < 0).count()
    if negative_count:
        print(f"[error] negative cases_total: {negative_count}")
        spark.stop()
        return 1

    invalid_week = df.filter(~F.col("epi_week").between(1, 53)).count()
    if invalid_week:
        print(f"[error] invalid epi_week: {invalid_week}")
        spark.stop()
        return 1

    dup_count = (
        df.groupBy(KEY_COLUMNS)
        .count()
        .filter(F.col("count") > 1)
        .count()
    )
    if dup_count:
        print(f"[error] duplicated keys: {dup_count}")
        spark.stop()
        return 1

    print("[ok] validation passed")
    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
