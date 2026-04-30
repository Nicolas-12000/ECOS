"""Compute embeddings and load into a Postgres (Supabase) table.

This script uses `sentence-transformers` to compute embeddings and `psycopg` (psycopg[binary])
to insert into the `document_embeddings` table created by `docs/supabase_pgvector.sql`.

Usage:
  export DATABASE_URL="postgresql://..."
  python load_embeddings_supabase.py

Note: confirm `pgvector` extension availability and embedding dimension.
"""
from pathlib import Path
import os
import logging

try:
    from sentence_transformers import SentenceTransformer
except Exception as exc:  # pragma: no cover - dependency guard
    SentenceTransformer = None
    _EMBEDDING_IMPORT_ERROR = exc

try:
    import psycopg
except Exception as exc:  # pragma: no cover - dependency guard
    psycopg = None
    _PSYCOPG_IMPORT_ERROR = exc

logger = logging.getLogger("load_embeddings_supabase")


def collect_docs(root: Path):
    return list((root / "docs").rglob("*.md"))


def compute_embeddings(texts, model_name="all-MiniLM-L6-v2"):
    if SentenceTransformer is None:
        raise RuntimeError(f"sentence-transformers is not available: {_EMBEDDING_IMPORT_ERROR}")
    model = SentenceTransformer(model_name)
    embs = model.encode(texts)
    return embs


def upsert_embeddings(db_url: str, records):
    if psycopg is None:
        raise RuntimeError(f"psycopg is not available: {_PSYCOPG_IMPORT_ERROR}")
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Ensure pgvector and uuid-generating extension exist when possible
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            except Exception:
                # Not critical; may lack permissions on some managed DBs
                pass
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            except Exception:
                pass

            # Create table if missing (id default uses gen_random_uuid from pgcrypto)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS public.document_embeddings (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_text text,
                    excerpt text,
                    embedding vector(384),
                    created_at timestamptz DEFAULT now()
                );
                """
            )

            # Create index if possible (ivfflat requires proper vector config)
            try:
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_document_embeddings_embedding ON public.document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
                )
            except Exception:
                # index creation can fail if the operator class or extension isn't available
                pass

            for src, excerpt, emb in records:
                # emb must be list[float] and match vector dim
                cur.execute(
                    """
                    INSERT INTO public.document_embeddings (source_text, excerpt, embedding)
                    VALUES (%s, %s, %s)
                    """,
                    (str(src), excerpt, emb.tolist()),
                )


def main():
    repo_root = Path(__file__).resolve().parents[2]
    docs = collect_docs(repo_root)
    if not docs:
        logger.error("No docs to embed")
        return
    texts = []
    meta = []
    for p in docs:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        excerpt = txt.strip()[:400]
        texts.append(txt)
        meta.append((p, excerpt))

    embs = compute_embeddings(texts)
    records = [(m[0], m[1], emb) for m, emb in zip(meta, embs)]

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("Set DATABASE_URL environment variable to Supabase DB URL")
        return
    upsert_embeddings(db_url, records)
    logger.info("Uploaded %d embeddings to Supabase", len(records))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
