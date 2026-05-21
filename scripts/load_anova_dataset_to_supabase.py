#!/usr/bin/env python3
"""Load ANOVA dataset CSV into Supabase/Postgres.

Usage:
  SUPABASE_DB_URL='postgresql://...'
  .venv/bin/python scripts/load_anova_dataset_to_supabase.py --truncate
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env", override=True)

DEFAULT_CSV = REPO_ROOT / "data/processed/ANOVA_test/dataset_maestro_epidemiologico.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description="Load ANOVA dataset into Supabase")
    parser.add_argument("--database-url", default=os.getenv("SUPABASE_DB_URL", ""))
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to dataset CSV")
    parser.add_argument("--schema", default="analytics")
    parser.add_argument("--table", default="anova_dataset")
    parser.add_argument("--truncate", action="store_true", help="Truncate table before loading")
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("Missing database URL. Set --database-url or SUPABASE_DB_URL.")

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    table_ref = f"{args.schema}.{args.table}"

    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            with csv_path.open("r", encoding="utf-8") as f:
                header_line = f.readline().strip()
                # Handle UTF-8 BOM that can prefix the first column name
                header_line = header_line.lstrip("\ufeff")
                columns = [c.strip() for c in header_line.split(",") if c.strip()]
                f.seek(0)

                cur.execute(
                    """
                    select column_name
                    from information_schema.columns
                    where table_schema = %s and table_name = %s
                    order by ordinal_position;
                    """,
                    (args.schema, args.table),
                )
                table_columns = [row[0] for row in cur.fetchall()]
                missing = [col for col in columns if col not in table_columns]
                if missing:
                    raise SystemExit(
                        "Table schema mismatch for "
                        f"{table_ref}. Missing columns: {missing}. "
                        f"Table columns: {table_columns}"
                    )

                if args.truncate:
                    cur.execute(f"TRUNCATE TABLE {table_ref}")

                copy_sql = (
                    f"COPY {table_ref} ({', '.join(columns)}) "
                    "FROM STDIN WITH (FORMAT csv, HEADER true)"
                )

                with cur.copy(copy_sql) as copy:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        copy.write(chunk)

        conn.commit()

    print(f"[ok] loaded {csv_path.name} into {table_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
