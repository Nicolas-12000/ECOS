"""Lightweight RAG answer generation using Groq (optional)."""

from __future__ import annotations

from typing import Iterable

import httpx

from app.core.config import settings


def available() -> bool:
    return bool(settings.groq_api_key)


def _build_context(sources: Iterable) -> str:
    chunks = []
    for src in sources:
        title = getattr(src, "title", "doc")
        excerpt = getattr(src, "excerpt", "")
        if excerpt:
            chunks.append(f"- [{title}]: {excerpt}")
    return "\n".join(chunks)


def generate_answer(question: str, sources: Iterable, fallback: str) -> str:
    if not available():
        return fallback

    context = _build_context(sources)
    system = (
        "Eres ECOS AI, un experto en vigilancia epidemiológica de Colombia. "
        "Tu misión es proporcionar análisis precisos basados únicamente en los datos entregados. "
        "Reglas:\n"
        "1. Cita siempre la fuente con metadatos (ej: [historial_municipio] — publication_date: YYYY-MM-DD).\n"
        "2. Si los datos sugieren un brote (casos > umbral), destaca la alerta.\n"
        "3. Si usas fuentes de 2020/2021 o que mencionan 'covid', incluye una nota breve sobre posibles anomalías relacionadas con la pandemia y cómo eso afecta la interpretación.\n"
        "4. Cuando las fuentes provengan mayoritariamente de 2020/2021, añade una línea de confianza/limitación en la respuesta.\n"
        "5. Si no tienes datos suficientes para responder, dilo claramente.\n"
        "6. Mantén un tono profesional, técnico y operativo.\n"
        "7. Responde en español."
    )
    user = (
        f"Pregunta del usuario: {question}\n\n"
        "--- CONTEXTO RECUPERADO ---\n"
        f"{context}\n\n"
        "--- DATOS OPERATIVOS (API) ---\n"
        f"{fallback}\n\n"
        "Genera una respuesta estructurada que analice la situación y sugiera acciones si es necesario."
    )

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

    try:
        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return fallback
