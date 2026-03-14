from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.models import *  # noqa: F403
from app.db.session import get_engine
from app.db.session import ensure_mock_database_exists
from app.db.session import get_mock_engine
from app.db.session import get_mock_session_factory
from app.mock_records.db.base import MockRecordsBase
from app.mock_records.db.bootstrap import seed_mock_records
from app.mock_records.db.models import *  # noqa: F403


configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await ensure_mock_database_exists()
    async with get_mock_engine().begin() as conn:
        await conn.run_sync(MockRecordsBase.metadata.create_all)
    async with get_mock_session_factory()() as mock_session:
        await seed_mock_records(mock_session)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}
