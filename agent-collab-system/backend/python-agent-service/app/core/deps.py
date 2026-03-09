from fastapi import Header

from app.core.security import RequestContext


async def get_request_context(
    x_user_id: str | None = Header(default=None),
    x_dept_id: str | None = Header(default=None),
) -> RequestContext:
    return RequestContext(user_id=x_user_id or "system", dept_id=x_dept_id or "default")
