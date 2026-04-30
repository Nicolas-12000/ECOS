"""
Servicio de datos epidemiológicos.
Lee el dataset curado en Parquet (o CSV como fallback) y expone
helpers para filtrar por municipio, departamento, enfermedad y semana.
No tiene lógica de predicción aquí — eso lo hace el modelo joblib.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd
import psycopg
from psycopg.rows import dict_row

from app.core.db import get_db_connection

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
_PARQUET_MAIN = REPO_ROOT / "data/processed/curated_weekly_parquet"
_CSV_MAIN = REPO_ROOT / "data/processed/curated_weekly_csv"
_PARQUET_FRESH = REPO_ROOT / "data/processed/curated_weekly_fresh_parquet"
_CSV_FRESH = REPO_ROOT / "data/processed/curated_weekly_fresh_csv"
_PARQUET_LEGACY = REPO_ROOT / "data/processed/curated_weekly_v0_parquet"
_CSV_LEGACY = REPO_ROOT / "data/processed/curated_weekly_v0_csv"

VALID_DISEASES = {"dengue", "chikungunya", "zika", "malaria"}
OUTBREAK_THRESHOLD = 5.0


@lru_cache(maxsize=1)
def _load_df() -> pd.DataFrame:
    """Carga el dataset curado una vez y lo cachea en memoria."""
    for parquet, csv_dir in [
        (_PARQUET_FRESH, _CSV_FRESH),
        (_PARQUET_MAIN, _CSV_MAIN),
        (_PARQUET_LEGACY, _CSV_LEGACY),
    ]:
        if parquet.exists():
            logger.info("Loading curated dataset from %s", parquet)
            df = pd.read_parquet(parquet)
            df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
            df["cases_total"] = pd.to_numeric(df["cases_total"], errors="coerce").fillna(0).astype(int)
            return df
        if csv_dir.exists():
            csv_files = sorted(csv_dir.glob("*.csv"))
            if csv_files:
                logger.info("Loading curated dataset from CSV at %s", csv_dir)
                df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
                df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
                df["cases_total"] = pd.to_numeric(df["cases_total"], errors="coerce").fillna(0).astype(int)
                return df
    raise FileNotFoundError("Curated dataset not found. Run curate_weekly_spark.py first.")


def get_history(municipio_code: str, disease: str, limit: int = 104) -> pd.DataFrame:
    """Retorna las últimas `limit` semanas de historia para un municipio y enfermedad."""
    df = _load_df()
    mask = (df["municipio_code"] == municipio_code) & (df["disease"] == disease)
    result = df[mask].sort_values("week_start_date", ascending=False).head(limit)
    return result.reset_index(drop=True)


def get_signals(departamento_code: str, disease: str, limit: int = 52) -> pd.DataFrame:
    """
    Retorna señales tempranas (RIPS, movilidad, vacunación) a nivel departamental.
    El dataset curado agrega estas features por municipio; aquí agrupamos a depto.
    """
    df = _load_df()
    mask = (df["departamento_code"] == departamento_code) & (df["disease"] == disease)
    subset = df[mask].copy()

    signal_cols = {
        "vaccination_coverage_pct": "mean",
        "trends_score": "mean",
        "rss_mentions": "sum",
        "signals_score": "mean",
    }
    agg = {col: fn for col, fn in signal_cols.items() if col in df.columns}

    if not agg:
        return pd.DataFrame()

    grouped = (
        subset.groupby(["epi_year", "epi_week", "week_start_date", "departamento_code"])
        .agg(agg)
        .reset_index()
        .sort_values("week_start_date", ascending=False)
        .head(limit)
    )
    grouped["disease"] = disease
    return grouped.reset_index(drop=True)


def get_latest_global_summary() -> dict:
    """Retorna un resumen global de la última semana disponible en Supabase."""
    query = """
        SELECT 
            SUM(cases_total) as total_cases,
            AVG(NULLIF(temp_avg_c, 0)) as avg_temp,
            AVG(NULLIF(precipitation_mm, 0)) as avg_precip,
            epi_year, epi_week, week_start_date
        FROM public.fact_core_weekly
        GROUP BY epi_year, epi_week, week_start_date
        ORDER BY week_start_date DESC
        LIMIT 1
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(query)
                row = cur.fetchone()
                if not row:
                    return {}
                return row
    except Exception as e:
        logger.error("Error fetching global summary from DB: %s", e)
        return {}


def get_last_known_features(municipio_code: str, disease: str) -> pd.Series | Optional[pd.DataFrame]:
    """Retorna la fila más reciente del dataset para usar como input al modelo."""
    df = _load_df()
    mask = (df["municipio_code"] == municipio_code) & (df["disease"] == disease)
    subset = df[mask].sort_values("week_start_date", ascending=False)
    if subset.empty:
        return None
    return subset.iloc[0]
