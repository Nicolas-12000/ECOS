#!/usr/bin/env python3
"""
Scraper for INS (Instituto Nacional de Salud) Epidemiological Bulletins.
Downloads PDFs, extracts text, and loads into knowledge_base with embeddings.
"""

import argparse
import io
import logging
import requests
import pdfplumber
from pathlib import Path
from dotenv import load_dotenv

# Import semantic service to generate embeddings
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.semantic import generate_embedding
from app.core.db import get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

def download_pdf(url: str) -> io.BytesIO:
    logger.info(f"Downloading PDF from {url}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return io.BytesIO(response.content)

def extract_text_from_pdf(pdf_stream: io.BytesIO) -> str:
    logger.info("Extracting text from PDF...")
    text_content = []
    with pdfplumber.open(pdf_stream) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
    return "\n\n".join(text_content)

def save_to_knowledge_base(title: str, content: str):
    logger.info(f"Saving '{title}' to knowledge_base...")
    embedding = generate_embedding(content[:2000]) # Use first 2000 chars for embedding
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if already exists
                cur.execute("SELECT id FROM public.knowledge_base WHERE title = %s", (title,))
                if cur.fetchone():
                    logger.info(f"Bulletin '{title}' already exists. Updating...")
                    cur.execute("""
                        UPDATE public.knowledge_base 
                        SET content = %s, embedding = %s::vector 
                        WHERE title = %s
                    """, (content, embedding_str, title))
                else:
                    cur.execute("""
                        INSERT INTO public.knowledge_base (title, content, embedding)
                        VALUES (%s, %s, %s::vector)
                    """, (title, content, embedding_str))
            conn.commit()
        logger.info("[ok] Saved.")
    except Exception as e:
        logger.error(f"Failed to save to DB: {e}")

def main():
    parser = argparse.ArgumentParser(description="INS Bulletin Scraper")
    parser.add_argument("url", help="URL of the INS PDF bulletin")
    parser.add_argument("--title", help="Title for the knowledge entry", default=None)
    
    args = parser.parse_args()
    
    if not args.title:
        # Extract title from URL or use generic
        args.title = args.url.split("/")[-1]
        
    try:
        pdf_stream = download_pdf(args.url)
        content = extract_text_from_pdf(pdf_stream)
        
        if content.strip():
            save_to_knowledge_base(args.title, content)
        else:
            logger.warning("No text extracted from PDF.")
            
    except Exception as e:
        logger.error(f"Scraping failed: {e}")

if __name__ == "__main__":
    main()
