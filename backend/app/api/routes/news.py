from fastapi import APIRouter, Query
import json
from app.schemas.epidemiology import NewsArticle
from app.scraping.scraping_service import fetch_rss_articles
from app.core.db import get_db_connection

router = APIRouter()

@router.get("/news", response_model=list[NewsArticle], summary="Noticias epidemiológicas de medios colombianos")
def get_news(
    lookback_days: int = Query(30, ge=1, le=180),
    disease: str | None = Query(None)
):
    # Prefer DB if available
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                params = [lookback_days]
                where = "published_at >= now() - (%s || ' days')::interval"
                if disease:
                    where += " AND diseases ? %s"
                    params.append(disease.lower())
                cur.execute(
                    f"""
                    SELECT source, title, summary, link, published_at, diseases
                    FROM public.raw_rss_articles
                    WHERE {where}
                    ORDER BY published_at DESC
                    LIMIT 200
                    """,
                    params,
                )
                rows = cur.fetchall()
        if rows:
            results = []
            for row in rows:
                diseases = row[5]
                if isinstance(diseases, str):
                    try:
                        diseases = json.loads(diseases)
                    except Exception:
                        diseases = []
                article = NewsArticle(
                    title=row[1] or "",
                    link=row[3] or "",
                    source=row[0] or "",
                    published=(row[4].isoformat() if row[4] else ""),
                    summary=row[2] or "",
                    diseases=diseases or [],
                )
                results.append(article)
            return results
    except Exception:
        # Fall back to live scrape if DB not configured
        pass

    articles = fetch_rss_articles(lookback_days=lookback_days)
    if disease:
        articles = [a for a in articles if disease.lower() in a.get("diseases", [])]
    return [
        NewsArticle(
            title=a.get("title", ""),
            link=a.get("link", ""),
            source=a.get("source", ""),
            published=a.get("published", ""),
            summary=a.get("summary", ""),
            diseases=a.get("diseases", []),
        )
        for a in articles
    ]
