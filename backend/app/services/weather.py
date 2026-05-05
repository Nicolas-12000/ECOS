"""Open-Meteo weekly aggregation service."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable

import httpx


@dataclass
class WeeklyWeather:
    week_start_date: str
    temperature_2m_max: float | None
    temperature_2m_min: float | None
    temperature_2m_mean: float | None
    precipitation_sum: float | None
    relative_humidity_2m_mean: float | None


def _to_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def _week_start(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


def _safe_mean(values: Iterable[float]) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(sum(vals) / len(vals))


def _safe_sum(values: Iterable[float]) -> float | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(sum(vals))


def fetch_open_meteo_weekly(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
) -> list[WeeklyWeather]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "relative_humidity_2m_mean",
        ],
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "America/Bogota",
    }

    resp = httpx.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=30.0)
    resp.raise_for_status()
    payload = resp.json()

    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    humid = daily.get("relative_humidity_2m_mean", [])

    grouped: dict[dt.date, list[tuple[float | None, float | None, float | None, float | None]]] = {}
    for idx, date_str in enumerate(dates):
        day = _to_date(date_str)
        week = _week_start(day)
        grouped.setdefault(week, []).append(
            (
                tmax[idx] if idx < len(tmax) else None,
                tmin[idx] if idx < len(tmin) else None,
                precip[idx] if idx < len(precip) else None,
                humid[idx] if idx < len(humid) else None,
            )
        )

    weekly: list[WeeklyWeather] = []
    for week_start, rows in sorted(grouped.items()):
        max_vals = [r[0] for r in rows]
        min_vals = [r[1] for r in rows]
        precip_vals = [r[2] for r in rows]
        humid_vals = [r[3] for r in rows]

        temp_mean_vals = []
        for mx, mn in zip(max_vals, min_vals):
            if mx is None or mn is None:
                continue
            temp_mean_vals.append((mx + mn) / 2.0)

        weekly.append(
            WeeklyWeather(
                week_start_date=week_start.isoformat(),
                temperature_2m_max=max(max_vals) if max_vals else None,
                temperature_2m_min=min(min_vals) if min_vals else None,
                temperature_2m_mean=_safe_mean(temp_mean_vals),
                precipitation_sum=_safe_sum(precip_vals),
                relative_humidity_2m_mean=_safe_mean(humid_vals),
            )
        )

    return weekly
