import logging
import re
import unicodedata
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.epidemiology import ChatRequest, ChatResponse, ChatSource
from app.services.epidemiology import VALID_DISEASES, get_history, get_signals, get_last_known_features
from app.services.prediction import predict_cases
from app.services import rag
try:
    from app.services.semantic import available as semantic_available, search as semantic_search
except Exception:  # pragma: no cover - optional dependency
    semantic_available = lambda: False
    semantic_search = lambda q, k=3: []

try:
    from app.scraping.scraping_service import fetch_rss_articles
except Exception:  # pragma: no cover
    fetch_rss_articles = lambda **kw: []

logger = logging.getLogger(__name__)
router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[4]
DOC_PATHS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "Ecos.md",
    REPO_ROOT / "docs/api.md",
    REPO_ROOT / "docs/data-dictionary.md",
    REPO_ROOT / "docs/data-lineage.md",
    REPO_ROOT / "docs/sprints.md",
    REPO_ROOT / "docs/metrics-final.md",
]

# ── Mapeo de nombres comunes a códigos DANE ────────────────────────────────
# Departamentos: nombre normalizado → código DANE 2 dígitos
DEPARTAMENTO_NAME_TO_CODE = {
    "amazonas": "91", "antioquia": "05", "arauca": "81", "atlantico": "08",
    "bolivar": "13", "boyaca": "15", "caldas": "17", "caqueta": "18",
    "casanare": "85", "cauca": "19", "cesar": "20", "choco": "27",
    "cordoba": "23", "cundinamarca": "25", "guainia": "94", "guaviare": "95",
    "huila": "41", "la guajira": "44", "guajira": "44", "magdalena": "47",
    "meta": "50", "narino": "52", "nariño": "52",
    "norte de santander": "54", "norte santander": "54",
    "putumayo": "86", "quindio": "63", "risaralda": "66",
    "san andres": "88", "san andres y providencia": "88",
    "santander": "68", "sucre": "70", "tolima": "73",
    "valle del cauca": "76", "valle": "76", "vaupes": "97", "vichada": "99",
    "bogota": "11", "bogota dc": "11", "distrito capital": "11",
}

# Capitales departamentales: nombre normalizado → código DANE 5 dígitos
MUNICIPIO_NAME_TO_CODE = {
    "medellin": "05001", "barranquilla": "08001", "bogota": "11001",
    "cartagena": "13001", "tunja": "15001", "manizales": "17001",
    "florencia": "18001", "popayan": "19001", "valledupar": "20001",
    "quibdo": "27001", "monteria": "23001", "agua de dios": "25001",
    "neiva": "41001", "riohacha": "44001", "santa marta": "47001",
    "villavicencio": "50001", "pasto": "52001", "cucuta": "54001",
    "armenia": "63001", "pereira": "66001", "bucaramanga": "68001",
    "sincelejo": "70001", "ibague": "73001", "cali": "76001",
    "arauca": "81001", "yopal": "85001", "mocoa": "86001",
    "leticia": "91001", "puerto carreno": "99001", "inirida": "94001",
    "san jose del guaviare": "95001", "mitu": "97001",
    "san andres": "88001", "providencia": "88564",
}


def _normalize_name(text: str) -> str:
    """Remove accents and lowercase for flexible matching."""
    text = unicodedata.normalize("NFKD", text.lower().strip())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _section_snippet(text: str, terms: set[str]) -> tuple[int, str]:
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    best_score = 0
    best_snippet = ""
    for paragraph in paragraphs:
        normalized = _clean_text(paragraph)
        score = sum(normalized.lower().count(term) for term in terms)
        if score > best_score:
            best_score = score
            best_snippet = normalized[:500]
    return best_score, best_snippet


def _extract_terms(question: str) -> tuple[str | None, str | None, str | None]:
    """Extract disease, municipio_code, and departamento_code from the question.

    Supports both DANE codes and natural language names (e.g., "Medellín", "Antioquia").
    """
    lowered = question.lower()
    normalized = _normalize_name(question)

    # 1. Disease detection
    disease = next((item for item in VALID_DISEASES if item in lowered), None)

    municipio_code = None
    departamento_code = None

    # 2. Try explicit DANE codes first
    municipio_match = re.search(r"\b\d{5}\b", question)
    departamento_match = re.search(r"\b\d{2}\b", question)
    if municipio_match:
        municipio_code = municipio_match.group(0)
    elif departamento_match:
        departamento_code = departamento_match.group(0)

    # 3. If no code found, try name-based resolution
    if not municipio_code and not departamento_code:
        # Check municipio names first (more specific)
        for name, code in MUNICIPIO_NAME_TO_CODE.items():
            if name in normalized:
                municipio_code = code
                break

        # If no municipio found, check departamento names
        if not municipio_code:
            for name, code in DEPARTAMENTO_NAME_TO_CODE.items():
                if name in normalized:
                    departamento_code = code
                    break

    return disease, municipio_code, departamento_code


def _document_snippets(question: str, limit: int = 3) -> list[ChatSource]:
    # Prefer semantic search when available and index exists
    if semantic_available():
        try:
            hits = semantic_search(question, k=limit)
            sources = []
            for src, excerpt in hits:
                sources.append(ChatSource(title=Path(src).name, excerpt=excerpt, source_type="doc"))
            if sources:
                return sources
        except Exception:
            pass

    terms = {word for word in re.findall(r"[a-záéíóúñ0-9]+", question.lower()) if len(word) > 3}
    scored: list[tuple[int, Path, str]] = []
    for path in DOC_PATHS:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        score, snippet = _section_snippet(text, terms)
        if score:
            scored.append((score, path, snippet))
    scored.sort(key=lambda item: item[0], reverse=True)
    sources = []
    for _, path, snippet in scored[:limit]:
        sources.append(ChatSource(title=path.name, excerpt=snippet, source_type="doc"))
    return sources


def _fetch_relevant_news(disease: str | None, limit: int = 3) -> list[ChatSource]:
    """Fetch recent RSS articles relevant to the disease from Colombian media."""
    try:
        articles = fetch_rss_articles(lookback_days=30)
    except Exception:
        return []

    if disease:
        articles = [a for a in articles if disease in a.get("diseases", [])]

    sources = []
    for article in articles[:limit]:
        title = article.get("title", "Noticia")
        summary = article.get("summary", "")
        source_name = article.get("source", "")
        published = article.get("published", "")
        relevance = article.get("relevance_score", 0)
        diseases_str = ", ".join(article.get("diseases", []))

        excerpt = (
            f"[{source_name}] {title}. "
            f"Publicado: {published}. "
            f"Enfermedades: {diseases_str}. "
            f"Relevancia: {relevance}. "
            f"Resumen: {summary[:200]}"
        )
        sources.append(ChatSource(
            title=f"RSS_{source_name}",
            excerpt=excerpt,
            source_type="news",
        ))
    return sources


def _build_detailed_context(
    last_row, history, disease: str, municipio_code: str
) -> str:
    """Build a rich textual summary of all available data for the LLM."""
    parts = []

    if last_row is not None:
        latest_cases = int(last_row.get("cases_total", 0))
        epi_year = int(last_row.get("epi_year", 0))
        epi_week = int(last_row.get("epi_week", 0))
        dept_code = str(last_row.get("departamento_code", ""))

        parts.append(
            f"Municipio {municipio_code} (depto {dept_code}), enfermedad: {disease}."
        )
        parts.append(
            f"Último registro: año {epi_year}, semana {epi_week}, "
            f"casos_total={latest_cases}."
        )

        # Trend from last 3 weeks
        if history is not None and len(history) >= 3:
            recent = history.head(3)["cases_total"].tolist()
            if recent[0] > recent[-1]:
                trend = "ASCENDENTE ↑"
            elif recent[0] < recent[-1]:
                trend = "DESCENDENTE ↓"
            else:
                trend = "ESTABLE →"
            parts.append(
                f"Tendencia últimas 3 semanas: {trend} "
                f"(valores: {recent[0]}, {recent[1]}, {recent[2]})."
            )

        # Climate
        temp = last_row.get("temp_avg_c")
        humidity = last_row.get("humidity_avg_pct")
        precip = last_row.get("precipitation_mm")
        if temp is not None and str(temp) != "nan":
            parts.append(
                f"Clima actual: temp_avg={float(temp):.1f}°C, "
                f"humedad={float(humidity or 0):.1f}%, "
                f"precipitación={float(precip or 0):.1f}mm."
            )

        # Vaccination
        vacc = last_row.get("vaccination_coverage_pct")
        if vacc is not None and str(vacc) != "nan":
            parts.append(
                f"Cobertura de vacunación departamental: {float(vacc):.1f}%."
            )

        # RIPS
        rips = last_row.get("rips_visits_total")
        if rips is not None and str(rips) != "nan" and float(rips) > 0:
            parts.append(
                f"Atenciones RIPS (arbovirosis): {int(float(rips))} visitas."
            )

        # Mobility / Transport
        mobility = last_row.get("mobility_index")
        if mobility is not None and str(mobility) != "nan" and float(mobility) > 0:
            parts.append(
                f"Índice de movilidad intermunicipal: {float(mobility):.1f} "
                f"(pasajeros — mayor valor = mayor riesgo de propagación regional). "
                f"Fuente: Dataset 6 — Movilidad Urbana y Transporte, Ministerio de Transporte."
            )

        # Early signals
        trends = last_row.get("trends_score")
        rss = last_row.get("rss_mentions")
        sig = last_row.get("signals_score")
        if trends is not None and str(trends) != "nan":
            parts.append(
                f"Señales tempranas: Google Trends score={float(trends):.1f}, "
                f"menciones RSS en medios={int(float(rss or 0))}, "
                f"signals_score combinado={float(sig or 0):.3f}."
            )

    return " ".join(parts)


def _build_answer(
    question: str,
    disease: str | None,
    municipio_code: str | None,
    departamento_code: str | None,
) -> tuple[str, list[ChatSource]]:
    sources = _document_snippets(question)

    # Add RSS news if disease is known
    if disease:
        news_sources = _fetch_relevant_news(disease, limit=3)
        sources.extend(news_sources)

    answer_parts = [
        "ECOS responde con datos del sistema de vigilancia epidemiológica de Colombia.",
    ]

    if disease and municipio_code:
        try:
            history = get_history(municipio_code, disease, limit=8)
        except FileNotFoundError:
            history = None

        try:
            last_row = get_last_known_features(municipio_code, disease)
        except FileNotFoundError:
            last_row = None

        if history is not None and not history.empty:
            # Build detailed context with all variables
            detailed = _build_detailed_context(
                last_row, history, disease, municipio_code
            )
            answer_parts.append(detailed)

            # Add prediction
            prediction_summary = ""
            try:
                forecast = predict_cases(municipio_code, disease, weeks_ahead=2)
                if forecast:
                    next_item = forecast[0]
                    outbreak_text = "SÍ" if next_item["outbreak_flag"] else "NO"
                    prediction_summary = (
                        f"Predicción a 2 semanas (semana {next_item['epi_year']}-W{next_item['epi_week']}): "
                        f"{next_item['predicted_cases']:.1f} casos estimados. "
                        f"Alerta de brote: {outbreak_text} "
                        f"(umbral: {next_item['outbreak_threshold']} casos)."
                    )
                    sources.append(
                        ChatSource(
                            title="prediccion_modelo_XGBoost",
                            excerpt=(
                                f"Semana {next_item['epi_year']}-W{next_item['epi_week']}: "
                                f"{next_item['predicted_cases']:.1f} casos previstos. "
                                f"Brote={outbreak_text}."
                            ),
                            source_type="prediction",
                        )
                    )
            except (FileNotFoundError, ValueError):
                prediction_summary = ""

            if prediction_summary:
                answer_parts.append(prediction_summary)

            # Source: curated data
            latest = history.iloc[0]
            sources.append(ChatSource(
                title="datos_curados_SIVIGILA",
                excerpt=(
                    f"Última semana: {int(latest['cases_total'])} casos; "
                    f"municipio {municipio_code}; enfermedad {disease}. "
                    f"Fuente: SIVIGILA + IDEAM + señales tempranas."
                ),
                source_type="data",
            ))
        else:
            answer_parts.append(
                f"No se encontraron datos históricos para el municipio {municipio_code} "
                f"con la enfermedad {disease}. Verifica el código DANE del municipio."
            )

    elif disease and departamento_code:
        try:
            signals = get_signals(departamento_code, disease, limit=8)
        except FileNotFoundError:
            signals = None
        if signals is not None and not signals.empty:
            latest = signals.iloc[0]
            vacc = latest.get("vaccination_coverage_pct", "n/a")
            trends = latest.get("trends_score", "n/a")
            rss = latest.get("rss_mentions", "n/a")
            sig = latest.get("signals_score", "n/a")

            answer_parts.append(
                f"Departamento {departamento_code}, enfermedad {disease}. "
                f"Señales más recientes: vacunación={vacc}%, "
                f"Google Trends={trends}, menciones RSS={rss}, "
                f"signals_score={sig}."
            )
            sources.append(ChatSource(
                title="senales_departamentales",
                excerpt=(
                    f"Depto {departamento_code}: vacunación={vacc}%, "
                    f"trends={trends}, rss={rss}, score={sig}."
                ),
                source_type="data",
            ))
        else:
            answer_parts.append(
                f"No se encontraron señales para el departamento {departamento_code} "
                f"con la enfermedad {disease}."
            )
    else:
        answer_parts.append(
            "Para una respuesta operativa precisa, indícame la enfermedad "
            "(dengue, chikungunya, zika o malaria) y el municipio o departamento. "
            "Puedes usar el nombre (ej: 'Medellín', 'Antioquia') o el código DANE."
        )

    if not sources:
        sources.append(ChatSource(
            title="ECOS_docs",
            excerpt="Documentación técnica del proyecto ECOS — plataforma de alerta temprana epidemiológica.",
            source_type="doc",
        ))

    return " ".join(answer_parts), sources[:8]


@router.post("/chat", response_model=ChatResponse, summary="Asistente conversacional con contexto documental y epidemiológico")
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="question is required")

    disease = req.disease
    municipio_code = req.municipio_code
    departamento_code = req.departamento_code

    if disease and disease not in VALID_DISEASES:
        raise HTTPException(status_code=422, detail=f"disease must be one of {sorted(VALID_DISEASES)}")

    if not disease or (not municipio_code and not departamento_code):
        inferred_disease, inferred_municipio, inferred_departamento = _extract_terms(req.question)
        disease = disease or inferred_disease
        municipio_code = municipio_code or inferred_municipio
        departamento_code = departamento_code or inferred_departamento

    answer, sources = _build_answer(req.question, disease, municipio_code, departamento_code)
    answer = rag.generate_answer(req.question, sources, answer)
    logger.info("Chat answered for disease=%s municipio=%s departamento=%s", disease, municipio_code, departamento_code)
    return ChatResponse(
        answer=answer,
        sources=sources,
        disease=disease,
        municipio_code=municipio_code,
        departamento_code=departamento_code,
    )
