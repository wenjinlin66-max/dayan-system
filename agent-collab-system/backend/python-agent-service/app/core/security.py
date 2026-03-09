from pydantic import BaseModel


class RequestContext(BaseModel):
    user_id: str = "system"
    dept_id: str = "default"
    roles: list[str] = []
