import logging
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.epidemiology import ChatRequest, ChatResponse, ChatSource
from app.services.epidemiology import VALID_DISEASES, get_history, get_last_known_features
from app.services.prediction import predict_cases
from app.services import rag
from app.core.db import get_db_connection

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
            ROUND(AVG(NULLIF(humidity_avg_pct, 0))::numeric, 2)   AS avg_humidity,
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
        "avg_precip": r[3], "max_precip": r[4], "avg_humidity": r[5],
        "data_from": str(r[6]), "data_to": str(r[7]),
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

    return {
        "disease": disease,
        "departamento_code": departamento_code,
        "municipio_code": municipio_code,
        "wants_climate": wants_climate,
        "wants_national": wants_national,
        "wants_region": wants_region,
        "region_norm": region_norm,
    }


# ---------------------------------------------------------------------------
# Knowledge base search
# ---------------------------------------------------------------------------

def _search_knowledge_base(question: str, limit: int = 3) -> list[ChatSource]:
    rows = _db_execute("""
        SELECT title, content
        FROM public.knowledge_base
        WHERE to_tsvector('spanish', content) @@ plainto_tsquery('spanish', %s)
           OR content ILIKE %s
        LIMIT %s
    """, (question, f"%{question}%", limit))
    return [ChatSource(title=r[0], excerpt=r[1][:500], source_type="doc") for r in rows]


def _document_snippets(question: str, limit: int = 3) -> list[ChatSource]:
    db_sources = _search_knowledge_base(question, limit=limit)
    if db_sources:
        return db_sources
    if semantic_available():
        try:
            hits = semantic_search(question, k=limit)
            sources = [ChatSource(title=Path(s).name, excerpt=e, source_type="doc") for s, e in hits]
            if sources:
                return sources
        except Exception:
            pass
    return []


# ---------------------------------------------------------------------------
# Answer builder
# ---------------------------------------------------------------------------

def _build_answer(question: str, intent: dict) -> tuple[str, list[ChatSource]]:
    sources = _document_snippets(question)
    parts: list[str] = []

    disease = intent["disease"]
    depto = intent["departamento_code"]
    muni = intent["municipio_code"]

    # ── 1. Municipio + enfermedad → histórico local ──────────────────────────
    if muni and disease:
        try:
            history = get_history(muni, disease, limit=8)
        except FileNotFoundError:
            history = None
        if history is not None and not history.empty:
            latest = history.iloc[0]
            recent = history.head(4)["cases_total"].tolist()
            trend = ("ascendente" if recent[0] > recent[-1]
                     else "descendente" if recent[0] < recent[-1] else "estable")
            parts.append(
                f"Municipio {muni} | {disease}: {int(latest['cases_total'])} casos en la última semana "
                f"(tendencia {trend}). Últimas 4 semanas: {recent}."
            )
            sources.append(ChatSource(
                title="historial_municipio",
                excerpt=f"{muni}/{disease}: última semana {int(latest['cases_total'])} casos, tendencia {trend}.",
                source_type="data",
            ))
        return " ".join(parts) or "No se encontraron datos para ese municipio.", sources

    # ── 2. Clima por departamento ────────────────────────────────────────────
    if intent["wants_climate"] and depto:
        climate = _query_climate_by_depto(depto)
        if climate:
            parts.append(
                f"Datos climáticos del departamento {depto} "
                f"(período {climate['data_from']} – {climate['data_to']}): "
                f"Temperatura promedio: {climate['avg_temp']}°C "
                f"(mín {climate['min_temp']}°C / máx {climate['max_temp']}°C). "
                f"Precipitación promedio: {climate['avg_precip']} mm "
                f"(máximo registrado: {climate['max_precip']} mm). "
                f"Humedad promedio: {climate['avg_humidity']}%."
            )
            sources.append(ChatSource(
                title="clima_departamento",
                excerpt=f"Depto {depto}: T°={climate['avg_temp']}°C, Precip={climate['avg_precip']}mm, Humedad={climate['avg_humidity']}%.",
                source_type="data",
            ))
        else:
            parts.append(f"No se encontraron datos climáticos para el departamento {depto} en la base de datos.")
        
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
