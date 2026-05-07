#!/usr/bin/env python3
"""Load curated datasets (Star Schema) into Supabase/Postgres.

Usage:
  SUPABASE_DB_URL='postgresql://...'
  .venv/bin/python scripts/load_curated_to_supabase.py --truncate
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from dotenv import load_dotenv

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")
PROCESSED_DIR = REPO_ROOT / "data/processed"

# Define tables in dependency order for safe loading (Dimensions first, then Facts)
TABLES = [
    ("dim_departamentos", PROCESSED_DIR / "curated_weekly_csv_dim_departamentos"),
    ("dim_municipios", PROCESSED_DIR / "curated_weekly_csv_dim_municipios"),
    ("fact_avg_cases_annual", PROCESSED_DIR / "curated_weekly_csv_fact_avg_cases_annual"),
    ("fact_climate_monthly", PROCESSED_DIR / "curated_weekly_csv_fact_climate_monthly"),
    ("fact_vaccination_annual", PROCESSED_DIR / "curated_weekly_csv_fact_vaccination_annual"),
    ("fact_core_weekly", PROCESSED_DIR / "curated_weekly_csv_fact_core_weekly"),
    ("raw_signals_trends", PROCESSED_DIR / "signals_trends.csv"),
    ("raw_signals_rss", PROCESSED_DIR / "signals_rss.csv"),
    ("raw_open_meteo_weekly", PROCESSED_DIR / "open_meteo_weekly.csv"),
    ("raw_rss_articles", PROCESSED_DIR / "signals_rss_articles.csv"),
]

def resolve_csv_file(path_or_dir: Path) -> Path:
    if path_or_dir.is_file():
        return path_or_dir
    files = sorted(path_or_dir.glob("part-*.csv"))
    if not files:
        raise FileNotFoundError(f"No part-*.csv found in {path_or_dir}")
    return files[0]

def main() -> int:
    parser = argparse.ArgumentParser(description="Load Star Schema into Supabase")
    parser.add_argument("--database-url", default=os.getenv("SUPABASE_DB_URL", ""))
    parser.add_argument("--truncate", action="store_true", help="Truncate destination tables before loading")
    parser.add_argument("--scraped-only", action="store_true", help="Load only scraped tables (raw_*)")
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("Missing database URL. Set --database-url or SUPABASE_DB_URL.")

    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            tables_to_load = TABLES
            if args.scraped_only:
                tables_to_load = [t for t in TABLES if t[0].startswith("raw_")]

            if args.truncate:
                print("[info] truncating tables...")
                # Truncate all tables in one go with CASCADE to handle foreign keys
                tables_str = ", ".join([f"public.{t}" for t, _ in tables_to_load])
                cur.execute(f"TRUNCATE TABLE {tables_str} CASCADE")
                print(f"[ok] truncated: {tables_str}")

            for table_name, path_or_dir in tables_to_load:
                if not path_or_dir.exists():
                    print(f"[warn] skipping {table_name}: path not found {path_or_dir}")
                    continue
                
                try:
                    csv_file = resolve_csv_file(path_or_dir)
                except FileNotFoundError as e:
                    print(f"[warn] skipping {table_name}: {e}")
                    continue

                print(f"[info] loading {table_name} from {csv_file.name}...")
                
                with csv_file.open("r", encoding="utf-8") as f:
                    header_line = f.readline().strip()
                    columns = header_line.split(",")
                    f.seek(0)
                    
                    copy_sql = f"COPY public.{table_name} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv, HEADER true)"
                    
                    with cur.copy(copy_sql) as copy:
                        while True:
                            chunk = f.read(1024 * 1024)
                            if not chunk:
                                break
                            copy.write(chunk)
                print(f"[ok] {table_name} loaded.")

        conn.commit()

    print("\n[ok] all datasets loaded successfully")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
