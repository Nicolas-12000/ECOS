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
            chunks.append(f"- {title}: {excerpt}")
    return "\n".join(chunks)


def generate_answer(question: str, sources: Iterable, fallback: str) -> str:
    if not available():
        return fallback

    context = _build_context(sources)
    system = (
        "Eres el asistente ECOS. Responde en espanol, breve y operativo. "
        "Toda tu informacion proviene de la base de datos oficial en Supabase. "
        "Usa solo el contexto y los hechos entregados. Si faltan datos, dilo."
    )
    user = (
        "Pregunta:\n"
        f"{question}\n\n"
        "Contexto documental (puede estar incompleto):\n"
        f"{context}\n\n"
        "Hechos operativos preliminares:\n"
        f"{fallback}\n\n"
        "Devuelve una respuesta clara, con una accion sugerida si aplica."
    )

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
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
