from fastapi import APIRouter

from app.schemas.chat import ChatSessionCreateRequest, ChatSessionResponse

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(payload: ChatSessionCreateRequest) -> ChatSessionResponse:
    return ChatSessionResponse(session_id="chat_placeholder", title=payload.title or "新会话")
