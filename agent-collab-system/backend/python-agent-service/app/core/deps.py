from collections.abc import AsyncGenerator

from fastapi import Header
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import RequestContext
from app.domain.auth.token_service import token_service
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_mock_session_factory, get_session_factory


async def get_request_context(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_dept_id: str | None = Header(default=None),
    x_roles: str | None = Header(default=None),
) -> RequestContext:
    if authorization and authorization.lower().startswith('bearer '):
        token = authorization.split(' ', 1)[1].strip()
        payload = token_service.verify_token(token)
        if payload is not None:
            return RequestContext(
                user_id=payload.user_id,
                dept_id=payload.dept_id,
                display_name=payload.display_name,
                roles=list(payload.roles),
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='AUTH_INVALID_TOKEN')
    if not settings.allow_header_auth_fallback:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='AUTH_UNAUTHORIZED')
    roles = [item.strip() for item in (x_roles or "").split(",") if item.strip()]
    return RequestContext(user_id=x_user_id or "system", dept_id=x_dept_id or "default", display_name=x_user_id or None, roles=roles)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


async def get_mock_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_mock_session_factory()() as session:
        yield session
