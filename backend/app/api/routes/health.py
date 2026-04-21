import logging

import psycopg
from fastapi import APIRouter

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health():
    payload = {"status": "ok"}
    database_url = settings.resolved_database_url()
    if database_url:
        try:
            with psycopg.connect(database_url, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("select 1;")
            payload["database"] = "ok"
        except Exception:
            logger.exception("Database health check failed")
            payload["database"] = "error"
    return payload
