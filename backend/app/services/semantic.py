"""Optional semantic index service using sentence-transformers + faiss.

This module is optional: if dependencies or index file are missing,
functions return empty results and the chat falls back to BM25-style retrieval.
"""
from pathlib import Path
import json
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
INDEX_DIR = REPO_ROOT / "models/semantic"
INDEX_FILE = INDEX_DIR / "index.faiss"
META_FILE = INDEX_DIR / "meta.json"


def _ensure_index_dir():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def available() -> bool:
    try:
        import faiss  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore
        return INDEX_FILE.exists() and META_FILE.exists()
    except Exception:
        return False


def build_index(paths: List[Path], model_name: str = "all-MiniLM-L6-v2", chunk_size: int = 500) -> None:
    """Builds a FAISS index from the given document paths.

    Writes `index.faiss` and `meta.json` to `models/semantic`.
    """
    try:
        import faiss  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception as exc:
        logger.error("Missing dependencies for semantic index: %s", exc)
        raise

    _ensure_index_dir()
    model = SentenceTransformer(model_name)
    metas = []
    embeddings = []

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # naive chunking by characters
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size].strip()
            if not chunk:
                continue
            emb = model.encode(chunk)
            embeddings.append(emb)
            metas.append({"source": str(path), "excerpt": chunk[:400]})

    if not embeddings:
        raise RuntimeError("No embeddings generated from provided paths")

    import numpy as np  # type: ignore

    xb = np.array(embeddings).astype("float32")
    dim = xb.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(xb)
    faiss.write_index(index, str(INDEX_FILE))
    META_FILE.write_text(json.dumps(metas, ensure_ascii=False), encoding="utf-8")
    logger.info("Semantic index built with %d vectors", len(metas))


def search(query: str, k: int = 3) -> List[Tuple[str, str]]:
    """Return up to k (source, excerpt) tuples for the query, or empty list."""
    if not available():
        return []
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        import faiss  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return []

    model = SentenceTransformer("all-MiniLM-L6-v2")
    q_emb = model.encode(query).astype("float32")
    index = faiss.read_index(str(INDEX_FILE))
    D, I = index.search(np.array([q_emb]), k)
    metas = json.loads(META_FILE.read_text(encoding="utf-8"))
    results = []
    for idx in I[0]:
        if idx < 0 or idx >= len(metas):
            continue
        m = metas[idx]
        results.append((m.get("source", ""), m.get("excerpt", "")))
    return results
