from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.predict import router as predict_router
from app.api.routes.signals import router as signals_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(predict_router, prefix="/api/v1", tags=["predict"])
api_router.include_router(history_router, prefix="/api/v1", tags=["history"])
api_router.include_router(signals_router, prefix="/api/v1", tags=["signals"])
