import logging
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.epidemiology import ChatRequest, ChatResponse, ChatSource
from app.services.epidemiology import VALID_DISEASES, get_history, get_signals, get_last_known_features
from app.services.prediction import predict_cases
try:
    from app.services.semantic import available as semantic_available, search as semantic_search
except Exception:  # pragma: no cover - optional dependency
    semantic_available = lambda: False
    semantic_search = lambda q, k=3: []

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
    lowered = question.lower()
    disease = next((item for item in VALID_DISEASES if item in lowered), None)
    municipio_code = None
    departamento_code = None
    municipio_match = re.search(r"\b\d{5}\b", question)
    departamento_match = re.search(r"\b\d{2}\b", question)
    if municipio_match:
        municipio_code = municipio_match.group(0)
    elif departamento_match:
        departamento_code = departamento_match.group(0)
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


def _build_answer(question: str, disease: str | None, municipio_code: str | None, departamento_code: str | None) -> tuple[str, list[ChatSource]]:
    sources = _document_snippets(question)
    answer_parts = [
        "ECOS responde con contexto documental y datos curados disponibles.",
    ]

    if disease and municipio_code:
        try:
            history = get_history(municipio_code, disease, limit=8)
        except FileNotFoundError:
            history = None
        if history is not None and not history.empty:
            latest = history.iloc[0]
            trend = "estable"
            if len(history) >= 3:
                recent = history.head(3)["cases_total"].tolist()
                if recent[0] > recent[-1]:
                    trend = "ascendente"
                elif recent[0] < recent[-1]:
                    trend = "descendente"
            prediction_summary = ""
            try:
                forecast = predict_cases(municipio_code, disease, weeks_ahead=2)
                if forecast:
                    next_item = forecast[0]
                    prediction_summary = (
                        f" La predicción a 2 semanas estima {next_item['predicted_cases']:.2f} casos y "
                        f"marca brote={str(next_item['outbreak_flag']).lower()}."
                    )
                    sources.append(
                        ChatSource(
                            title="prediccion_operativa",
                            excerpt=f"Semana {next_item['epi_year']}-W{next_item['epi_week']}: {next_item['predicted_cases']:.2f} casos previstos.",
                            source_type="prediction",
                        )
                    )
            except (FileNotFoundError, ValueError):
                prediction_summary = ""
            answer_parts.append(
                f"Para {disease} en el municipio {municipio_code}, el último registro disponible muestra {int(latest['cases_total'])} casos y una tendencia reciente {trend}."
                f"{prediction_summary}"
            )
            sources.append(ChatSource(title="historial_curado", excerpt=f"Última semana: {int(latest['cases_total'])} casos; municipio {municipio_code}; enfermedad {disease}.", source_type="data"))
    elif disease and departamento_code:
        try:
            signals = get_signals(departamento_code, disease, limit=8)
        except FileNotFoundError:
            signals = None
        if signals is not None and not signals.empty:
            latest = signals.iloc[0]
            answer_parts.append(
                f"Para {disease} en el departamento {departamento_code}, las señales más recientes muestran contexto operativo en RIPS, movilidad y vacunación."
            )
            sources.append(ChatSource(title="senales_curadas", excerpt=f"Última señal: RIPS={latest.get('rips_visits_total', 'n/a')}, movilidad={latest.get('mobility_index', 'n/a')}, vacunación={latest.get('vaccination_coverage_pct', 'n/a')}.", source_type="data"))
    else:
        answer_parts.append(
            "Si quieres una respuesta operativa más exacta, indícame enfermedad y municipio_code o departamento_code."
        )

    if not sources:
        sources.append(ChatSource(title="docs", excerpt="Documentación técnica y diccionario de datos del proyecto ECOS.", source_type="doc"))

    if municipio_code and disease:
        try:
            last_known = get_last_known_features(municipio_code, disease)
        except FileNotFoundError:
            last_known = None
        if last_known is not None:
            answer_parts.append(
                f"El último punto conocido del municipio {municipio_code} para {disease} está disponible para alimentar la predicción operativa."
            )

    return " ".join(answer_parts), sources[:5]


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
    logger.info("Chat answered for disease=%s municipio=%s departamento=%s", disease, municipio_code, departamento_code)
    return ChatResponse(
        answer=answer,
        sources=sources,
        disease=disease,
        municipio_code=municipio_code,
        departamento_code=departamento_code,
    )