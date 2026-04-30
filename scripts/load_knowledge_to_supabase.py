#!/usr/bin/env python3
"""Load markdown documents into Supabase knowledge_base table for RAG."""

import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

DOC_PATHS = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "Ecos.md",
    REPO_ROOT / "docs/api.md",
    REPO_ROOT / "docs/data-dictionary.md",
    REPO_ROOT / "docs/data-lineage.md",
]

def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    """Simple paragraph-based chunking."""
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def main():
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        print("[error] SUPABASE_DB_URL not found in .env")
        return

    print(f"[info] connecting to database...")
    
    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                print("[info] clearing knowledge_base table...")
                cur.execute("TRUNCATE TABLE public.knowledge_base")
                
                for path in DOC_PATHS:
                    if not path.exists():
                        print(f"[warn] skipping {path.name}: not found")
                        continue
                    
                    print(f"[info] processing {path.name}...")
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    chunks = chunk_text(text)
                    
                    for i, chunk in enumerate(chunks):
                        cur.execute(
                            """
                            INSERT INTO public.knowledge_base (title, content, source_path, metadata)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                f"{path.name} - Part {i+1}",
                                chunk,
                                str(path.relative_to(REPO_ROOT)),
                                json.dumps({"chunk_index": i, "total_chunks": len(chunks)})
                            )
                        )
                
            conn.commit()
            print("[ok] knowledge_base populated successfully")
    except Exception as e:
        print(f"[error] {e}")

if __name__ == "__main__":
    main()
