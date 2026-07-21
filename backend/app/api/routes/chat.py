import logging
import re
import statistics
import datetime as dt
from pathlib import Path

from fastapi import APIRouter, HTTPException

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
        SELECT epi_year, SUM(cases_total)
        FROM public.fact_core_weekly
        WHERE departamento_code = %s {disease_filter}
        GROUP BY epi_year ORDER BY epi_year
    """, params)
    by_year = {r[0]: int(r[1]) for r in year_rows}
    peak_year = max(by_year, key=by_year.get) if by_year else None

    if disease is None:
        dis_rows = _db_execute("""
            SELECT disease, SUM(cases_total)
            FROM public.fact_core_weekly
            WHERE departamento_code = %s
            GROUP BY disease ORDER BY 2 DESC
        """, (departamento_code,))
        by_disease = {r[0]: int(r[1]) for r in dis_rows}
    else:
        by_disease = {}

    recent_rows = _db_execute(f"""
        SELECT epi_year, epi_week, SUM(cases_total)
        FROM public.fact_core_weekly
        WHERE departamento_code = %s {disease_filter}
        GROUP BY epi_year, epi_week
        ORDER BY epi_year DESC, epi_week DESC LIMIT 4
    """, params)
    recent = [{"year": r[0], "week": r[1], "cases": int(r[2])} for r in recent_rows]

    return {
        "total_historical": int(total_hist),
        "by_year": by_year,
        "by_disease": by_disease,
        "peak_year": peak_year,
        "peak_cases": by_year.get(peak_year, 0),
        "recent_weeks": recent,
        "data_from": str(min_date),
        "data_to": str(max_date),
        "n_weeks": n_weeks,
    }


def _query_national_summary(disease: str | None = None) -> dict | None:
    """Total de casos a nivel nacional."""
    disease_filter = "WHERE disease = %s" if disease else ""
    params = (disease,) if disease else ()

    rows = _db_execute(f"""
        SELECT SUM(cases_total), MIN(week_start_date), MAX(week_start_date)
        FROM public.fact_core_weekly {disease_filter}
    """, params)
    if not rows or rows[0][0] is None:
        return None
    total, min_d, max_d = rows[0]

    top_rows = _db_execute(f"""
        SELECT departamento_code, SUM(cases_total)
        FROM public.fact_core_weekly {disease_filter}
        GROUP BY departamento_code ORDER BY 2 DESC LIMIT 5
    """, params)

    year_rows = _db_execute(f"""
        SELECT epi_year, SUM(cases_total)
        FROM public.fact_core_weekly {disease_filter}
        GROUP BY epi_year ORDER BY epi_year
    """, params)
    by_year = {r[0]: int(r[1]) for r in year_rows}

    if not disease:
        dis_rows = _db_execute("""
            SELECT disease, SUM(cases_total)
            FROM public.fact_core_weekly
            GROUP BY disease ORDER BY 2 DESC
        """)
        by_disease = {r[0]: int(r[1]) for r in dis_rows}
    else:
        by_disease = {}

    return {
        "total": int(total),
        "data_from": str(min_d),
        "data_to": str(max_d),
        "top_deptos": [(r[0], int(r[1])) for r in top_rows],
        "by_year": by_year,
        "by_disease": by_disease,
    }


def _query_region_summary(region_norm: str, disease: str | None = None) -> dict | None:
    """Casos por región (usando dim_departamentos.region_norm)."""
    disease_filter = "AND f.disease = %s" if disease else ""
    params = (region_norm, disease) if disease else (region_norm,)

    rows = _db_execute(f"""
        SELECT SUM(f.cases_total), MIN(f.week_start_date), MAX(f.week_start_date)
        FROM public.fact_core_weekly f
        JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
        WHERE UPPER(d.region_norm) LIKE UPPER(%s) {disease_filter}
    """, params)
    if not rows or rows[0][0] is None:
        return None
    total, min_d, max_d = rows[0]

    dep_rows = _db_execute(f"""
        SELECT f.departamento_code, SUM(f.cases_total)
        FROM public.fact_core_weekly f
        JOIN public.dim_departamentos d ON f.departamento_code = d.departamento_code
        WHERE UPPER(d.region_norm) LIKE UPPER(%s) {disease_filter}
        GROUP BY f.departamento_code ORDER BY 2 DESC LIMIT 5
    """, params)

    return {
        "total": int(total),
        "data_from": str(min_d),
        "data_to": str(max_d),
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
    region_map = {
        "pacifico": "PACÍFICO", "pacífico": "PACÍFICO",
        "caribe": "CARIBE", "andina": "ANDINA", "andino": "ANDINA",
        "orinoquia": "ORINOQUÍA", "orinoquía": "ORINOQUÍA",
        "amazonia": "AMAZONÍA", "amazonía": "AMAZONÍA",
        "insular": "INSULAR",
    }
    region_norm = None
    for kw, rn in region_map.items():
        if kw in lowered:
            region_norm = rn
            break

    fecha = find_date_in_text(question)

    return {
        "disease": disease,
        "departamento_code": departamento_code,
        "municipio_code": municipio_code,
        "wants_climate": wants_climate,
        "wants_national": wants_national,
        "wants_region": wants_region,
        "region_norm": region_norm,
        "fecha": fecha,
    }


# ---------------------------------------------------------------------------
# Knowledge base search
# ---------------------------------------------------------------------------

def _search_knowledge_base(question: str, limit: int = 3) -> list[ChatSource]:
    # Try to read publication_date and source_type if available in the table.
    rows = _db_execute("""
        SELECT title, content,
               COALESCE(publication_date::text, '') AS publication_date,
               COALESCE(source_type, 'doc') AS source_type
        FROM public.knowledge_base
        WHERE to_tsvector('spanish', content) @@ plainto_tsquery('spanish', %s)
           OR content ILIKE %s
        LIMIT %s
    """, (question, f"%{question}%", limit))

    sources: list[ChatSource] = []
    for r in rows:
        title, content, pub_date, src_type = r[0], r[1] or "", (r[2] or None), (r[3] or "doc")
        excerpt = content[:500]
        sources.append(ChatSource(title=title, excerpt=excerpt, source_type=src_type, publication_date=pub_date))
    return sources


def _document_snippets(question: str, limit: int = 3) -> list[ChatSource]:
    """Recupera fragmentos de documentos relevantes usando búsqueda semántica o textual."""
    # Intentar búsqueda semántica (vectores en Supabase) primero
    if semantic_available():
        try:
            hits = semantic_search(question, k=limit)
            if hits:
                return [ChatSource(title=s, excerpt=e, source_type="doc") for s, e in hits]
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

    if predictions:
        # Disclaimer about data sources (more human, no variable names)
        disclaimer = (
            "⚠️ Nota importante: Las predicciones se basan en información de diversas fuentes verificadas, "
            "como datos históricos de salud, clima, tendencias de búsqueda, noticias relevantes, "
            "movilidad de personas y coberturas de vacunación. Usamos un modelo combinado de Prophet y XGBoost "
            "para generarlas, y SHAP para entender qué factores influyen más."
        )
        parts.append(disclaimer)
        sources.append(ChatSource(
            title="metodologia_prediccion",
            excerpt=disclaimer,
            source_type="data",
        ))

        for pred in predictions:
            location = pred['departamento_code'] or 'Colombia'
            pred_text = (
                f"Para {pred['disease']} en {location}, estimamos alrededor de {round(pred['predicted_cases'], 1)} casos para la semana {pred['epi_week']}/{pred['epi_year']}. "
                f"El nivel de riesgo endémico es {pred['endemic_risk']}, y {'sí hay' if pred['outbreak_flag'] else 'no hay'} señal de brote."
            )
            parts.append(pred_text)
            sources.append(ChatSource(
                title="prediccion_modelo",
                excerpt=pred_text,
                source_type="data",
            ))
            if pred["shap_top_factors"]:
                # Make SHAP factors more human-readable
                readable_factors = []
                for factor, value in pred["shap_top_factors"].items():
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
                    
                    direction = "aumenta" if value > 0 else "disminuye"
                    readable_factors.append(f"{friendly_name} ({direction} el riesgo)")
                
                shap_text = "Los factores que más influyen en esta estimación son: " + ", ".join(readable_factors) + "."
                parts.append(shap_text)
                sources.append(ChatSource(
                    title="explicacion_factores",
                    excerpt=shap_text,
                    source_type="data",
                ))
    elif fecha is not None:
        parts.append(fecha.as_context_line())
        sources.append(ChatSource(
            title="fecha_calculada",
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
                title="proyeccion_estacional_canal_endemico",
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
                title="historial_municipio",
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
                    title="movilidad_municipio",
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
                    title="conclusiones_ia",
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
                    title="clima_historico_departamento",
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
                    title="clima_vivo_open_meteo",
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
                        title="pronostico_open_meteo",
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
                title="clima",
                excerpt=f"T°={climate['avg_temp']}°C, Precip={climate['avg_precip']}mm.",
                source_type="data",
            ))

        cases = _query_cases_by_depto(depto, disease)
        if cases:
            year_str = ", ".join(f"{y}: {c}" for y, c in sorted(cases["by_year"].items()))
            dis_str = ""
            if cases["by_disease"]:
                dis_str = " Por enfermedad: " + ", ".join(
                    f"{d}: {c}" for d, c in cases["by_disease"].items()
                ) + "."
            recent_str = ", ".join(
                f"Sem {w['week']}/{w['year']}: {w['cases']}" for w in cases["recent_weeks"]
            )
            label = disease if disease else "todas las enfermedades"
            parts.append(
                f"Departamento {depto} | {label} "
                f"(datos {cases['data_from']} → {cases['data_to']}, {cases['n_weeks']} semanas): "
                f"TOTAL ACUMULADO: {cases['total_historical']} casos."
                f"{dis_str}"
                f" Desglose anual: {year_str}."
                f" Año pico: {cases['peak_year']} ({cases['peak_cases']} casos)."
                f" Últimas semanas: {recent_str}."
            )
            sources.append(ChatSource(
                title="casos_departamento",
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
            top_str = ", ".join(f"depto {d}: {c}" for d, c in rdata["top_deptos"])
            label = disease if disease else "todas las enfermedades"
            parts.append(
                f"Región {intent['region_norm']} | {label}: "
                f"{rdata['total']} casos totales "
                f"(período {rdata['data_from']} → {rdata['data_to']}). "
                f"Top departamentos: {top_str}."
            )
            sources.append(ChatSource(
                title="resumen_region",
                excerpt=f"Región {intent['region_norm']}: {rdata['total']} casos totales.",
                source_type="data",
            ))
        return " ".join(parts) or "Sin datos para esa región.", sources[:5]

    # ── 5. Nacional (total Colombia o por enfermedad) ────────────────────────
    if intent["wants_national"] or (disease and not depto and not muni):
        nat = _query_national_summary(disease)
        if nat:
            year_str = ", ".join(f"{y}: {c}" for y, c in sorted(nat["by_year"].items()))
            dis_str = ""
            if nat["by_disease"]:
                dis_str = " Por enfermedad: " + ", ".join(
                    f"{d}: {c}" for d, c in nat["by_disease"].items()
                ) + "."
            top_str = ", ".join(f"depto {d}: {c}" for d, c in nat["top_deptos"])
            label = disease if disease else "todas las enfermedades"
            parts.append(
                f"Colombia | {label} "
                f"(datos {nat['data_from']} → {nat['data_to']}): "
                f"TOTAL NACIONAL: {nat['total']} casos."
                f"{dis_str}"
                f" Desglose anual: {year_str}."
                f" Top 5 departamentos más afectados: {top_str}."
            )
            sources.append(ChatSource(
                title="resumen_nacional",
                excerpt=f"Colombia | {label}: {nat['total']} casos totales. Período {nat['data_from']} → {nat['data_to']}.",
                source_type="data",
            ))
        return " ".join(parts) or "Sin datos nacionales.", sources[:5]

    # ── 6. Fallback general ───────────────────────────────────────────────────
    nat = _query_national_summary()
    if nat:
        dis_str = ", ".join(f"{d}: {c}" for d, c in nat.get("by_disease", {}).items())
        parts.append(
            f"Resumen general de la base de datos ECOS: "
            f"{nat['total']} casos totales en Colombia "
            f"(período {nat['data_from']} → {nat['data_to']}). "
            f"Por enfermedad: {dis_str}. "
            f"Para una respuesta más específica, menciona departamento, región o enfermedad."
        )
        sources.append(ChatSource(
            title="resumen_general",
            excerpt=f"Total Colombia: {nat['total']} casos. Enfermedades: {dis_str}.",
            source_type="data",
        ))

    if not sources:
        sources.append(ChatSource(
            title="docs",
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
    answer = rag.generate_answer(req.question, sources, answer)

    logger.info(
        "Chat: disease=%s depto=%s muni=%s climate=%s national=%s",
        intent["disease"], intent["departamento_code"],
        intent["municipio_code"], intent["wants_climate"], intent["wants_national"],
    )
    return ChatResponse(
        answer=answer,
        sources=sources,
        disease=intent["disease"],
        municipio_code=intent["municipio_code"],
        departamento_code=intent["departamento_code"],
    )
