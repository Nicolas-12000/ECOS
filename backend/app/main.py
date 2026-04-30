import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging(settings.debug)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the ECOS API."""
    # ── Startup ─────────────────────────────────────────────────────────
    logger.info("ECOS API starting up...")

    # 1. Report data source
    try:
        from app.services.epidemiology import get_data_source
        source = get_data_source()
        logger.info("Data source: %s", source)
    except Exception as exc:
        logger.warning("Could not determine data source: %s", exc)

    # 2. Pre-warm the RSS scraping cache (runs in background, non-blocking)
    try:
        from app.scraping.scraping_service import fetch_rss_articles
        articles = fetch_rss_articles(lookback_days=30)
        logger.info("RSS scraping cache warmed: %d articles found", len(articles))
    except Exception as exc:
        logger.warning("RSS scraping warm-up failed (non-critical): %s", exc)

    # 3. Pre-load the curated dataset into memory
    try:
        from app.services.epidemiology import _load_df
        df = _load_df()
        logger.info("Curated dataset loaded: %d rows", len(df))
    except FileNotFoundError:
        logger.warning(
            "No curated dataset found. Run 'python scripts/generate_demo_data.py' "
            "to generate demo data, or 'python scripts/run_pipeline.py' for full data."
        )
    except Exception as exc:
        logger.warning("Failed to pre-load curated dataset: %s", exc)

    # 4. Check Groq API key
    if settings.groq_api_key:
        logger.info("Groq API key configured — RAG chat is enabled (model: %s)", settings.groq_model)
    else:
        logger.warning("Groq API key not configured — RAG chat will return fallback answers only")

    logger.info("ECOS API ready!")

    yield

    # ── Shutdown ────────────────────────────────────────────────────────
    logger.info("ECOS API shutting down...")


app = FastAPI(
    title="ECOS API",
    description="Early Control and Observation System — API de alerta temprana epidemiológica",
    version="0.3.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS — permite que el frontend Next.js se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "name": "ECOS API",
        "version": "0.3.0",
        "status": "ok",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/api/predict",
            "/api/history",
            "/api/signals",
            "/api/chat",
            "/api/alerts",
            "/api/scraping/rss",
        ],
    }
