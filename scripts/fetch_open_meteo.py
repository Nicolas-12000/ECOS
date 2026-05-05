#!/usr/bin/env python3
"""Fetch weekly aggregated Open‑Meteo data for departments and write CSV.

Produces `data/raw/open_meteo_weekly.csv` with columns:
 - departamento_code, week_start_date, temp_max_c, temp_min_c, temp_avg_c, precipitation_mm

Behaviour:
 - By default fetches the last `--weeks` weeks of daily data and aggregates to week.
 - If `--append` is set it appends to existing CSV and deduplicates by (departamento_code, week_start_date).
 - Keeps only the most recent `--retain-weeks` weeks in the final CSV (rolling window).
"""

from __future__ import annotations

import argparse
import datetime as dt
import time
from pathlib import Path
import statistics

import httpx
import pandas as pd

from geo import DEPT_CODE_TO_LATLON

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data/raw/open_meteo_weekly.csv"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def to_week_start(d: dt.date) -> dt.date:
    iso = d.isocalendar()
    return dt.date.fromisocalendar(iso[0], iso[1], 1)


def fetch_daily_for_coord(lat: float, lon: float, start_date: str, end_date: str, timeout: float = 30.0) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
        ]),
        "timezone": "UTC",
        "start_date": start_date,
        "end_date": end_date,
    }
    with httpx.Client(timeout=timeout) as client:
        r = client.get(OPEN_METEO_URL, params=params)
        r.raise_for_status()
        return r.json()


def aggregate_weekly(daily: dict) -> list[dict]:
    # daily expected keys: daily.time, daily.temperature_2m_max, etc.
    times = daily.get("daily", {}).get("time", [])
    if not times:
        return []

    tmp_max = daily.get("daily", {}).get("temperature_2m_max", [])
    tmp_min = daily.get("daily", {}).get("temperature_2m_min", [])
    tmp_mean = daily.get("daily", {}).get("temperature_2m_mean", [])
    precip = daily.get("daily", {}).get("precipitation_sum", [])

    rows_by_week: dict[dt.date, list[dict]] = {}
    for i, t in enumerate(times):
        d = dt.date.fromisoformat(t)
        wk = to_week_start(d)
        rows_by_week.setdefault(wk, []).append({
            "date": d,
            "temp_max": tmp_max[i] if i < len(tmp_max) else None,
            "temp_min": tmp_min[i] if i < len(tmp_min) else None,
            "temp_mean": tmp_mean[i] if i < len(tmp_mean) else None,
            "precip": precip[i] if i < len(precip) else None,
        })

    out = []
    for wk, items in rows_by_week.items():
        max_vals = [it["temp_max"] for it in items if it["temp_max"] is not None]
        min_vals = [it["temp_min"] for it in items if it["temp_min"] is not None]
        mean_vals = [it["temp_mean"] for it in items if it["temp_mean"] is not None]
        precip_vals = [it["precip"] for it in items if it["precip"] is not None]

        out.append({
            "week_start_date": wk.isoformat(),
            "temp_max_c": float(max(max_vals)) if max_vals else None,
            "temp_min_c": float(min(min_vals)) if min_vals else None,
            "temp_avg_c": float(statistics.mean(mean_vals)) if mean_vals else None,
            "precipitation_mm": float(sum(precip_vals)) if precip_vals else 0.0,
        })

    return out


def write_csv(df: pd.DataFrame, path: Path, append: bool, retain_weeks: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if append and path.exists():
        existing = pd.read_csv(path, parse_dates=["week_start_date"])
        df_existing = existing.copy()
        df = pd.concat([df_existing, df], ignore_index=True)

    # Normalize types and dedupe
    df["week_start_date"] = pd.to_datetime(df["week_start_date"]).dt.date
    df = df.drop_duplicates(subset=["departamento_code", "week_start_date"], keep="last")

    # Retain only last `retain_weeks` weeks
    if not df.empty and retain_weeks and retain_weeks > 0:
        max_week = df["week_start_date"].max()
        cutoff = max_week - dt.timedelta(weeks=retain_weeks - 1)
        df = df[df["week_start_date"] >= cutoff]

    # Ensure canonical ordering
    cols = ["departamento_code", "week_start_date", "temp_max_c", "temp_min_c", "temp_avg_c", "precipitation_mm"]
    df = df.loc[:, [c for c in cols if c in df.columns]]
    # Write with ISO date strings
    df["week_start_date"] = df["week_start_date"].apply(lambda d: d.isoformat() if not pd.isna(d) else "")
    df.to_csv(path, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Open‑Meteo weekly and write data/raw/open_meteo_weekly.csv")
    parser.add_argument("--weeks", type=int, default=6, help="How many past weeks to fetch (default 6)")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output CSV path")
    parser.add_argument("--append", action="store_true", help="Append to existing CSV instead of overwriting")
    parser.add_argument("--retain-weeks", type=int, default=4, help="Keep only this many recent weeks in CSV (default 4)")
    parser.add_argument("--sleep", type=float, default=0.5, help="Seconds to sleep between API calls")
    args = parser.parse_args()

    end_date = dt.date.today()
    start_date = end_date - dt.timedelta(weeks=args.weeks)

    records = []
    for code, (lat, lon) in DEPT_CODE_TO_LATLON.items():
        try:
            payload = fetch_daily_for_coord(lat, lon, start_date.isoformat(), end_date.isoformat())
            weekly = aggregate_weekly(payload)
            for wk in weekly:
                row = {"departamento_code": code}
                row.update(wk)
                records.append(row)
            time.sleep(args.sleep)
        except Exception as e:
            print(f"[warn] failed fetching for {code}: {e}")

    if not records:
        print("[warn] no open-meteo data fetched; aborting write")
        return 1

    df = pd.DataFrame(records)
    out_path = Path(args.out)
    write_csv(df, out_path, append=args.append, retain_weeks=args.retain_weeks)
    print(f"[ok] open-meteo weekly written to {out_path} ({len(df)} rows fetched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
