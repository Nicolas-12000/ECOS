#!/usr/bin/env python3
"""Fetch weekly early signals from Google Trends and RSS feeds.

Outputs:
- data/raw/signals_trends.csv
- data/raw/signals_rss.csv
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import time
from email.utils import parsedate_to_datetime
from pathlib import Path

import pandas as pd
import feedparser
from pytrends.request import TrendReq

from geo import DEPT_CODE_TO_ISO, DEPT_NAME_TO_CODE, normalize_text

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRENDS_OUT = REPO_ROOT / "data/raw/signals_trends.csv"
DEFAULT_RSS_OUT = REPO_ROOT / "data/raw/signals_rss.csv"

TREND_KEYWORDS = {
    "dengue": ["dengue sintomas", "fiebre dengue", "mosquito dengue"],
    "chikungunya": ["chikungunya sintomas", "fiebre chikungunya", "dolor articulaciones"],
    "zika": ["zika sintomas", "fiebre zika", "zika colombia"],
    "malaria": ["malaria sintomas", "paludismo", "malaria colombia"],
}

DISEASE_TERMS = {
    "dengue": ["dengue"],
    "chikungunya": ["chikungunya"],
    "zika": ["zika"],
    "malaria": ["malaria", "paludismo"],
}

RSS_FEEDS = [
    "https://www.eltiempo.com/rss/colombia.xml",
    "https://www.eltiempo.com/rss/salud.xml",
    "https://www.elcolombiano.com/rss/salud.xml",
    "https://www.elheraldo.co/rss.xml",
    "https://www.laopinion.com.co/rss.xml",
    "https://www.diariodelhuila.com/rss.xml",
    "https://www.noticiasrcn.com/rss",
    "https://www.caracol.com.co/rss/",
    "https://www.ins.gov.co/Noticias/Paginas/default.aspx?RSS=1",
]


def to_week_start(value: dt.datetime) -> dt.date:
    iso_year, iso_week, _ = value.isocalendar()
    return dt.date.fromisocalendar(iso_year, iso_week, 1)


def parse_date(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except Exception:
        return None


def detect_diseases(text: str) -> list[str]:
    hits = []
    for disease, terms in DISEASE_TERMS.items():
        for term in terms:
            if term in text:
                hits.append(disease)
                break
    return hits


def detect_departments(text: str) -> list[str]:
    hits = []
    for name, code in DEPT_NAME_TO_CODE.items():
        pattern = r"\b" + re.escape(name) + r"\b"
        if re.search(pattern, text):
            hits.append(code)
    return hits


def fetch_trends(timeframe: str, by_dept: bool, sleep_seconds: float) -> pd.DataFrame:
    rows = []
    pytrends = TrendReq(hl="es-CO", tz=-300)

    targets = [(None, "CO")]
    if by_dept:
        targets = [(code, geo) for code, geo in DEPT_CODE_TO_ISO.items()]

    for dept_code, geo in targets:
        for disease, keywords in TREND_KEYWORDS.items():
            try:
                pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
                data = pytrends.interest_over_time()
            except Exception:
                continue

            if data is None or data.empty:
                continue

            data = data.drop(columns=["isPartial"], errors="ignore")
            series = data.mean(axis=1)

            for idx, value in series.items():
                if isinstance(idx, pd.Timestamp):
                    timestamp = idx.to_pydatetime()
                else:
                    timestamp = pd.to_datetime(idx).to_pydatetime()
                week_start = to_week_start(timestamp)
                rows.append(
                    {
                        "week_start_date": week_start.isoformat(),
                        "disease": disease,
                        "trends_score": float(value),
                        "departamento_code": dept_code or "",
                    }
                )

            if sleep_seconds:
                time.sleep(sleep_seconds)

    return pd.DataFrame(rows)


def fetch_rss(lookback_days: int) -> pd.DataFrame:
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=lookback_days)
    rows = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in getattr(feed, "entries", []):
            published = parse_date(entry.get("published") or entry.get("updated"))
            if published is None:
                continue
            if published.tzinfo is None:
                published = published.replace(tzinfo=dt.timezone.utc)
            if published < cutoff.replace(tzinfo=dt.timezone.utc):
                continue

            text = f"{entry.get('title', '')} {entry.get('summary', '')}"
            normalized = normalize_text(text)
            diseases = detect_diseases(normalized.lower())
            if not diseases:
                continue

            departments = detect_departments(normalized)
            if not departments:
                departments = [""]

            week_start = to_week_start(published.astimezone(dt.timezone.utc))
            for disease in diseases:
                for dept_code in departments:
                    rows.append(
                        {
                            "week_start_date": week_start.isoformat(),
                            "disease": disease,
                            "departamento_code": dept_code,
                            "rss_mentions": 1,
                        }
                    )

    if not rows:
        return pd.DataFrame(columns=["week_start_date", "disease", "departamento_code", "rss_mentions"])

    df = pd.DataFrame(rows)
    grouped = (
        df.groupby(["week_start_date", "disease", "departamento_code"], dropna=False)
        .agg({"rss_mentions": "sum"})
        .reset_index()
    )
    return grouped


def write_csv(df: pd.DataFrame, path: Path, append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if append and path.exists():
        existing = pd.read_csv(path)
        df = pd.concat([existing, df], ignore_index=True)
        df = df.drop_duplicates()
    df.to_csv(path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Trends + RSS signals")
    parser.add_argument("--timeframe", default="today 5-y", help="Google Trends timeframe")
    parser.add_argument("--by-dept", action="store_true", help="Fetch Trends by departamento ISO code")
    parser.add_argument("--sleep", type=float, default=0.8, help="Seconds to sleep between Trends requests")
    parser.add_argument("--rss-lookback-days", type=int, default=180)
    parser.add_argument("--trends-output", default=str(DEFAULT_TRENDS_OUT))
    parser.add_argument("--rss-output", default=str(DEFAULT_RSS_OUT))
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    trends_df = fetch_trends(args.timeframe, args.by_dept, args.sleep)
    if not trends_df.empty:
        write_csv(trends_df, Path(args.trends_output), args.append)
        print(f"[ok] trends -> {args.trends_output} ({len(trends_df)})")
    else:
        print("[warn] no trends data fetched")

    rss_df = fetch_rss(args.rss_lookback_days)
    if not rss_df.empty:
        write_csv(rss_df, Path(args.rss_output), args.append)
        print(f"[ok] rss -> {args.rss_output} ({len(rss_df)})")
    else:
        print("[warn] no rss data fetched")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
