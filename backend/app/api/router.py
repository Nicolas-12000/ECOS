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
from app.api.routes.anova import router as anova_router

api_router = APIRouter()

# Health remains at root `/health`
api_router.include_router(health_router, tags=["health"])

# Provide compatibility prefixes so clients/tests using different API versions continue
# to work: `/api`, `/api/v1` and `/api/v3` will expose the same set of routers.
api_prefixes = ["/api", "/api/v1", "/api/v3"]

routers = [
	(predict_router, "predict"),
	(history_router, "history"),
	(chat_router, "chat"),
	(alerts_router, "alerts"),
	(scraping_router, "scraping"),
	(signals_router, "signals"),
	(weather_router, "weather"),
	(endemic_router, "endemic"),
	(trends_router, "trends"),
	(news_router, "news"),
	(mobility_router, "mobility"),
	(timeseries_router, "timeseries"),
	(whatif_router, "whatif"),
	(report_router, "report"),
	(anova_router, "anova"),
]

for prefix in api_prefixes:
	for r, tag in routers:
		api_router.include_router(r, prefix=prefix, tags=[tag])
