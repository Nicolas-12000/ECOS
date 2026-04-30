from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging(settings.debug)

app = FastAPI(
    title="ECOS API",
    description="Early Control and Observation System — API de alerta temprana epidemiológica",
    version="0.2.0",
    debug=settings.debug,
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
        "version": "0.2.0",
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
