from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging


configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}
