from collections.abc import AsyncGenerator

from fastapi import Header

from app.core.security import RequestContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_mock_session_factory, get_session_factory


async def get_request_context(
    x_user_id: str | None = Header(default=None),
    x_dept_id: str | None = Header(default=None),
) -> RequestContext:
    return RequestContext(user_id=x_user_id or "system", dept_id=x_dept_id or "default")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


async def get_mock_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_mock_session_factory()() as session:
        yield session
