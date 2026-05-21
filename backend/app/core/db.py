"""Database connection utility for Supabase/PostgreSQL via psycopg."""

import logging
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from app.core.config import settings

logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """Context manager que abre y cierra la conexión a Supabase."""
    db_url = settings.resolved_database_url()
    if not db_url:
        raise RuntimeError("SUPABASE_DB_URL (or DATABASE_URL) is not configured in .env")
    conn = psycopg.connect(db_url)
    try:
        yield conn
    finally:
        conn.close()
