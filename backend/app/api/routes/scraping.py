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
