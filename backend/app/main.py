from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title="ECOS API",
    version="0.1.0",
    debug=settings.debug,
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"name": "ECOS API", "status": "ok"}
