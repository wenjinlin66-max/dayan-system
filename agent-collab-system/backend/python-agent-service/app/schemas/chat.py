from pydantic import BaseModel


class ChatSessionCreateRequest(BaseModel):
    title: str | None = None


class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
