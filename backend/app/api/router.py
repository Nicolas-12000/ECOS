from fastapi import APIRouter

from app.api.routes.alerts import router as alerts_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.predict import router as predict_router
from app.api.routes.weather import router as weather_router
from app.api.routes.scraping import router as scraping_router
from app.api.routes.signals import router as signals_router
from app.api.routes.endemic import router as endemic_router
from app.api.routes.trends import router as trends_router
from app.api.routes.news import router as news_router
from app.api.routes.mobility import router as mobility_router
from app.api.routes.timeseries import router as timeseries_router
from app.api.routes.whatif import router as whatif_router
from app.api.routes.report import router as report_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(predict_router, prefix="/api/v1", tags=["predict"])
api_router.include_router(history_router, prefix="/api/v1", tags=["history"])
api_router.include_router(chat_router, prefix="/api/v1", tags=["chat"])
api_router.include_router(alerts_router, prefix="/api/v1", tags=["alerts"])
api_router.include_router(scraping_router, prefix="/api/v1", tags=["scraping"])
api_router.include_router(signals_router, prefix="/api/v1", tags=["signals"])
api_router.include_router(weather_router, prefix="/api/v1", tags=["weather"])
api_router.include_router(endemic_router, prefix="/api/v1", tags=["endemic"])
api_router.include_router(trends_router, prefix="/api/v1", tags=["trends"])
api_router.include_router(news_router, prefix="/api/v1", tags=["news"])
api_router.include_router(mobility_router, prefix="/api/v1", tags=["mobility"])
api_router.include_router(timeseries_router, prefix="/api/v1", tags=["timeseries"])
api_router.include_router(whatif_router, prefix="/api/v1", tags=["whatif"])
api_router.include_router(report_router, prefix="/api/v1", tags=["report"])
