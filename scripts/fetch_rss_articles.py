#!/usr/bin/env python3
"""Fetch RSS articles and write data/processed/signals_rss_articles.csv.

Uses backend scraping_service to avoid duplicating RSS parsing logic.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data/processed/signals_rss_articles.csv"

# Allow importing backend app module
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.scraping.scraping_service import fetch_rss_articles  # noqa: E402


def write_csv(df: pd.DataFrame, path: Path, append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if append and path.exists():
        existing = pd.read_csv(path)
        df = pd.concat([existing, df], ignore_index=True)
    # Deduplicate by link if available
    if "link" in df.columns:
        df = df.drop_duplicates(subset=["link"], keep="last")
    df.to_csv(path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch RSS articles and write CSV for DB loading")
    parser.add_argument("--lookback-days", type=int, default=30)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--debug", action="store_true", help="Print per-feed counts")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.INFO)
    articles = fetch_rss_articles(
        lookback_days=args.lookback_days,
        force_refresh=True,
        debug=args.debug,
    )
    rows = []
    for a in articles:
        rows.append({
            "source": a.get("source", ""),
            "title": a.get("title", ""),
            "summary": a.get("summary", ""),
            "link": a.get("link", ""),
            "published_at": a.get("published", ""),
            "diseases": json.dumps(a.get("diseases", [])),
            "relevance_score": a.get("relevance_score", 0),
        })

    df = pd.DataFrame(rows, columns=[
        "source",
        "title",
        "summary",
        "link",
        "published_at",
        "diseases",
        "relevance_score",
    ])

    write_csv(df, Path(args.out), append=args.append)
    if df.empty:
        print(f"[warn] no RSS articles matched filters -> {args.out} (0 rows)")
        return 2
    print(f"[ok] rss articles -> {args.out} ({len(df)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
