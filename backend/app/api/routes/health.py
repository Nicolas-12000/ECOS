import logging
from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[4]


@router.get("/health")
def health():
    """Health check — funciona sin DB, reporta estado de cada componente."""
    payload = {"status": "ok"}

    # Check database (optional)
    database_url = settings.resolved_database_url()
    if database_url:
        try:
            import psycopg

            with psycopg.connect(database_url, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("select 1;")
            payload["database"] = "ok"
        except Exception:
            logger.warning("Database health check failed")
            payload["database"] = "unavailable"
    else:
        payload["database"] = "not_configured"

    # Check which data source is active
    try:
        from app.services.epidemiology import get_data_source
        payload["data_source"] = get_data_source()
    except Exception:
        payload["data_source"] = "unknown"

    # Check curated data (local files)
    data_paths = [
        REPO_ROOT / "data/processed/curated_weekly_parquet",
        REPO_ROOT / "data/processed/curated_weekly_csv",
        REPO_ROOT / "data/processed/curated_weekly_fresh_parquet",
        REPO_ROOT / "data/processed/curated_weekly_fresh_csv",
    ]
    payload["curated_data_local"] = "missing"
    for p in data_paths:
        if p.exists():
            payload["curated_data_local"] = "ok"
            payload["curated_data_path"] = str(p.name)
            break

    # Check model
    model_paths = [
        REPO_ROOT / "models/final_model.joblib",
        REPO_ROOT / "models/baseline_v2.joblib",
        REPO_ROOT / "models/baseline_v0.joblib",
    ]
    payload["model"] = "missing"
    for p in model_paths:
        if p.exists():
            payload["model"] = "ok"
            payload["model_path"] = str(p.name)
            break

    # Check Groq
    payload["groq"] = "ok" if settings.groq_api_key else "not_configured"

    # Check semantic index
    index_path = REPO_ROOT / "models/semantic/index.faiss"
    payload["semantic_index"] = "ok" if index_path.exists() else "missing"

    # Check RSS scraping
    try:
        from app.scraping.scraping_service import _cache
        if _cache["data"] is not None:
            payload["rss_scraping"] = f"cached ({len(_cache['data'])} articles)"
        else:
            payload["rss_scraping"] = "not_cached"
    except Exception:
        payload["rss_scraping"] = "unavailable"

    return payload
