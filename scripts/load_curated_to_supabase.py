#!/usr/bin/env python3
"""Load curated_weekly CSV into Supabase/Postgres.

Usage:
  SUPABASE_DB_URL='postgresql://...'
  .venv/bin/python scripts/load_curated_to_supabase.py --truncate
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_DIR = REPO_ROOT / "data/processed/curated_weekly_csv"

COLUMNS = [
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
]


def resolve_csv_file(csv_arg: str | None) -> Path:
    if csv_arg:
        candidate = Path(csv_arg)
        if candidate.is_file():
            return candidate
        if candidate.is_dir():
            files = sorted(candidate.glob("part-*.csv"))
            if files:
                return files[0]
        raise FileNotFoundError(f"CSV path not found: {csv_arg}")

    files = sorted(DEFAULT_CSV_DIR.glob("part-*.csv"))
    if not files:
        raise FileNotFoundError(f"No part-*.csv found in {DEFAULT_CSV_DIR}")
    return files[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Load curated_weekly into Supabase")
    parser.add_argument("--database-url", default=os.getenv("SUPABASE_DB_URL", ""))
    parser.add_argument("--csv", default="", help="CSV file path or directory containing part-*.csv")
    parser.add_argument("--truncate", action="store_true", help="Truncate destination table before loading")
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("Missing database URL. Set --database-url or SUPABASE_DB_URL.")

    csv_file = resolve_csv_file(args.csv or None)
    print(f"[info] using CSV: {csv_file}")

    copy_sql = (
        "COPY public.curated_weekly ("
        + ", ".join(COLUMNS)
        + ") FROM STDIN WITH (FORMAT csv, HEADER true)"
    )

    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            if args.truncate:
                print("[info] truncating public.curated_weekly")
                cur.execute("TRUNCATE TABLE public.curated_weekly")

            with csv_file.open("r", encoding="utf-8") as f:
                with cur.copy(copy_sql) as copy:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        copy.write(chunk)

        conn.commit()

    print("[ok] load completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
