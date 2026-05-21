"""RSS scraping service — fetches epidemiological news from Colombian media.

Uses httpx + xml.etree.ElementTree instead of feedparser for Python 3.14
compatibility (feedparser depends on sgmllib3k which doesn't support 3.14).

Results are cached for 30 minutes to avoid hammering RSS feeds.
"""

from __future__ import annotations

import datetime as dt
import logging
import time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import httpx

logger = logging.getLogger(__name__)

def _load_rss_feeds() -> list[tuple[str, str]]:
    from pathlib import Path
    import json
    repo_root = Path(__file__).resolve().parents[3]
    feeds_path = repo_root / "data" / "rss_feeds.json"
    if not feeds_path.exists():
        return [
            ("El Tiempo", "https://www.eltiempo.com/rss/colombia.xml"),
            ("El Tiempo Salud", "https://www.eltiempo.com/rss/salud.xml"),
            ("La Opinion", "https://www.laopinion.co/rss.xml"),
        ]
    try:
        data = json.loads(feeds_path.read_text(encoding="utf-8"))
        return [(item.get("name", "RSS"), item.get("url", "")) for item in data if item.get("url")]
    except Exception:
        return [
            ("El Tiempo", "https://www.eltiempo.com/rss/colombia.xml"),
            ("El Tiempo Salud", "https://www.eltiempo.com/rss/salud.xml"),
            ("La Opinion", "https://www.laopinion.co/rss.xml"),
        ]

RSS_FEEDS = _load_rss_feeds()

REQUEST_HEADERS = {
    "User-Agent": "ECOS/1.0 (+https://ecos.local)",
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
}

DISEASE_TERMS = {
    "dengue": [
        "dengue", "fiebre dengue", "dengue grave", "dengue hemorr", "dengue hemorrag",
        "aedes aegypti", "aedes", "arbovirosis",
    ],
    "chikungunya": [
        "chikungunya", "chikunguña", "fiebre chikungunya", "dolor articular",
    ],
    "zika": [
        "zika", "virus del zika", "microcefalia",
    ],
    "malaria": [
        "malaria", "paludismo", "plasmodium", "anopheles",
    ],
}

ALERT_TERMS = [
    "brote", "epidemia", "alerta sanitaria", "alerta epidemiológica",
    "emergencia sanitaria", "aumento de casos", "casos confirmados",
    "mosquito", "vector", "fumigación",
]

# Cache control
_cache: dict = {"data": None, "timestamp": 0.0}
CACHE_TTL = 1800  # 30 minutes


def _parse_date(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except Exception:
        return None


def _detect_diseases(text: str) -> list[str]:
    lowered = text.lower()
    hits = []
    for disease, terms in DISEASE_TERMS.items():
        if any(term in lowered for term in terms):
            hits.append(disease)
    return hits


def _relevance_score(text: str) -> float:
    lowered = text.lower()
    score = 0.0
    for term in ALERT_TERMS:
        if term in lowered:
            score += 1.0
    for terms in DISEASE_TERMS.values():
        for term in terms:
            if term in lowered:
                score += 0.5
    return min(score / 5.0, 1.0)


def _parse_rss_xml(xml_text: str) -> list[dict]:
    """Parse RSS XML manually using xml.etree.ElementTree."""
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    # Handle both RSS 2.0 (<channel><item>) and Atom (<entry>)
    for item_el in root.iter("item"):
        title = (item_el.findtext("title") or "").strip()
        link = (item_el.findtext("link") or "").strip()
        description = (item_el.findtext("description") or "").strip()
        pub_date = (item_el.findtext("pubDate") or "").strip()
        items.append({
            "title": title,
            "link": link,
            "description": description[:500],
            "pubDate": pub_date,
        })

    # Atom feeds
    for entry_el in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = (entry_el.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link_el = entry_el.find("{http://www.w3.org/2005/Atom}link")
        link = link_el.get("href", "") if link_el is not None else ""
        summary = (entry_el.findtext("{http://www.w3.org/2005/Atom}summary") or "").strip()
        updated = (entry_el.findtext("{http://www.w3.org/2005/Atom}updated") or "").strip()
        items.append({
            "title": title,
            "link": link,
            "description": summary[:500],
            "pubDate": updated,
        })

    return items


def fetch_rss_articles(
    lookback_days: int = 30,
    force_refresh: bool = False,
    debug: bool = False,
) -> list[dict]:
    """Fetch and filter epidemiological articles from RSS feeds."""
    now = time.time()
    if not force_refresh and _cache["data"] is not None and (now - _cache["timestamp"]) < CACHE_TTL:
        return _cache["data"]

    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=lookback_days)
    articles = []
    total_items = 0
    total_matched = 0

    for source_name, feed_url in RSS_FEEDS:
        try:
            resp = httpx.get(feed_url, timeout=15.0, follow_redirects=True, headers=REQUEST_HEADERS)
            resp.raise_for_status()
            items = _parse_rss_xml(resp.text)

            total_items += len(items)
            matched_feed = 0
            sample_titles = [it.get("title", "").strip() for it in items[:5]]
            for item in items:
                published = _parse_date(item.get("pubDate"))
                if published is None:
                    continue
                if published.tzinfo is None:
                    published = published.replace(tzinfo=dt.timezone.utc)
                if published < cutoff:
                    continue

                title = item.get("title", "")
                summary = item.get("description", "")
                full_text = f"{title} {summary}"

                diseases = _detect_diseases(full_text)
                if not diseases:
                    continue

                score = _relevance_score(full_text)
                articles.append({
                    "source": source_name,
                    "title": title,
                    "summary": summary[:300],
                    "link": item.get("link", ""),
                    "published": published.isoformat(),
                    "diseases": diseases,
                    "relevance_score": round(score, 2),
                })
                matched_feed += 1
                total_matched += 1
        except Exception as exc:
            logger.warning("Failed to fetch RSS from %s: %s", source_name, exc)

        if debug:
            print(f"[rss] {source_name}: items={len(items)} matched={matched_feed}")
            if matched_feed == 0 and sample_titles:
                print("[rss] sample titles:")
                for t in sample_titles:
                    if t:
                        print(f"  - {t}")

    if debug:
        print(f"[rss] total items={total_items} matched={total_matched}")

    articles.sort(key=lambda a: a["relevance_score"], reverse=True)
    _cache["data"] = articles
    _cache["timestamp"] = now
    return articles
