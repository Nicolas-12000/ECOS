#!/usr/bin/env python3
"""Generate predictions using the trained model.

By default, runs on a limited sample. Use --all to score all municipio/disease pairs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(REPO_ROOT / ".env")
DEFAULT_DB_URL = os.getenv("SUPABASE_DB_URL")

from app.services.epidemiology import VALID_DISEASES, _load_df
from app.services.prediction import predict_cases

DEFAULT_OUTPUT = REPO_ROOT / "data/processed/predictions_demo.csv"


def resolve_targets(df: pd.DataFrame, municipio: str | None, disease: str | None, limit: int | None):
    if municipio and disease:
        return [(municipio, disease)]

    pairs = df[["municipio_code", "disease"]].drop_duplicates()
    if disease:
        pairs = pairs[pairs["disease"] == disease]
    if municipio:
        pairs = pairs[pairs["municipio_code"] == municipio]
    if limit:
        pairs = pairs.head(limit)
    return list(pairs.itertuples(index=False, name=None))


def save_predictions_to_supabase(rows, db_url):
    if not db_url:
        print("[warn] No SUPABASE_DB_URL provided, skipping Supabase save")
        return

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = 0")
                for row in rows:
                    # Get top 3 SHAP factors
                    shap_top = None
                    if row.get("shap_values"):
                        sorted_shap = sorted(row["shap_values"].items(), key=lambda x: abs(x[1]), reverse=True)[:3]
                        shap_top = {k: v for k, v in sorted_shap}

                    cur.execute(
                        """
                        INSERT INTO public.predictions (
                            departamento_code, municipio_code, disease,
                            epi_year, epi_week, week_start_date,
                            predicted_cases, outbreak_flag, outbreak_threshold,
                            endemic_risk, shap_top_factors
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            row.get("departamento_code"),
                            row.get("municipio_code"),
                            row.get("disease"),
                            row.get("epi_year"),
                            row.get("epi_week"),
                            row.get("week_start_date"),
                            row.get("predicted_cases"),
                            row.get("outbreak_flag"),
                            row.get("outbreak_threshold"),
                            row.get("endemic_risk"),
                            json.dumps(shap_top) if shap_top else None,
                        ),
                    )
            conn.commit()
        print("[ok] Predictions saved to Supabase")
    except Exception as e:
        print(f"[error] Failed to save predictions to Supabase: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ECOS predictions")
    parser.add_argument("--municipio", help="DANE municipio code")
    parser.add_argument("--disease", choices=sorted(VALID_DISEASES))
    parser.add_argument("--weeks-ahead", type=int, default=2)
    parser.add_argument("--all", action="store_true", help="Score all municipio/disease pairs")
    parser.add_argument("--limit", type=int, default=50, help="Limit number of targets when not using --all")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    parser.add_argument("--database-url", default=DEFAULT_DB_URL)
    parser.add_argument("--save-to-db", action="store_true", help="Save predictions to Supabase")
    args = parser.parse_args()

    df = _load_df()
    limit = None if args.all else args.limit
    targets = resolve_targets(df, args.municipio, args.disease, limit)

    if not targets:
        print("[warn] no targets to score")
        return 0

    rows = []
    for municipio_code, disease in targets:
        try:
            preds = predict_cases(municipio_code, disease, weeks_ahead=args.weeks_ahead)
        except Exception as exc:
            print(f"[warn] skip {municipio_code}/{disease}: {exc}")
            continue
        rows.extend(preds)

    if not rows:
        print("[warn] no predictions generated")
        return 0

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "json":
        output_path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    else:
        pd.DataFrame(rows).to_csv(output_path, index=False)

    print(f"[ok] predictions -> {output_path} ({len(rows)})")

    if args.save_to_db:
        save_predictions_to_supabase(rows, args.database_url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
