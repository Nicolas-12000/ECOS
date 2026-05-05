import logging

from fastapi import APIRouter, Query

from app.scraping.scraping_service import fetch_rss_articles

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/scraping/rss",
    summary="Noticias epidemiológicas de medios colombianos (RSS)",
    response_model=list[dict],
)
def scraping_rss(
    lookback_days: int = Query(30, ge=1, le=180, description="Días hacia atrás para buscar"),
    disease: str | None = Query(None, description="Filtrar por enfermedad (opcional)"),
):
    """
    Retorna artículos de medios colombianos que mencionan dengue, chikungunya,
    zika o malaria. Los resultados se cachean por 30 minutos.
    """
    articles = fetch_rss_articles(lookback_days=lookback_days)

    if disease:
        articles = [a for a in articles if disease.lower() in a.get("diseases", [])]

    return articles


@router.post(
    "/scraping/trigger",
    summary="Disparar proceso de scraping manual (Trends/RSS)",
    response_model=dict,
)
def trigger_scraping():
    """
    Inicia el proceso de scraping de señales (Trends y RSS) si no se ha ejecutado 
    en la última semana. Si está en cooldown, retorna el tiempo restante.
    """
    import os
    import json
    import subprocess
    import sys
    from datetime import datetime, timedelta
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[4]
    status_file = repo_root / "data" / "scraping_status.json"
    python_exe = sys.executable
    script_path = repo_root / "scripts" / "fetch_signals.py"

    # Cargar estado
    if status_file.exists():
        with open(status_file, "r") as f:
            status = json.load(f)
    else:
        status = {"last_run": "2000-01-01T00:00:00", "status": "idle"}

    last_run = datetime.fromisoformat(status["last_run"])
    cooldown_period = timedelta(days=7)
    now = datetime.now()

    if now - last_run < cooldown_period:
        remaining = cooldown_period - (now - last_run)
        return {
            "status": "cooldown",
            "message": f"El scraping está en cooldown. Intenta de nuevo en {remaining.days} días.",
            "last_run": status["last_run"],
            "remaining_days": remaining.days
        }

    # Ejecutar en segundo plano
    try:
        # Actualizar estado a running
        status["status"] = "running"
        status["last_run"] = now.isoformat()
        with open(status_file, "w") as f:
            json.dump(status, f, indent=4)

        # Usar Popen para no bloquear la API
        subprocess.Popen(
            [python_exe, str(script_path)],
            cwd=str(repo_root),
            start_new_session=True
        )

        return {
            "status": "started",
            "message": "Proceso de scraping iniciado en segundo plano.",
            "last_run": status["last_run"]
        }
    except Exception as e:
        logger.error("Error triggering scraper: %s", e)
        return {"status": "error", "message": str(e)}
