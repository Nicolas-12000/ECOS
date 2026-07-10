from fastapi import APIRouter

# Solo importamos los routers NECESARIOS para el RAG (sin dependencias de ML pesado)
from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.chat import router as chat_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.signals import router as signals_router
from app.api.routes.endemic import router as endemic_router
from app.api.routes.report import router as report_router

api_router = APIRouter()

# Health siempre en la raíz
api_router.include_router(health_router, tags=["health"])

# Prefijos compatibilidad
api_prefixes = ["/api", "/api/v1", "/api/v3"]

# Lista de routers esenciales para RAG
routers = [
    (chat_router, "chat"),
    (history_router, "history"),
    (alerts_router, "alerts"),
    (signals_router, "signals"),
    (endemic_router, "endemic"),
    (report_router, "report"),
]

for prefix in api_prefixes:
    for r, tag in routers:
        api_router.include_router(r, prefix=prefix, tags=[tag])
