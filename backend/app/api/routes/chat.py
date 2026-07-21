import logging
import re
import statistics
import datetime as dt
import uuid
from pathlib import Path
from typing import Dict, List

try:
    import pandas as pd
except ImportError:
    pd = None

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.epidemiology import ChatRequest, ChatResponse, ChatSource
from app.services.epidemiology import VALID_DISEASES, get_history, get_last_known_features, get_mobility, _load_departamento_coords
from app.services import rag
from app.services.weather import fetch_open_meteo_weekly
from app.core.db import get_db_connection
from app.core.epi_date import find_date_in_text

# Importación opcional de predict_cases (evita cargar dependencias pesadas de ML)
try:
    from app.services.prediction import predict_cases
    PREDICT_AVAILABLE = True
except Exception:
    PREDICT_AVAILABLE = False
    predict_cases = None

try:
    from app.services.semantic import available as semantic_available, search as semantic_search
except Exception:
    semantic_available = lambda: False
    semantic_search = lambda q, k=3: []

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory chat history cache (session_id -> list of messages)
chat_history_cache: Dict[str, List[Dict[str, str]]] = {}

REPO_ROOT = Path(__file__).resolve().parents[4]

# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------

DEPTO_NAME_TO_CODE: dict[str, str] = {
    "amazonas": "91", "antioquia": "05", "arauca": "81", "atlantico": "08",
    "atlántico": "08", "bolivar": "13", "bolívar": "13", "boyaca": "15",
    "boyacá": "15", "caldas": "17", "caqueta": "18", "caquetá": "18",
    "casanare": "85", "cauca": "19", "cesar": "20", "choco": "27",
    "chocó": "27", "cordoba": "23", "córdoba": "23", "cundinamarca": "25",
    "guainia": "94", "guainía": "94", "guaviare": "95", "huila": "41",
    "la guajira": "44", "magdalena": "47", "meta": "50", "narino": "52",
    "nariño": "52", "norte de santander": "54", "putumayo": "86",
    "quindio": "63", "quindío": "63", "risaralda": "66", "san andres": "88",
    "san andrés": "88", "santander": "68", "sucre": "70", "tolima": "73",
    "valle del cauca": "76", "vaupes": "97", "vaupés": "97", "vichada": "99",
    "bogota": "11", "bogotá": "11",
}

CLIMATE_KEYWORDS = {
    "precipitacion", "precipitación", "lluvia", "lluvias", "temperatura",
    "temp", "calor", "humedad", "clima", "climatico", "climático",
}

NATIONAL_KEYWORDS = {
    "colombia", "nacional", "país", "pais", "total", "todos",
    "nivel nacional", "a nivel nacional",
}

REGION_KEYWORDS = {
    "region", "región", "pacifico", "pacífico", "caribe", "andina",
    "orinoquia", "orinoquía", "amazonia", "amazonía", "insular",
}


# ---------------------------------------------------------------------------
# DB Query Functions
# ---------------------------------------------------------------------------

def _db_execute(query: str, params: tuple = ()) -> list:
    """Ejecuta una consulta y retorna filas como listas."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()
    except Exception as e:
        logger.error("DB query error: %s", e)
        return []


def _query_climate_by_depto(departamento_code: str) -> dict | None:
    """Temperatura y precipitación promedio/min/max para un departamento."""
    rows = _db_execute("""
        SELECT
            ROUND(AVG(NULLIF(temp_avg_c, 0))::numeric, 2)         AS avg_temp,
            ROUND(MIN(NULLIF(temp_min_c, 0))::numeric, 2)         AS min_temp,
            ROUND(MAX(NULLIF(temp_max_c, 0))::numeric, 2)         AS max_temp,
            ROUND(AVG(NULLIF(precipitation_mm, 0))::numeric, 2)   AS avg_precip,
            ROUND(MAX(NULLIF(precipitation_mm, 0))::numeric, 2)   AS max_precip,
            MIN(week_start_date)                                   AS data_from,
            MAX(week_start_date)                                   AS data_to
        FROM public.fact_core_weekly
        WHERE departamento_code = %s
          AND temp_avg_c IS NOT NULL
          AND temp_avg_c > 0
    """, (departamento_code,))
    if not rows or rows[0][0] is None:
        return None
    r = rows[0]
    return {
        "avg_temp": r[0], "min_temp": r[1], "max_temp": r[2],
        "avg_precip": r[3], "max_precip": r[4],
        "data_from": str(r[5]), "data_to": str(r[6]),
    }


def _query_cases_by_depto(departamento_code: str, disease: str | None) -> dict | None:
    """Casos históricos completos por departamento, opcionalmente filtrado por enfermedad."""
    disease_filter = "AND disease = %s" if disease else ""
    params = (departamento_code, disease) if disease else (departamento_code,)

    rows = _db_execute(f"""
        SELECT SUM(cases_total), MIN(week_start_date), MAX(week_start_date), COUNT(*)
        FROM public.fact_core_weekly
        WHERE departamento_code = %s {disease_filter}
    """, params)
    if not rows or rows[0][0] is None:
        return None
    total_hist, min_date, max_date, n_weeks = rows[0]

    year_rows = _db_execute(f"""
        SELECT epi_year, SUM(cases_total), AVG(cases_total), MAX(cases_total)
        FROM public.fact_core_weekly
        WHERE departamento_code = %s {disease_filter}
        GROUP BY epi_year ORDER BY epi_year
    """, params)
    by_year = {}
    year_data = []
    for r in year_rows:
        by_year[r[0]] = {
            "total": int(r[1]),
            "avg_weekly": round(float(r[2]), 2) if r[2] else 0,
            "max_weekly": int(r[3]) if r[3] else 0
        }
        year_data.append((r[0], int(r[1])))
    
    peak_year = max(by_year, key=lambda y: by_year[y]["total"]) if by_year else None

    if disease is None:
        dis_rows = _db_execute("""
            SELECT disease, SUM(cases_total), AVG(cases_total)
            FROM public.fact_core_weekly
            WHERE departamento_code = %s
            GROUP BY disease ORDER BY 2 DESC
        """, (departamento_code,))
        by_disease = {r[0]: {"total": int(r[1]), "avg_weekly": round(float(r[2]), 2) if r[2] else 0} for r in dis_rows}
    else:
        by_disease = {}

    recent_rows = _db_execute(f"""
        SELECT epi_year, epi_week, SUM(cases_total), week_start_date
        FROM public.fact_core_weekly
        WHERE departamento_code = %s {disease_filter}
        GROUP BY epi_year, epi_week, week_start_date
        ORDER BY week_start_date DESC LIMIT 12
    """, params)
    recent = [{"year": r[0], "week": r[1], "cases": int(r[2]), "date": str(r[3])} for r in recent_rows]
    
    # Obtener datos estacionales (mismos meses en años anteriores)
    seasonal_comparison = {}
    if recent:
        latest_epi_week = recent[0]["week"]
        # Consultar casos de las mismas semanas en años anteriores
        seasonal_params = list(params)  # Copiar params existentes
        seasonal_params.extend([max(1, latest_epi_week - 4), latest_epi_week])
        seasonal_rows = _db_execute(f"""
            SELECT epi_year, epi_week, SUM(cases_total)
            FROM public.fact_core_weekly
            WHERE departamento_code = %s {disease_filter}
            AND epi_week BETWEEN %s AND %s
            GROUP BY epi_year, epi_week
            ORDER BY epi_year DESC, epi_week
        """, tuple(seasonal_params))
        
        for r in seasonal_rows:
            if r[0] not in seasonal_comparison:
                seasonal_comparison[r[0]] = []
            seasonal_comparison[r[0]].append({"week": r[1], "cases": int(r[2])})

    # Calcular estadísticas básicas
    all_weeks = _db_execute(f"""
        SELECT SUM(cases_total)
        FROM public.fact_core_weekly
        WHERE departamento_code = %s {disease_filter}
        GROUP BY epi_year, epi_week
    """, params)
    all_cases = [int(r[0]) for r in all_weeks if r[0] is not None]
    stats = {}
    if all_cases:
        stats = {
            "min_weekly": min(all_cases),
            "max_weekly": max(all_cases),
            "avg_weekly": round(statistics.mean(all_cases), 2),
            "median_weekly": round(statistics.median(all_cases), 2),
            "p75_weekly": _percentile(all_cases, 75),
            "p90_weekly": _percentile(all_cases, 90)
        }

    return {
        "total_historical": int(total_hist),
        "by_year": by_year,
        "by_disease": by_disease,
        "peak_year": peak_year,
        "peak_cases": by_year.get(peak_year, {}).get("total", 0) if peak_year else 0,
        "recent_weeks": recent,
        "seasonal_comparison": seasonal_comparison,
        "statistics": stats,
        "data_from": str(min_date),
        "data_to": str(max_date),
        "n_weeks": n_weeks,
    }


def _query_national_summary(disease: str | None = None) -> dict | None:
    """Total de casos a nivel nacional."""
    disease_filter = "WHERE disease = %s" if disease else ""
    params = (disease,) if disease else ()

    rows = _db_execute(f"""
        SELECT SUM(cases_total), MIN(week_start_date), MAX(week_start_date), COUNT(DISTINCT CONCAT(epi_year, '-', epi_week))
        FROM public.fact_core_weekly {disease_filter}
    """, params)
    if not rows or rows[0][0] is None:
        return None
    total_historical, min_date, max_date, n_weeks = rows[0]

    year_rows = _db_execute(f"""
        SELECT epi_year, SUM(cases_total), AVG(cases_total), MAX(cases_total)
        FROM public.fact_core_weekly {disease_filter}
        GROUP BY epi_year ORDER BY epi_year
    """, params)
    by_year = {}
    for r in year_rows:
        by_year[r[0]] = {
            "total": int(r[1]),
            "avg_weekly": round(float(r[2]), 2) if r[2] else 0,
            "max_weekly": int(r[3]) if r[3] else 0
        }

    peak_year = max(by_year, key=lambda y: by_year[y]["total"]) if by_year else None
    peak_cases = by_year.get(peak_year, {}).get("total", 0) if peak_year else 0

    if not disease:
        dis_rows = _db_execute("""
            SELECT disease, SUM(cases_total), AVG(cases_total)
            FROM public.fact_core_weekly
            GROUP BY disease ORDER BY 2 DESC
        """)
        by_disease = {r[0]: {"total": int(r[1]), "avg_weekly": round(float(r[2]), 2) if r[2] else 0} for r in dis_rows}
    else:
        by_disease = {}

    recent_rows = _db_execute(f"""
        SELECT epi_year, epi_week, SUM(cases_total), week_start_date
        FROM public.fact_core_weekly {disease_filter}
        GROUP BY epi_year, epi_week, week_start_date
        ORDER BY week_start_date DESC LIMIT 12
    """, params)
    recent = [{"year": r[0], "week": r[1], "cases": int(r[2]), "date": str(r[3])} for r in recent_rows]

    seasonal_comparison = {}
    if recent:
        latest_epi_week = recent[0]["week"]
        seasonal_params = list(params) 
        seasonal_params.extend([max(1, latest_epi_week - 4), latest_epi_week])
        if disease_filter:
            seasonal_filter = f"AND epi_week BETWEEN %s AND %s"
            full_query = f"{disease_filter} {seasonal_filter}"
        else:
            seasonal_filter = f"WHERE epi_week BETWEEN %s AND %s"
            full_query = seasonal_filter
            
        seasonal_rows = _db_execute(f"""
            SELECT epi_year, epi_week, SUM(cases_total)
            FROM public.fact_core_weekly {full_query}
            GROUP BY epi_year, epi_week
            ORDER BY epi_year DESC, epi_week
        """, tuple(seasonal_params))
        
        for r in seasonal_rows:
            if r[0] not in seasonal_comparison:
                seasonal_comparison[r[0]] = []
            seasonal_comparison[r[0]].append({"week": r[1], "cases": int(r[2])})

    all_weeks = _db_execute(f"""
        SELECT SUM(cases_total)
        FROM public.fact_core_weekly {disease_filter}
        GROUP BY epi_year, epi_week
    """, params)
    all_cases = [int(r[0]) for r in all_weeks if r[0] is not None]
    stats = {}
    if all_cases:
        stats = {
            "min_weekly": min(all_cases),
            "max_weekly": max(all_cases),
            "avg_weekly": round(statistics.mean(all_cases), 2),
            "median_weekly": round(statistics.median(all_cases), 2),
            "p75_weekly": _percentile(all_cases, 75),
            "p90_weekly": _percentile(all_cases, 90)
        }

    top_rows = _db_execute(f"""
        SELECT departamento_code, SUM(cases_total)
        FROM public.fact_core_weekly {disease_filter}
        GROUP BY departamento_code ORDER BY 2 DESC LIMIT 5
    """, params)

    return {
        "total_historical": int(total_historical),
        "data_from": str(min_date),
        "data_to": str(max_date),
        "n_weeks": n_weeks,
        "top_deptos": [(r[0], int(r[1])) for r in top_rows],
        "by_year": by_year,
        "peak_year": peak_year,
        "peak_cases": peak_cases,
        "by_disease": by_disease,
        "recent_weeks": recent,
        "seasonal_comparison": seasonal_comparison,
        "statistics": stats,
    }


def _query_region_summary(region_norm: str, disease: str | None = None) -> dict | None:
    """Casos por región (usando dim_departamentos.region_norm)."""
    disease_filter = "AND f.disease = %s" if disease else ""
    params = (region_norm, disease) if disease else (region_norm,)

    rows = _db_execute(f"""
        SELECT SUM(f.cases_total), MIN(f.week_start_date), MAX(f.week_start_date), COUNT(DISTINCT CONCAT(f.epi_year, '-', f.epi_week))
        FROM public.fact_core_weekly f
        JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
        WHERE UPPER(d.region_norm) LIKE UPPER(%s) {disease_filter}
    """, params)
    if not rows or rows[0][0] is None:
        return None
    total_historical, min_date, max_date, n_weeks = rows[0]

    year_rows = _db_execute(f"""
        SELECT f.epi_year, SUM(f.cases_total), AVG(f.cases_total), MAX(f.cases_total)
        FROM public.fact_core_weekly f
        JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
        WHERE UPPER(d.region_norm) LIKE UPPER(%s) {disease_filter}
        GROUP BY f.epi_year ORDER BY f.epi_year
    """, params)
    by_year = {}
    for r in year_rows:
        by_year[r[0]] = {
            "total": int(r[1]),
            "avg_weekly": round(float(r[2]), 2) if r[2] else 0,
            "max_weekly": int(r[3]) if r[3] else 0
        }

    peak_year = max(by_year, key=lambda y: by_year[y]["total"]) if by_year else None
    peak_cases = by_year.get(peak_year, {}).get("total", 0) if peak_year else 0

    if disease is None:
        dis_rows = _db_execute(f"""
            SELECT f.disease, SUM(f.cases_total), AVG(f.cases_total)
            FROM public.fact_core_weekly f
            JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
            WHERE UPPER(d.region_norm) LIKE UPPER(%s)
            GROUP BY f.disease ORDER BY 2 DESC
        """, (region_norm,))
        by_disease = {r[0]: {"total": int(r[1]), "avg_weekly": round(float(r[2]), 2) if r[2] else 0} for r in dis_rows}
    else:
        by_disease = {}

    recent_rows = _db_execute(f"""
        SELECT f.epi_year, f.epi_week, SUM(f.cases_total), f.week_start_date
        FROM public.fact_core_weekly f
        JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
        WHERE UPPER(d.region_norm) LIKE UPPER(%s) {disease_filter}
        GROUP BY f.epi_year, f.epi_week, f.week_start_date
        ORDER BY f.week_start_date DESC LIMIT 12
    """, params)
    recent = [{"year": r[0], "week": r[1], "cases": int(r[2]), "date": str(r[3])} for r in recent_rows]

    seasonal_comparison = {}
    if recent:
        latest_epi_week = recent[0]["week"]
        seasonal_params = list(params) 
        seasonal_params.extend([max(1, latest_epi_week - 4), latest_epi_week])
        seasonal_filter = f"AND f.epi_week BETWEEN %s AND %s"
        seasonal_rows = _db_execute(f"""
            SELECT f.epi_year, f.epi_week, SUM(f.cases_total)
            FROM public.fact_core_weekly f
            JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
            WHERE UPPER(d.region_norm) LIKE UPPER(%s) {disease_filter} {seasonal_filter}
            GROUP BY f.epi_year, f.epi_week
            ORDER BY f.epi_year DESC, f.epi_week
        """, tuple(seasonal_params))
        
        for r in seasonal_rows:
            if r[0] not in seasonal_comparison:
                seasonal_comparison[r[0]] = []
            seasonal_comparison[r[0]].append({"week": r[1], "cases": int(r[2])})

    all_weeks = _db_execute(f"""
        SELECT SUM(f.cases_total)
        FROM public.fact_core_weekly f
        JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
        WHERE UPPER(d.region_norm) LIKE UPPER(%s) {disease_filter}
        GROUP BY f.epi_year, f.epi_week
    """, params)
    all_cases = [int(r[0]) for r in all_weeks if r[0] is not None]
    stats = {}
    if all_cases:
        stats = {
            "min_weekly": min(all_cases),
            "max_weekly": max(all_cases),
            "avg_weekly": round(statistics.mean(all_cases), 2),
            "median_weekly": round(statistics.median(all_cases), 2),
            "p75_weekly": _percentile(all_cases, 75),
            "p90_weekly": _percentile(all_cases, 90)
        }

    dep_rows = _db_execute(f"""
        SELECT f.departamento_code, SUM(f.cases_total)
        FROM public.fact_core_weekly f
        JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
        WHERE UPPER(d.region_norm) LIKE UPPER(%s) {disease_filter}
        GROUP BY f.departamento_code ORDER BY 2 DESC LIMIT 5
    """, params)

    return {
        "total_historical": int(total_historical),
        "by_year": by_year,
        "peak_year": peak_year,
        "peak_cases": peak_cases,
        "by_disease": by_disease,
        "recent_weeks": recent,
        "seasonal_comparison": seasonal_comparison,
        "statistics": stats,
        "data_from": str(min_date),
        "data_to": str(max_date),
        "n_weeks": n_weeks,
        "top_deptos": [(r[0], int(r[1])) for r in dep_rows],
    }


def _percentile(values: list[int], p: float) -> float:
    """Percentil por interpolación lineal, sin depender de numpy."""
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * (p / 100)
    f, c = int(k), min(int(k) + 1, len(values) - 1)
    if f == c:
        return float(values[f])
    return round(values[f] * (c - k) + values[c] * (k - f), 1)


def _query_seasonal_projection(
    epi_week: int,
    disease: str | None,
    departamento_code: str | None,
    years_exclude: tuple[int, ...] = (2020, 2021),
) -> dict | None:
    """Canal endémico histórico para una semana epidemiológica dada.

    Misma metodología que la definición de 'brote' del proyecto (percentil
    75 del histórico de la misma semana, excluyendo años de ruido COVID).
    Sirve como proyección estacional cuando no hay modelo entrenado para
    la fecha consultada (ej. años futuros).
    """
    filters = ["epi_week = %s"]
    params: list = [epi_week]
    if disease:
        filters.append("disease = %s")
        params.append(disease)
    if departamento_code:
        filters.append("departamento_code = %s")
        params.append(departamento_code)
    if years_exclude:
        placeholders = ",".join(["%s"] * len(years_exclude))
        filters.append(f"epi_year NOT IN ({placeholders})")
        params.extend(years_exclude)

    rows = _db_execute(f"""
        SELECT epi_year, SUM(cases_total)
        FROM public.fact_core_weekly
        WHERE {" AND ".join(filters)}
        GROUP BY epi_year
        ORDER BY epi_year
    """, tuple(params))

    if not rows:
        return None

    years = [r[0] for r in rows]
    values = [int(r[1]) for r in rows]
    if len(values) < 3:
        return None  # muy pocos años como para dar un rango con sentido

    return {
        "years": years,
        "n_years": len(years),
        "p25": _percentile(values, 25),
        "p50": _percentile(values, 50),
        "p75": _percentile(values, 75),
        "p90": _percentile(values, 90),
        "mean": round(statistics.mean(values), 1),
    }


def _query_predictions(
    disease: str | None,
    departamento_code: str | None,
    municipio_code: str | None,
    epi_year: int | None = None,
    epi_week: int | None = None,
    limit: int = 4,
) -> list[dict] | None:
    """Query precomputed predictions from Supabase."""
    filters = []
    params = []
    if disease:
        filters.append("disease = %s")
        params.append(disease)
    if departamento_code:
        filters.append("departamento_code = %s")
        params.append(departamento_code)
    if municipio_code:
        filters.append("municipio_code = %s")
        params.append(municipio_code)
    if epi_year:
        filters.append("epi_year = %s")
        params.append(epi_year)
    if epi_week:
        filters.append("epi_week = %s")
        params.append(epi_week)

    rows = _db_execute(f"""
        SELECT 
            departamento_code, municipio_code, disease,
            epi_year, epi_week, week_start_date,
            predicted_cases, outbreak_flag, outbreak_threshold,
            endemic_risk, shap_top_factors
        FROM public.predictions
        WHERE {" AND ".join(filters) if filters else "1=1"}
        ORDER BY week_start_date DESC
        LIMIT %s
    """, tuple(params + [limit]))

    if not rows:
        return None

    predictions = []
    for row in rows:
        predictions.append({
            "departamento_code": row[0],
            "municipio_code": row[1],
            "disease": row[2],
            "epi_year": row[3],
            "epi_week": row[4],
            "week_start_date": row[5],
            "predicted_cases": row[6],
            "outbreak_flag": row[7],
            "outbreak_threshold": row[8],
            "endemic_risk": row[9],
            "shap_top_factors": row[10],
        })
    return predictions


# ---------------------------------------------------------------------------
# Question type detection
# ---------------------------------------------------------------------------

def _detect_intent(question: str) -> dict:
    """Detecta las intenciones de la pregunta."""
    lowered = question.lower()
    
    disease = next((d for d in VALID_DISEASES if d in lowered), None)
    
    # Detect location
    departamento_code = None
    for name in sorted(DEPTO_NAME_TO_CODE, key=len, reverse=True):
        if name in lowered:
            departamento_code = DEPTO_NAME_TO_CODE[name]
            break
    if not departamento_code:
        m = re.search(r"\b(\d{5})\b", question)
        if m:
            departamento_code = m.group(1)[:2]
        else:
            m = re.search(r"\b(\d{2})\b", question)
            if m:
                departamento_code = m.group(1)

    municipio_code = None
    m = re.search(r"\b(\d{5})\b", question)
    if m:
        municipio_code = m.group(1)

    # Detect topic
    wants_climate = any(kw in lowered for kw in CLIMATE_KEYWORDS)
    wants_national = any(kw in lowered for kw in NATIONAL_KEYWORDS) and not departamento_code
    wants_region = any(kw in lowered for kw in REGION_KEYWORDS)

    # Detect region name
    # NOTE: Using exact matches database dim_departamentos.region_norm values
    region_map = {
        "pacifico": "PACIFICO", "pacífico": "PACIFICO",
        "caribe": "CARIBE", "andina": "ANDINA", "andino": "ANDINA",
        "orinoquia": "ORINOQUIA", "orinoquía": "ORINOQUIA",
        "amazonia": "AMAZONIA", "amazonía": "AMAZONIA",
        "insular": "INSULAR",
    }
    region_norm = None
    for kw, rn in region_map.items():
        if kw in lowered:
            region_norm = rn
            break

    fecha = find_date_in_text(question)
    
    # Detect response mode
    response_mode = "current"  # Default
    
    # Check for comparison keywords first
    comparison_keywords = ["comparar", "vs", "versus", "comparación", "diferencia entre", "entre"]
    is_comparison = any(kw in lowered for kw in comparison_keywords)
    
    if is_comparison:
        response_mode = "comparison"
    else:
        # Check for forecast keywords: future, next, prediction, estimate, etc.
        forecast_keywords = ["qué pasará", "qué pasará", "qué pasa", "pronóstico", "predicción",
                            "próximas semanas", "proximas semanas", "siguientes semanas",
                            "siguiente semana", "próximo mes", "futuro", "2025", "2026", "2027"]
        is_forecast = any(kw in lowered for kw in forecast_keywords)
        if fecha and fecha.epi_year and (fecha.epi_year >= 2025):
            is_forecast = True
        if is_forecast:
            response_mode = "forecast"
        else:
            # Check if it's historical: mentions past years, "entre 20xx y 20xx", "cómo estuvo", etc.
            historical_keywords = ["entre 201", "entre 202", "cómo estuvo", "cómo estaba", "histórico", "historia",
                                  "datos de", "casos de", "en el año", "en los años", "de 20", "de 201"]
            is_historical = any(kw in lowered for kw in historical_keywords)
            if fecha and fecha.epi_year and (fecha.epi_year <= 2024):
                is_historical = True
            if is_historical:
                response_mode = "historical"
            else:
                # Check for current
                current_keywords = ["cómo está", "actual", "ahora", "últimas semanas", "actualmente"]
                if any(kw in lowered for kw in current_keywords):
                    response_mode = "current"

    return {
        "disease": disease,
        "departamento_code": departamento_code,
        "municipio_code": municipio_code,
        "wants_climate": wants_climate,
        "wants_national": wants_national,
        "wants_region": wants_region,
        "region_norm": region_norm,
        "fecha": fecha,
        "response_mode": response_mode,
    }


# ---------------------------------------------------------------------------
# Knowledge base search
# ---------------------------------------------------------------------------

def _get_friendly_source_name(internal_name: str) -> str:
    """Converts internal source names to user-friendly names."""
    friendly_map = {
        "historial_municipio": "Registro histórico municipal",
        "historial_departamento": "Registro histórico departamental",
        "clima": "Datos climáticos",
        "clima_historico_departamento": "Datos climáticos históricos",
        "clima_vivo_open_meteo": "Datos climáticos recientes (Open-Meteo)",
        "pronostico_open_meteo": "Pronóstico climático (Open-Meteo)",
        "resumen_region": "Resumen regional",
        "resumen_nacional": "Resumen nacional",
        "resumen_general": "Resumen general",
        "proyeccion_estacional_canal_endemico": "Proyección estacional (canal endémico)",
        "prediccion_modelo": "Predicción del modelo",
        "explicacion_factores": "Explicación de factores (SHAP)",
        "metodologia_prediccion": "Metodología de predicción",
        "fecha_calculada": "Fecha calculada",
        "docs": "Documentación del proyecto",
        "movilidad_municipio": "Datos de movilidad municipal",
        "conclusiones_ia": "Interpretación sugerida por IA",
        "casos_departamento": "Datos de casos departamentales"
    }
    return friendly_map.get(internal_name, internal_name)


def _search_knowledge_base(question: str, limit: int = 3) -> list[ChatSource]:
    # Try to read publication_date and source_type from metadata if available.
    rows = _db_execute("""
        SELECT metadata->>'title' as title, content,
               metadata->>'publication_date' AS publication_date,
               COALESCE(metadata->>'source_type', 'doc') AS source_type
        FROM public.knowledge_base
        WHERE to_tsvector('spanish', content) @@ plainto_tsquery('spanish', %s)
           OR content ILIKE %s
        LIMIT %s
    """, (question, f"%{question}%", limit))

    sources: list[ChatSource] = []
    for r in rows:
        title, content, pub_date, src_type = r[0], r[1] or "", (r[2] or None), (r[3] or "doc")
        excerpt = content[:500]
        friendly_title = _get_friendly_source_name(title)
        sources.append(ChatSource(title=friendly_title, excerpt=excerpt, source_type=src_type, publication_date=pub_date))
    return sources


def _document_snippets(question: str, limit: int = 3) -> list[ChatSource]:
    """Recupera fragmentos de documentos relevantes usando búsqueda semántica o textual."""
    # Intentar búsqueda semántica (vectores en Supabase) primero
    if semantic_available():
        try:
            hits = semantic_search(question, k=limit)
            if hits:
                return [ChatSource(title=_get_friendly_source_name(s), excerpt=e, source_type="doc") for s, e in hits]
        except Exception as e:
            logger.error(f"Semantic search error: {e}")

    # Fallback a búsqueda textual (TSVECTOR/ILIKE)
    db_sources = _search_knowledge_base(question, limit=limit)

    # Depriorizar automáticamente documentos de la época pandémica (2020/2021)
    # salvo que la pregunta mencione explícitamente esos años o 'covid'.
    qlow = question.lower()
    if not re.search(r"\b(2020|2021|covid)\b", qlow):
        def _is_pandemic(src: ChatSource) -> bool:
            text = (src.title or "") + " " + (src.excerpt or "")
            text = text.lower()
            return "2020" in text or "2021" in text or "covid" in text

        # Stable sort: non-pandemic first
        db_sources.sort(key=lambda s: _is_pandemic(s))

    return db_sources


# ---------------------------------------------------------------------------
# Answer builder
# ---------------------------------------------------------------------------

def _build_answer(question: str, intent: dict) -> tuple[str, list[ChatSource]]:
    sources = _document_snippets(question)
    parts: list[str] = []

    fecha = intent.get("fecha")
    disease = intent["disease"]
    depto = intent["departamento_code"]
    muni = intent["municipio_code"]

    # First, try to get precomputed predictions
    predictions = None
    if fecha or disease or depto or muni:
        predictions = _query_predictions(
            disease=disease,
            departamento_code=depto,
            municipio_code=muni,
            epi_year=fecha.epi_year if fecha else None,
            epi_week=fecha.epi_week if fecha else None,
            limit=4,
        )

    # If no precomputed predictions and we have municipio+disease, try to generate predictions on the fly
    if not predictions and PREDICT_AVAILABLE and muni and disease:
        try:
            # Try to generate predictions
            generated_preds = predict_cases(muni, disease, weeks_ahead=4)
            predictions = []
            for pred in generated_preds:
                predictions.append({
                    "departamento_code": pred.get("departamento_code", depto),
                    "municipio_code": pred.get("municipio_code", muni),
                    "disease": pred.get("disease", disease),
                    "epi_year": pred.get("epi_year"),
                    "epi_week": pred.get("epi_week"),
                    "week_start_date": pred.get("week_start_date"),
                    "predicted_cases": pred.get("predicted_cases"),
                    "outbreak_flag": pred.get("outbreak_flag", False),
                    "outbreak_threshold": pred.get("outbreak_threshold", 5.0),
                    "endemic_risk": pred.get("endemic_risk", "moderado"),
                    "shap_top_factors": pred.get("shap_values"),
                })
        except Exception as e:
            logger.error(f"Error generating predictions on the fly: {e}")
            predictions = None

    if predictions:
        # Disclaimer about data sources (more human, no variable names)
        disclaimer = (
            "⚠️ Nota importante: Las predicciones se basan en información de diversas fuentes verificadas, "
            "como datos históricos de salud, clima, tendencias de búsqueda, noticias relevantes, "
            "movilidad de personas y coberturas de vacunación. Usamos un modelo híbrido Prophet + XGBoost "
            "para generarlas, y SHAP (SHapley Additive exPlanations) para identificar y explicar qué factores "
            "influyen más en cada estimación. Esta es una proyección basada en datos históricos y no una certeza."
        )
        parts.append(disclaimer)
        sources.append(ChatSource(
            title=_get_friendly_source_name("metodologia_prediccion"),
            excerpt=disclaimer,
            source_type="data",
        ))

        for pred in predictions:
            location = pred['departamento_code'] or 'Colombia'
            outbreak_status = "hay señales de brote" if pred['outbreak_flag'] else "no hay señales de brote"
            pred_text = (
                f"Para {pred['disease']} en {location}, el modelo estima alrededor de {round(pred['predicted_cases'], 1)} casos "
                f"para la semana epidemiológica {pred['epi_week']}/{pred['epi_year']}. "
                f"El nivel de riesgo endémico se clasifica como {pred['endemic_risk']}, y actualmente {outbreak_status}. "
                f"El umbral de brote establecido para este contexto es de {pred['outbreak_threshold']} casos/semana."
            )
            parts.append(pred_text)
            sources.append(ChatSource(
                title=_get_friendly_source_name("prediccion_modelo"),
                excerpt=pred_text,
                source_type="data",
            ))
            if pred["shap_top_factors"]:
                # Make SHAP factors more human-readable and detailed
                readable_factors = []
                # Sort SHAP factors by absolute value to get most important first
                sorted_shap = sorted(pred["shap_top_factors"].items(), key=lambda x: abs(x[1]), reverse=True)[:5]
                for factor, value in sorted_shap:
                    # Map internal variable names to friendly names
                    friendly_name = {
                        'temp_avg_c': 'temperatura promedio',
                        'temp_min_c': 'temperatura mínima',
                        'temp_max_c': 'temperatura máxima',
                        'precipitation_mm': 'precipitación',
                        'mobility_in': 'flujo de personas entrantes',
                        'mobility_out': 'flujo de personas salientes',
                        'mobility_index': 'índice de movilidad',
                        'trends_score': 'interés en búsqueda (Google Trends)',
                        'rss_mentions': 'menciones en noticias',
                        'signals_score': 'señales tempranas',
                        'vaccination_coverage_pct': 'cobertura de vacunación',
                        'rips_visits_total': 'atenciones médicas (RIPS)',
                        'cases_lag_1': 'casos de la semana pasada',
                        'cases_lag_2': 'casos de hace dos semanas',
                        'cases_lag_4': 'casos de hace cuatro semanas',
                        'epi_year': 'año epidemiológico',
                        'epi_week': 'semana epidemiológica',
                    }.get(factor, factor)
                    
                    abs_value = abs(value)
                    direction = "aumenta" if value > 0 else "disminuye"
                    impact = "alto" if abs_value > 0.5 else "moderado" if abs_value > 0.2 else "bajo"
                    readable_factors.append(f"{friendly_name} ({direction} el riesgo con impacto {impact})")
                
                if readable_factors:
                    shap_text = "Factores que influyen en la predicción (ordenados por relevancia, usando valores SHAP): " + "; ".join(readable_factors) + "."
                    parts.append(shap_text)
                    sources.append(ChatSource(
                        title=_get_friendly_source_name("explicacion_factores"),
                        excerpt=shap_text,
                        source_type="data",
                    ))
    elif fecha is not None:
        parts.append(fecha.as_context_line())
        sources.append(ChatSource(
            title=_get_friendly_source_name("fecha_calculada"),
            excerpt=fecha.as_context_line(),
            source_type="data",
        ))

        seasonal = _query_seasonal_projection(fecha.epi_week, disease, depto)
        if seasonal:
            ambito = f"departamento {depto}" if depto else "Colombia (nacional)"
            enf = disease if disease else "todas las enfermedades"
            proj_text = (
                f"Proyección estacional para la semana epidemiológica {fecha.epi_week:02d} "
                f"({fecha.week_start_date.isoformat()} a {fecha.week_end_date.isoformat()}) en {ambito}, "
                f"{enf} — basada en {seasonal['n_years']} años históricos "
                f"({', '.join(str(y) for y in seasonal['years'])}, excluyendo 2020-2021 por ruido COVID): "
                f"mediana histórica {seasonal['p50']} casos; "
                f"canal endémico normal entre {seasonal['p25']} (p25) y {seasonal['p75']} (p75) casos; "
                f"por encima de {seasonal['p75']} se consideraría brote según la metodología del proyecto; "
                f"por encima de {seasonal['p90']} (p90) se consideraría epidemia."
            )
            parts.append(proj_text)
            sources.append(ChatSource(
                title=_get_friendly_source_name("proyeccion_estacional_canal_endemico"),
                excerpt=proj_text,
                source_type="data",
            ))
            parts.append(
                "Nota: esto es una proyección estadística basada en el patrón histórico de esa "
                "semana del año (canal endémico), no una salida del modelo Prophet+XGBoost — ese "
                "modelo necesita variables exógenas (clima, movilidad, Trends) que no existen para "
                "fechas tan lejanas en el futuro. Interprétese como un rango de referencia, no como "
                "una cifra puntual predicha."
            )
        else:
            parts.append(
                f"No hay suficiente historial para construir una proyección estacional confiable "
                f"para la semana epidemiológica {fecha.epi_week:02d}"
                + (f" en el departamento {depto}" if depto else "")
                + (f" para {disease}" if disease else "") + "."
            )



    # ── 1. Municipio + enfermedad → histórico local + movilidad + conclusiones ──────────────────────────
    if muni and disease:
        try:
            history = get_history(muni, disease, limit=8)
            mobility = get_mobility(muni, limit=4)
        except FileNotFoundError:
            history = None
            mobility = pd.DataFrame()
        
        if history is not None and not history.empty:
            latest = history.iloc[0]
            recent = history.head(4)["cases_total"].tolist()
            trend = ("ascendente" if recent[0] > recent[-1]
                     else "descendente" if recent[0] < recent[-1] else "estable")
            
            # Historical cases info
            parts.append(
                f"Municipio {muni} | {disease}: {int(latest['cases_total'])} casos en la última semana "
                f"(tendencia {trend}). Últimas 4 semanas: {recent}."
            )
            sources.append(ChatSource(
                title=_get_friendly_source_name("historial_municipio"),
                excerpt=f"{muni}/{disease}: última semana {int(latest['cases_total'])} casos, tendencia {trend}.",
                source_type="data",
            ))
            
            # Mobility info if available
            if not mobility.empty:
                latest_mob = mobility.iloc[0]
                mob_in = int(latest_mob.get('mobility_in', 0))
                mob_out = int(latest_mob.get('mobility_out', 0))
                mob_index = round(latest_mob.get('mobility_index', 0), 1)
                mob_text = (
                    f"En la última semana registrada, hubo alrededor de {mob_in} personas que llegaron a {muni} y {mob_out} que salieron. "
                    f"El índice de movilidad para la localidad es de {mob_index}."
                )
                parts.append(mob_text)
                sources.append(ChatSource(
                    title=_get_friendly_source_name("movilidad_municipio"),
                    excerpt=mob_text,
                    source_type="data",
                ))
                
                # AI-generated conclusions with disclaimer (more human)
                concl_text = (
                    "🤖 Interpretación sugerida por IA basada en datos de ECOS (esto es solo una guía, no reemplaza el juicio de un profesional): "
                )
                if trend == "ascendente" and latest_mob.get("mobility_in", 0) > 100:
                    concl_text += (
                        "Como la cantidad de casos está aumentando y hay bastante movimiento de personas entrando al municipio, "
                        "podría haber un riesgo de que los casos sigan creciendo en las próximas semanas. Sería buena idea intensificar las medidas de vigilancia."
                    )
                elif trend == "descendente":
                    concl_text += (
                        "¡Bueno! La cantidad de casos está bajando, lo cual es una señal positiva. Sería bueno seguir con las medidas de prevención para mantener esta tendencia."
                    )
                else:
                    concl_text += "La situación se ve estable por ahora. Es bueno seguir con la vigilancia normal para mantenerla así."
                
                parts.append(concl_text)
                sources.append(ChatSource(
                    title=_get_friendly_source_name("conclusiones_ia"),
                    excerpt=concl_text,
                    source_type="data",
                ))
        
        return " ".join(parts) or "No se encontraron datos para ese municipio.", sources

    # ── 2. Clima por departamento (incluye datos en vivo de Open-Meteo) ────────────────────────────────────────────
    if intent["wants_climate"] and depto:
        # First try to get historical data from our DB
        climate = _query_climate_by_depto(depto)
        
        # Try to get live Open-Meteo data
        dept_coords = _load_departamento_coords()
        live_weather = None
        if depto in dept_coords:
            lat, lon = dept_coords[depto]
            try:
                today = dt.date.today()
                start_date = (today - dt.timedelta(days=7)).isoformat()
                end_date = (today + dt.timedelta(days=14)).isoformat()
                live_weather = fetch_open_meteo_weekly(lat, lon, start_date, end_date)
            except Exception as e:
                logger.error(f"Error fetching live Open-Meteo data for {depto}: {e}")
        
        # Build climate info
        if climate or live_weather:
            if climate:
                parts.append(
                    f"Datos históricos del clima en el departamento {depto} "
                    f"(período {climate['data_from']} – {climate['data_to']}): "
                    f"La temperatura promedio es de {climate['avg_temp']}°C "
                    f"(mínima {climate['min_temp']}°C, máxima {climate['max_temp']}°C). "
                    f"La precipitación promedio es de {climate['avg_precip']} mm "
                    f"(el máximo registrado es {climate['max_precip']} mm)."
                )
                sources.append(ChatSource(
                    title=_get_friendly_source_name("clima_historico_departamento"),
                    excerpt=f"Depto {depto} (histórico): temp promedio {climate['avg_temp']}°C, precip promedio {climate['avg_precip']}mm.",
                    source_type="data",
                ))
            
            if live_weather and len(live_weather) > 0:
                latest = live_weather[-1]
                forecast = live_weather[0] if len(live_weather) > 1 else None
                live_parts = []
                live_parts.append(f"Datos del clima recientes para la semana de {latest.week_start_date} (de Open-Meteo): ")
                if latest.temperature_2m_mean:
                    live_parts.append(f"La temperatura promedio fue de {round(latest.temperature_2m_mean, 1)}°C")
                if latest.temperature_2m_min and latest.temperature_2m_max:
                    live_parts.append(f"con mínimas de {round(latest.temperature_2m_min, 1)}°C y máximas de {round(latest.temperature_2m_max, 1)}°C")
                if latest.precipitation_sum:
                    live_parts.append(f"Hubo {round(latest.precipitation_sum, 1)} mm de lluvia")
                if latest.relative_humidity_2m_mean:
                    live_parts.append(f"y la humedad relativa promedio fue del {round(latest.relative_humidity_2m_mean, 1)}%")
                
                live_text = " ".join(live_parts) + "."
                parts.append(live_text)
                sources.append(ChatSource(
                    title=_get_friendly_source_name("clima_vivo_open_meteo"),
                    excerpt=f"Depto {depto} (Open-Meteo): {live_text}",
                    source_type="data",
                ))
                
                if forecast:
                    forecast_parts = []
                    forecast_parts.append(f"Para la próxima semana ({forecast.week_start_date}), el pronóstico es: ")
                    if forecast.temperature_2m_mean:
                        forecast_parts.append(f"Temperatura promedio esperada: {round(forecast.temperature_2m_mean, 1)}°C")
                    if forecast.precipitation_sum:
                        forecast_parts.append(f"Precipitación esperada: {round(forecast.precipitation_sum, 1)} mm")
                    forecast_text = " ".join(forecast_parts) + "."
                    parts.append(forecast_text)
                    sources.append(ChatSource(
                        title=_get_friendly_source_name("pronostico_open_meteo"),
                        excerpt=f"Depto {depto} (pronóstico Open-Meteo): {forecast_text}",
                        source_type="data",
                    ))
        
        else:
            parts.append(f"No se encontraron datos climáticos para el departamento {depto}.")
        
        # Si también pregunta por casos junto al clima, añadirlos
        if disease:
            cases = _query_cases_by_depto(depto, disease)
            if cases:
                parts.append(
                    f"Adicionalmente, para {disease} en ese departamento: "
                    f"{cases['total_historical']} casos totales históricos."
                )
        return " ".join(parts), sources[:5]

    # ── 3. Departamento (con o sin enfermedad) ───────────────────────────────
    if depto:
        # Siempre incluir clima si hay datos
        climate = _query_climate_by_depto(depto)
        if climate and intent["wants_climate"]:
            parts.append(
                f"Clima depto {depto}: T°prom {climate['avg_temp']}°C, "
                f"precipitación prom {climate['avg_precip']} mm."
            )
            sources.append(ChatSource(
                title=_get_friendly_source_name("clima"),
                excerpt=f"T°={climate['avg_temp']}°C, Precip={climate['avg_precip']}mm.",
                source_type="data",
            ))

        cases = _query_cases_by_depto(depto, disease)
        if cases:
            # Construir desglose anual detallado
            year_list = sorted(cases["by_year"].items())
            year_str = ", ".join(
                f"{y}: {data['total']} casos (prom {data['avg_weekly']}/sem, máx {data['max_weekly']})"
                for y, data in year_list
            )
            
            dis_str = ""
            if cases["by_disease"]:
                dis_str = " Por enfermedad: " + ", ".join(
                    f"{d}: {data['total']} (prom {data['avg_weekly']}/sem)"
                    for d, data in cases["by_disease"].items()
                ) + "."
            
            # Construir resumen de últimas semanas
            recent_reversed = list(reversed(cases["recent_weeks"]))  # Orden cronológico
            recent_trend = ""
            if len(recent_reversed) >= 2:
                first_cases = recent_reversed[0]["cases"]
                last_cases = recent_reversed[-1]["cases"]
                if last_cases > first_cases:
                    pct_change = ((last_cases - first_cases) / first_cases * 100) if first_cases > 0 else 100
                    recent_trend = f" (tendencia ascendente: +{round(pct_change, 1)}%)"
                elif last_cases < first_cases:
                    pct_change = ((first_cases - last_cases) / first_cases * 100) if first_cases > 0 else 100
                    recent_trend = f" (tendencia descendente: -{round(pct_change, 1)}%)"
                else:
                    recent_trend = " (tendencia estable)"
            
            recent_str = ", ".join(
                f"Sem {w['week']}/{w['year']}: {w['cases']}" for w in cases["recent_weeks"]
            )
            
            # Añadir estadísticas
            stats_str = ""
            if cases.get("statistics"):
                stats = cases["statistics"]
                stats_str = (
                    f" Estadísticas históricas: promedio {stats['avg_weekly']} casos/sem, "
                    f"mediana {stats['median_weekly']}, mínimo {stats['min_weekly']}, máximo {stats['max_weekly']}. "
                    f"Percentil 75: {stats['p75_weekly']}, percentil 90: {stats['p90_weekly']}."
                )
            
            # Añadir comparación estacional
            seasonal_str = ""
            if cases.get("seasonal_comparison"):
                seasonal_parts = []
                for year, weeks in sorted(cases["seasonal_comparison"].items(), reverse=True):
                    weeks_str = ", ".join(f"S{w['week']}:{w['cases']}" for w in sorted(weeks, key=lambda x: x["week"]))
                    seasonal_parts.append(f"{year}: {weeks_str}")
                if seasonal_parts:
                    seasonal_str = f" Comparación estacional (mismas semanas): {'; '.join(seasonal_parts)}."
            
            label = disease if disease else "todas las enfermedades"
            parts.append(
                f"Departamento {depto} | {label} "
                f"(datos {cases['data_from']} → {cases['data_to']}, {cases['n_weeks']} semanas): "
                f"TOTAL ACUMULADO: {cases['total_historical']} casos."
                f"{dis_str}"
                f" Desglose anual: {year_str}."
                f" Año pico: {cases['peak_year']} ({cases['peak_cases']} casos)."
                f" Últimas 12 semanas: {recent_str}{recent_trend}."
                f"{stats_str}"
                f"{seasonal_str}"
            )
            sources.append(ChatSource(
                title=_get_friendly_source_name("casos_departamento"),
                excerpt=f"Depto {depto} | {label}: {cases['total_historical']} casos totales. Pico {cases['peak_year']}.",
                source_type="data",
            ))
        elif climate:
            pass  # ya añadimos clima arriba
        else:
            parts.append(f"No se encontraron datos para el departamento {depto}.")
        return " ".join(parts) or "Sin datos.", sources[:5]

    # ── 4. Región ────────────────────────────────────────────────────────────
    if intent["wants_region"] and intent["region_norm"]:
        rdata = _query_region_summary(intent["region_norm"], disease)
        if rdata:
            year_list = sorted(rdata["by_year"].items())
            year_str = ", ".join(
                f"{y}: {data['total']} casos (prom {data['avg_weekly']}/sem, máx {data['max_weekly']})"
                for y, data in year_list
            )
            
            dis_str = ""
            if rdata["by_disease"]:
                dis_str = " Por enfermedad: " + ", ".join(
                    f"{d}: {data['total']} (prom {data['avg_weekly']}/sem)"
                    for d, data in rdata["by_disease"].items()
                ) + "."
            
            recent_reversed = list(reversed(rdata["recent_weeks"])) 
            recent_trend = ""
            if len(recent_reversed) >= 2:
                first_cases = recent_reversed[0]["cases"]
                last_cases = recent_reversed[-1]["cases"]
                if last_cases > first_cases:
                    pct_change = ((last_cases - first_cases) / first_cases * 100) if first_cases > 0 else 100
                    recent_trend = f" (tendencia ascendente: +{round(pct_change, 1)}%)"
                elif last_cases < first_cases:
                    pct_change = ((first_cases - last_cases) / first_cases * 100) if first_cases > 0 else 100
                    recent_trend = f" (tendencia descendente: -{round(pct_change, 1)}%)"
                else:
                    recent_trend = " (tendencia estable)"
            
            recent_str = ", ".join(
                f"S{w['week']}/{w['year']}: {w['cases']}" for w in rdata["recent_weeks"]
            )
            
            stats_str = ""
            if rdata.get("statistics"):
                stats = rdata["statistics"]
                stats_str = (
                    f" Estadísticas históricas: promedio {stats['avg_weekly']} casos/sem, "
                    f"mediana {stats['median_weekly']}, mínimo {stats['min_weekly']}, máximo {stats['max_weekly']}. "
                    f"Percentil 75: {stats['p75_weekly']}, percentil 90: {stats['p90_weekly']}."
                )
            
            seasonal_str = ""
            if rdata.get("seasonal_comparison"):
                seasonal_parts = []
                for year, weeks in sorted(rdata["seasonal_comparison"].items(), reverse=True):
                    weeks_str = ", ".join(f"S{w['week']}:{w['cases']}" for w in sorted(weeks, key=lambda x: x["week"]))
                    seasonal_parts.append(f"{year}: {weeks_str}")
                if seasonal_parts:
                    seasonal_str = f" Comparación estacional (mismas semanas): {'; '.join(seasonal_parts)}."
            
            top_str = ", ".join(f"depto {d}: {c}" for d, c in rdata["top_deptos"])
            label = disease if disease else "todas las enfermedades"
            parts.append(
                f"Región {intent['region_norm']} | {label} "
                f"(datos {rdata['data_from']} → {rdata['data_to']}, {rdata['n_weeks']} semanas): "
                f"TOTAL ACUMULADO: {rdata['total_historical']} casos."
                f"{dis_str}"
                f" Desglose anual: {year_str}."
                f" Año pico: {rdata['peak_year']} ({rdata['peak_cases']} casos)."
                f" Últimas 12 semanas: {recent_str}{recent_trend}."
                f"{stats_str}"
                f"{seasonal_str}"
                f" Top departamentos: {top_str}."
            )
            sources.append(ChatSource(
                title=_get_friendly_source_name("resumen_region"),
                excerpt=f"Región {intent['region_norm']} | {label}: {rdata['total_historical']} casos totales. Pico {rdata['peak_year']}.",
                source_type="data",
            ))
        else:
            parts.append(f"No se encontraron datos para la región {intent['region_norm']}.")
        return " ".join(parts) or "Sin datos para esa región.", sources[:5]

    # ── 5. Nacional (total Colombia o por enfermedad) ────────────────────────
    if intent["wants_national"] or (disease and not depto and not muni):
        nat = _query_national_summary(disease)
        if nat:
            year_list = sorted(nat["by_year"].items())
            year_str = ", ".join(
                f"{y}: {data['total']} casos (prom {data['avg_weekly']}/sem, máx {data['max_weekly']})"
                for y, data in year_list
            )
            
            dis_str = ""
            if nat["by_disease"]:
                dis_str = " Por enfermedad: " + ", ".join(
                    f"{d}: {data['total']} (prom {data['avg_weekly']}/sem)"
                    for d, data in nat["by_disease"].items()
                ) + "."
            
            recent_reversed = list(reversed(nat["recent_weeks"])) 
            recent_trend = ""
            if len(recent_reversed) >= 2:
                first_cases = recent_reversed[0]["cases"]
                last_cases = recent_reversed[-1]["cases"]
                if last_cases > first_cases:
                    pct_change = ((last_cases - first_cases) / first_cases * 100) if first_cases > 0 else 100
                    recent_trend = f" (tendencia ascendente: +{round(pct_change, 1)}%)"
                elif last_cases < first_cases:
                    pct_change = ((first_cases - last_cases) / first_cases * 100) if first_cases > 0 else 100
                    recent_trend = f" (tendencia descendente: -{round(pct_change, 1)}%)"
                else:
                    recent_trend = " (tendencia estable)"
            
            recent_str = ", ".join(
                f"S{w['week']}/{w['year']}: {w['cases']}" for w in nat["recent_weeks"]
            )
            
            stats_str = ""
            if nat.get("statistics"):
                stats = nat["statistics"]
                stats_str = (
                    f" Estadísticas históricas: promedio {stats['avg_weekly']} casos/sem, "
                    f"mediana {stats['median_weekly']}, mínimo {stats['min_weekly']}, máximo {stats['max_weekly']}. "
                    f"Percentil 75: {stats['p75_weekly']}, percentil 90: {stats['p90_weekly']}."
                )
            
            seasonal_str = ""
            if nat.get("seasonal_comparison"):
                seasonal_parts = []
                for year, weeks in sorted(nat["seasonal_comparison"].items(), reverse=True):
                    weeks_str = ", ".join(f"S{w['week']}:{w['cases']}" for w in sorted(weeks, key=lambda x: x["week"]))
                    seasonal_parts.append(f"{year}: {weeks_str}")
                if seasonal_parts:
                    seasonal_str = f" Comparación estacional (mismas semanas): {'; '.join(seasonal_parts)}."
            
            top_str = ", ".join(f"depto {d}: {c}" for d, c in nat["top_deptos"])
            label = disease if disease else "todas las enfermedades"
            parts.append(
                f"Colombia | {label} "
                f"(datos {nat['data_from']} → {nat['data_to']}, {nat['n_weeks']} semanas): "
                f"TOTAL NACIONAL: {nat['total_historical']} casos."
                f"{dis_str}"
                f" Desglose anual: {year_str}."
                f" Año pico: {nat['peak_year']} ({nat['peak_cases']} casos)."
                f" Últimas 12 semanas: {recent_str}{recent_trend}."
                f"{stats_str}"
                f"{seasonal_str}"
                f" Top 5 departamentos más afectados: {top_str}."
            )
            sources.append(ChatSource(
                title=_get_friendly_source_name("resumen_nacional"),
                excerpt=f"Colombia | {label}: {nat['total_historical']} casos totales. Período {nat['data_from']} → {nat['data_to']}.",
                source_type="data",
            ))
        return " ".join(parts) or "Sin datos nacionales.", sources[:5]

    # ── 6. Fallback general ───────────────────────────────────────────────────
    nat = _query_national_summary()
    if nat:
        year_list = sorted(nat["by_year"].items())
        year_str = ", ".join(
            f"{y}: {data['total']} casos (prom {data['avg_weekly']}/sem, máx {data['max_weekly']})"
            for y, data in year_list
        )
        
        dis_str = ""
        if nat["by_disease"]:
            dis_str = " Por enfermedad: " + ", ".join(
                f"{d}: {data['total']} (prom {data['avg_weekly']}/sem)"
                for d, data in nat["by_disease"].items()
            ) + "."
        
        parts.append(
            f"Resumen general de la base de datos ECOS: "
            f"{nat['total_historical']} casos totales en Colombia "
            f"(datos {nat['data_from']} → {nat['data_to']}, {nat['n_weeks']} semanas). "
            f"{dis_str}"
            f" Desglose anual: {year_str}."
            f" Año pico: {nat['peak_year']} ({nat['peak_cases']} casos)."
            f" Para una respuesta más específica, menciona departamento, región o enfermedad."
        )
        sources.append(ChatSource(
            title=_get_friendly_source_name("resumen_general"),
            excerpt=f"Total Colombia: {nat['total_historical']} casos. Período {nat['data_from']} → {nat['data_to']}.",
            source_type="data",
        ))

    if not sources:
        sources.append(ChatSource(
            title=_get_friendly_source_name("docs"),
            excerpt="Sistema ECOS: vigilancia epidemiológica de dengue, malaria, zika, chikungunya en Colombia.",
            source_type="doc",
        ))

    return " ".join(parts) if parts else "Consulta el sistema ECOS para datos epidemiológicos de Colombia.", sources[:5]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse, summary="Asistente conversacional ECOS")
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="question is required")

    # Generate or use provided session ID
    session_id = req.session_id or str(uuid.uuid4())

    # Get chat history from cache
    chat_history = chat_history_cache.get(session_id, [])

    intent = _detect_intent(req.question)

    # Override intent with explicit request params if provided
    if req.disease:
        if req.disease not in VALID_DISEASES:
            raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")
        intent["disease"] = req.disease
    if req.municipio_code:
        intent["municipio_code"] = req.municipio_code
    if req.departamento_code:
        intent["departamento_code"] = req.departamento_code

    answer, sources = _build_answer(req.question, intent)
    answer = rag.generate_answer(req.question, sources, fallback=answer, response_mode=intent["response_mode"], chat_history=chat_history)

    # Save current conversation to cache
    chat_history.append({"role": "user", "content": req.question})
    chat_history.append({"role": "assistant", "content": answer})
    # Keep only last 10 messages to avoid huge context
    chat_history = chat_history[-10:]
    chat_history_cache[session_id] = chat_history

    logger.info(
        "Chat: disease=%s depto=%s muni=%s climate=%s national=%s session=%s",
        intent["disease"], intent["departamento_code"],
        intent["municipio_code"], intent["wants_climate"], intent["wants_national"],
        session_id,
    )
    return ChatResponse(
        answer=answer,
        sources=sources,
        disease=intent["disease"],
        municipio_code=intent["municipio_code"],
        departamento_code=intent["departamento_code"],
        session_id=session_id,
    )


# Add a new schema for clear chat request
class ClearChatRequest(BaseModel):
    session_id: str


@router.post("/chat/clear", summary="Borrar historial de chat")
def clear_chat(req: ClearChatRequest):
    if req.session_id in chat_history_cache:
        del chat_history_cache[req.session_id]
        logger.info(f"Cleared chat history for session {req.session_id}")
        return {"status": "ok", "message": "Historial de chat borrado"}
    else:
        logger.warning(f"No chat history found for session {req.session_id}")
        return {"status": "ok", "message": "No hay historial para borrar"}
