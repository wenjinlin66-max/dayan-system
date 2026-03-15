from __future__ import annotations

from datetime import datetime
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.workflow import WorkflowRegistry


class ChatRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_session(self, chat_session: ChatSession) -> ChatSession:
        self.session.add(chat_session)
        await self.session.flush()
        return chat_session

    async def get_session(self, session_id: str) -> ChatSession | None:
        result = await self.session.execute(select(ChatSession).where(ChatSession.id == session_id))
        return result.scalar_one_or_none()

    async def get_session_for_actor(self, session_id: str, dept_id: str, user_id: str) -> ChatSession | None:
        result = await self.session.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.dept_id == dept_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(self, dept_id: str, user_id: str) -> list[ChatSession]:
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.dept_id == dept_id, ChatSession.user_id == user_id)
            .order_by(ChatSession.last_message_at.desc().nullslast(), ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_message(self, message: ChatMessage) -> ChatMessage:
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_messages(self, session_id: str) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def delete_session_for_actor(self, session_id: str, *, dept_id: str, user_id: str) -> bool:
        session = await self.get_session_for_actor(session_id, dept_id, user_id)
        if session is None:
            return False
        _ = await self.session.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
        _ = await self.session.execute(delete(ChatSession).where(ChatSession.id == session_id))
        return True

    async def touch_session(self, session_id: str, *, last_message_at: datetime) -> None:
        _ = await self.session.execute(
            update(ChatSession).where(ChatSession.id == session_id).values(last_message_at=last_message_at)
        )

    async def append_assistant_message(
        self,
        *,
        session_id: str,
        dept_id: str,
        content: str,
        payload: dict[str, object] | None = None,
        related_execution_id: str | None = None,
        message_type: str = "system_notice",
    ) -> ChatMessage:
        message = ChatMessage(
            id=f"msg_{uuid4().hex[:12]}",
            session_id=session_id,
            dept_id=dept_id,
            role="assistant",
            message_type=message_type,
            content=content,
            payload=payload,
            related_execution_id=related_execution_id,
        )
        self.session.add(message)
        await self.session.flush()
        await self.touch_session(session_id, last_message_at=datetime.now(UTC))
        return message

    async def list_catalog(self, dept_id: str, category: str | None = None) -> list[WorkflowRegistry]:
        stmt = select(WorkflowRegistry).where(WorkflowRegistry.dept_id == dept_id, WorkflowRegistry.status == "active")
        if category and category != "all":
            stmt = stmt.where(WorkflowRegistry.category == category)
        result = await self.session.execute(stmt.order_by(WorkflowRegistry.updated_at.desc()))
        return list(result.scalars().all())
