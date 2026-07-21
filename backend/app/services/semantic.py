"""Semantic search service using Supabase pgvector.

Uses sentence-transformers locally to generate embeddings and queries 
the Supabase database for vector similarity.
"""

import logging
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from app.core.db import get_db_connection

logger = logging.getLogger(__name__)

# Load model once (all-MiniLM-L6-v2 is standard 384 dims)
_model = None

def get_model():
    global _model
    if _model is None:
        logger.info("Loading sentence-transformer model: all-MiniLM-L6-v2")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def available() -> bool:
    """Check if semantic search is ready (model can be loaded)."""
    try:
        get_model()
        return True
    except Exception as e:
        logger.error(f"Semantic service not available: {e}")
        return False

def generate_embedding(text: str) -> List[float]:
    """Generates a vector embedding for the given text."""
    model = get_model()
    embedding = model.encode(text)
    return embedding.tolist()

def search(query: str, k: int = 3, threshold: float = 0.4) -> List[Tuple[str, str]]:
    """
    Searches the knowledge_base in Supabase using vector similarity.
    Returns List of (title, content) tuples.
    """
    try:
        embedding = generate_embedding(query)
        # Convert list to Postgres vector format string: [1.2, 3.4, ...]
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1 - (embedding <=> vector) is cosine similarity
                cur.execute("""
                    SELECT metadata->>'title' as title, content, 1 - (embedding <=> %s::vector) AS similarity
                    FROM public.knowledge_base
                    WHERE 1 - (embedding <=> %s::vector) > %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (embedding_str, embedding_str, threshold, embedding_str, k))
                
                rows = cur.fetchall()
                # Return in same format as old search: (source, excerpt)
                return [(r[0], r[1]) for r in rows]
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []

def update_document_embeddings() -> int:
    """Batch updates embeddings for all documents missing them in the DB."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, content FROM public.knowledge_base WHERE embedding IS NULL")
                rows = cur.fetchall()
                
                if not rows:
                    return 0
                
                logger.info(f"Updating embeddings for {len(rows)} documents...")
                count = 0
                for doc_id, content in rows:
                    if not content: continue
                    emb = generate_embedding(content)
                    emb_str = "[" + ",".join(map(str, emb)) + "]"
                    cur.execute("UPDATE public.knowledge_base SET embedding = %s::vector WHERE id = %s", (emb_str, doc_id))
                    count += 1
                
            conn.commit()
            return count
    except Exception as e:
        logger.error(f"Failed to update document embeddings: {e}")
        return 0
