from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_request_context
from app.core.security import RequestContext
from app.domain.chat.repository import ChatRepository
from app.domain.chat.service import ChatService
from app.domain.executions.repository import ExecutionRepository
from app.domain.executions.service import ExecutionService
from app.domain.workflows.repository import WorkflowRepository
from app.integrations.llm.client import LLMClient
from app.schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageListResponse,
    ChatMessageResponse,
    ChatRouteRequest,
    ChatRouteResponse,
    ChatSessionCreateRequest,
    ChatSessionResponse,
    ChatWorkflowStartRequest,
    WorkflowCatalogResponse,
)

router = APIRouter()


def build_service(session: AsyncSession) -> ChatService:
    chat_repository = ChatRepository(session)
    execution_service = ExecutionService(ExecutionRepository(session), WorkflowRepository(session))
    return ChatService(chat_repository, execution_service, LLMClient.from_settings())


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: ChatSessionCreateRequest,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ChatSessionResponse:
    service = build_service(session)
    return await service.create_session(payload, dept_id=context.dept_id, user_id=context.user_id)


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[ChatSessionResponse]:
    repository = ChatRepository(session)
    items = await repository.list_sessions(context.dept_id, context.user_id)
    return [
        ChatSessionResponse(
            session_id=item.id,
            title=item.title or "新会话",
            dept_id=item.dept_id,
            last_message_at=item.last_message_at.isoformat() if item.last_message_at else None,
        )
        for item in items
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = build_service(session)
    try:
        await service.delete_session(session_id, dept_id=context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResponse)
async def send_message(
    session_id: str,
    payload: ChatMessageCreateRequest,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ChatMessageResponse:
    service = build_service(session)
    try:
        return await service.append_message_and_route(
            session_id,
            payload,
            dept_id=context.dept_id,
            user_id=context.user_id,
            roles=context.roles,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/sessions/{session_id}/messages", response_model=ChatMessageListResponse)
async def list_messages(
    session_id: str,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ChatMessageListResponse:
    service = build_service(session)
    try:
        return await service.list_messages_for_actor(session_id, dept_id=context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/workflows/catalog", response_model=WorkflowCatalogResponse)
async def get_workflow_catalog(
    category: str | None = Query(default=None),
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowCatalogResponse:
    service = build_service(session)
    return await service.list_catalog(dept_id=context.dept_id, category=category)


@router.post("/route", response_model=ChatRouteResponse)
async def route_message(
    payload: ChatRouteRequest,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ChatRouteResponse:
    service = build_service(session)
    return await service.route(payload, dept_id=context.dept_id, user_id=context.user_id, roles=context.roles)


@router.post("/sessions/{session_id}/workflows/{workflow_id}/start", response_model=ChatMessageResponse)
async def start_workflow_from_chat(
    session_id: str,
    workflow_id: str,
    payload: ChatWorkflowStartRequest,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ChatMessageResponse:
    service = build_service(session)
    try:
        return await service.start_workflow_from_selection(
            session_id,
            workflow_id,
            payload,
            dept_id=context.dept_id,
            user_id=context.user_id,
            roles=context.roles,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
