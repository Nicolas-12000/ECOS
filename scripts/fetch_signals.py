#!/usr/bin/env python3
"""
Extrae señales tempranas (Google Trends y noticias RSS).
Guarda los resultados como CSV en data/raw.
"""

import argparse
import datetime as dt
import time
from pathlib import Path

import feedparser
import pandas as pd
from pytrends.request import TrendReq

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data/raw"

DISEASES = ["dengue", "chikungunya", "zika", "malaria"]
RSS_FEEDS = [
    "https://www.who.int/rss-feeds/news-english.xml",
    "https://www.paho.org/en/rss.xml"
]


def fetch_google_trends(retry_delay: int = 15) -> pd.DataFrame:
    """Extrae interés de búsqueda semanal por enfermedad desde 2013."""
    pytrends = TrendReq(hl='es-CO', tz=300)
    dfs = []
    
    # We fetch a large window (2013 to present) because sivigila data usually goes back.
    # Google Trends returns weekly data automatically for >5 year spans.
    for disease in DISEASES:
        print(f"[trends] Fetching data for {disease}...")
        try:
            pytrends.build_payload([disease], cat=0, timeframe="2013-01-01 2024-01-01", geo='CO', gprop='')
            # Get interest over time
            df = pytrends.interest_over_time()
            if df.empty:
                print(f"[warn] No trends data for {disease}")
                continue
                
            df = df.reset_index()
            # Drop the isPartial column
            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])
                
            df = df.rename(columns={disease: "trends_score", "date": "week_start_date"})
            df["disease"] = disease
            dfs.append(df)
            
            # Prevent rate-limits
            print(f"[trends] Waiting {retry_delay}s to avoid rate limits...")
            time.sleep(retry_delay)
            
        except Exception as e:
            print(f"[error] Failed to fetch {disease}: {e}")
            
    if not dfs:
        return pd.DataFrame()
        
    return pd.concat(dfs, ignore_index=True)


def fetch_rss_mock_history() -> pd.DataFrame:
    """
    Dado que las fuentes RSS solo entregan los ultimos meses/días, 
    crearemos una historia base ruidosa correlacionada ligeramente
    con meses de lluvia para propósitos del pipeline y entrenamiento V2.
    """
    print("[rss] Generating mock historical baseline for ML training...")
    dates = pd.date_range(start="2013-01-01", end="2024-01-01", freq="W-MON")
    records = []
    
    import random
    random.seed(42)
    
    for d in dates:
        for disease in DISEASES:
            # Random score between 0 and 10 mentions, boosted slightly in wet months (Apr, May, Oct, Nov)
            base = random.randint(0, 3)
            if d.month in [4, 5, 10, 11] and disease in ["dengue", "malaria"]:
                base += random.randint(0, 5)
                
            records.append({
                "week_start_date": d,
                "disease": disease,
                "rss_mentions": base
            })
            
    return pd.DataFrame(records)


def parse_live_rss() -> pd.DataFrame:
    """Agrega conteo de menciones reales de los feeds RSS actuales."""
    print("[rss] Fetching live RSS feeds...")
    records = {}
    current_week = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()
                for d in DISEASES:
                    if d in text:
                        key = (current_week, d)
                        records[key] = records.get(key, 0) + 1
        except Exception as e:
            print(f"[error] Failed to parse {url}: {e}")
            
    df_records = []
    for (week, disease), mentions in records.items():
        df_records.append({
            "week_start_date": pd.Timestamp(week),
            "disease": disease,
            "rss_mentions": mentions
        })
        
    return pd.DataFrame(df_records)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-trends", action="store_true", help="Omitir pandas/trends scraping")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    if not args.skip_trends:
        print("[info] Iniciando extracción de Google Trends...")
        trends_df = fetch_google_trends()
        if not trends_df.empty:
            out_trends = RAW_DIR / "signals_trends.csv"
            trends_df.to_csv(out_trends, index=False)
            print(f"[ok] Trends guardados en {out_trends}")
    else:
        print("[skip] Google Trends omitido.")

    print("[info] Procesando RSS y baseline simulado...")
    rss_hist = fetch_rss_mock_history()
    rss_live = parse_live_rss()
    
    if not rss_live.empty:
        rss_df = pd.concat([rss_hist, rss_live], ignore_index=True)
    else:
        rss_df = rss_hist
        
    out_rss = RAW_DIR / "signals_rss.csv"
    rss_df.to_csv(out_rss, index=False)
    print(f"[ok] RSS guardados en {out_rss}")


if __name__ == "__main__":
    main()
