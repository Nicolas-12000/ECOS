from fastapi import APIRouter, Query
from app.schemas.epidemiology import NewsArticle
from app.scraping.scraping_service import fetch_rss_articles

router = APIRouter()

@router.get("/news", response_model=list[NewsArticle], summary="Noticias epidemiológicas de medios colombianos")
def get_news(
    lookback_days: int = Query(30, ge=1, le=180),
    disease: str | None = Query(None)
):
    articles = fetch_rss_articles(lookback_days=lookback_days)
    
    if disease:
        articles = [a for a in articles if disease.lower() in a.get("diseases", [])]

    # Map to schema
    results = []
    for a in articles:
        article = NewsArticle(
            title=a.get("title", ""),
            link=a.get("link", ""),
            source=a.get("source", ""),
            published=a.get("published", ""),
            summary=a.get("summary", ""),
            diseases=a.get("diseases", [])
        )
        results.append(article)
    return results
