"""
Servicio de datos epidemiológicos.
Lee el dataset curado desde Supabase (si está configurado) o desde
Parquet/CSV local como fallback.
No tiene lógica de predicción aquí — eso lo hace el modelo joblib.
"""

import logging
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.core.config import settings

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


def _try_load_from_supabase() -> pd.DataFrame | None:
    """Try loading the fact_core_weekly table from Supabase/Postgres.

    Returns a DataFrame if successful, None if Supabase is not configured
    or if the connection/query fails.
    """
    db_url = settings.resolved_database_url()
    if not db_url:
        return None

    try:
        import psycopg

        with psycopg.connect(db_url, connect_timeout=5) as conn:
            # Check if the table exists
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS ("
                    "  SELECT 1 FROM information_schema.tables "
                    "  WHERE table_schema = 'public' AND table_name = 'fact_core_weekly'"
                    ")"
                )
                exists = cur.fetchone()[0]
                if not exists:
                    logger.info("Supabase: fact_core_weekly table does not exist")
                    return None

            # Load the data
            query = """
                SELECT
                    epi_year, epi_week, week_start_date, week_end_date,
                    month_num, departamento_code, municipio_code,
                    event_code, disease, cases_total,
                    temp_avg_c, temp_min_c, temp_max_c,
                    humidity_avg_pct, precipitation_mm,
                    vaccination_coverage_pct, rips_visits_total,
                    mobility_index, trends_score, rss_mentions, signals_score
                FROM public.fact_core_weekly
                ORDER BY week_start_date DESC
            """
            df = pd.read_sql_query(query, conn)

            if df.empty:
                logger.info("Supabase: fact_core_weekly is empty")
                return None

            df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
            df["cases_total"] = pd.to_numeric(df["cases_total"], errors="coerce").fillna(0).astype(int)
            logger.info("Loaded %d rows from Supabase fact_core_weekly", len(df))
            return df

    except ImportError:
        logger.warning("psycopg not installed — cannot connect to Supabase")
        return None
    except Exception as exc:
        logger.warning("Supabase connection failed: %s", exc)
        return None


def _load_from_local() -> pd.DataFrame:
    """Load from local Parquet or CSV files."""
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
    raise FileNotFoundError("Curated dataset not found. Run curate_weekly_spark.py or generate_demo_data.py first.")


@lru_cache(maxsize=1)
def _load_df() -> pd.DataFrame:
    """Carga el dataset curado una vez y lo cachea en memoria.

    Intenta Supabase primero, luego archivos locales como fallback.
    """
    # 1. Try Supabase
    df = _try_load_from_supabase()
    if df is not None and not df.empty:
        return df

    # 2. Fall back to local files
    return _load_from_local()


def get_data_source() -> str:
    """Returns which data source is active ('supabase' or 'local')."""
    db_url = settings.resolved_database_url()
    if db_url:
        try:
            import psycopg
            with psycopg.connect(db_url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT count(*) FROM public.fact_core_weekly LIMIT 1"
                    )
                    count = cur.fetchone()[0]
                    if count > 0:
                        return "supabase"
        except Exception:
            pass
    return "local"


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


def get_last_known_features(municipio_code: str, disease: str) -> pd.Series | None:
    """Retorna la fila más reciente del dataset para usar como input al modelo."""
    df = _load_df()
    mask = (df["municipio_code"] == municipio_code) & (df["disease"] == disease)
    subset = df[mask].sort_values("week_start_date", ascending=False)
    if subset.empty:
        return None
    return subset.iloc[0]
