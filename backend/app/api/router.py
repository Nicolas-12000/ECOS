from fastapi import APIRouter

from app.api.routes.alerts import router as alerts_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.predict import router as predict_router

from app.api.routes.scraping import router as scraping_router
from app.api.routes.signals import router as signals_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(predict_router, prefix="/api", tags=["predict"])
api_router.include_router(history_router, prefix="/api", tags=["history"])

api_router.include_router(chat_router, prefix="/api", tags=["chat"])
api_router.include_router(alerts_router, prefix="/api", tags=["alerts"])
api_router.include_router(signals_router, prefix="/api", tags=["signals"])
api_router.include_router(scraping_router, prefix="/api", tags=["scraping"])
