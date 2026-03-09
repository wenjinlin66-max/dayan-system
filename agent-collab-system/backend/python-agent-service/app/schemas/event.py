from pydantic import BaseModel


class EventActor(BaseModel):
    user_id: str | None = None
    roles: list[str] = []
    scopes: list[str] = []


class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    event_version: int = 1
    source: str
    occurred_at: str
    dept_id: str
    tenant_id: str | None = None
    actor: EventActor | None = None
    payload: dict[str, object] = {}
