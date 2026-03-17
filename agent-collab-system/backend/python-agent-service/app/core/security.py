from pydantic import BaseModel


class RequestContext(BaseModel):
    user_id: str = "system"
    dept_id: str = "default"
    display_name: str | None = None
    roles: list[str] = []
