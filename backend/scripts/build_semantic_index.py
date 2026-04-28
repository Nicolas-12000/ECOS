"""Build a semantic FAISS index for repository docs.

Usage:
  python build_semantic_index.py

Requires `sentence-transformers` and `faiss-cpu` installed in the active venv.
"""
from pathlib import Path
import logging
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services import semantic

logger = logging.getLogger("build_semantic_index")


def collect_doc_paths(root: Path):
    docs = []
    seen = set()
    for path in root.rglob("*.md"):
        if any(part in {".venv", "node_modules", ".git"} for part in path.parts):
            continue
        if str(path) in seen:
            continue
        docs.append(path)
        seen.add(str(path))
    return docs


def main():
    paths = collect_doc_paths(REPO_ROOT)
    if not paths:
        logger.error("No documentation files found to index")
        return
    logger.info("Building semantic index with %d docs", len(paths))
    semantic.build_index(paths)
    logger.info("Index built at models/semantic")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
