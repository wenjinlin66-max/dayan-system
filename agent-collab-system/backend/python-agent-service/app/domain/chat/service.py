from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4
from typing import cast

import httpx

from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.workflow import WorkflowRegistry
from app.domain.chat.repository import ChatRepository
from app.domain.executions.service import ExecutionService
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
    WorkflowCatalogItem,
    WorkflowCatalogResponse,
)
from app.schemas.execution import ExecutionOperator, ExecutionStartRequest, ExecutionTrigger


@dataclass(slots=True)
class RouteDecision:
    route_type: str
    candidates: list[WorkflowRegistry]
    needs_confirmation: bool
    reply: str
    missing_inputs: list[str]
    execution_id: str | None = None


class ChatService:
    repository: ChatRepository
    execution_service: ExecutionService
    llm_client: LLMClient

    def __init__(self, repository: ChatRepository, execution_service: ExecutionService, llm_client: LLMClient) -> None:
        self.repository = repository
        self.execution_service = execution_service
        self.llm_client = llm_client

    async def create_session(self, payload: ChatSessionCreateRequest, *, dept_id: str, user_id: str) -> ChatSessionResponse:
        session = ChatSession(
            id=f"chat_{uuid4().hex[:12]}",
            dept_id=dept_id,
            user_id=user_id,
            title=payload.title or "新会话",
            status="active",
            last_message_at=datetime.now(timezone.utc),
        )
        _ = await self.repository.create_session(session)
        await self.repository.session.commit()
        return ChatSessionResponse(
            session_id=session.id,
            title=session.title or "新会话",
            dept_id=session.dept_id,
            last_message_at=session.last_message_at.isoformat() if session.last_message_at else None,
        )

    async def delete_session(self, session_id: str, *, dept_id: str, user_id: str) -> None:
        deleted = await self.repository.delete_session_for_actor(session_id, dept_id=dept_id, user_id=user_id)
        if not deleted:
            raise ValueError("CHAT_SESSION_NOT_FOUND")
        await self.repository.session.commit()

    async def list_catalog(self, *, dept_id: str, category: str | None = None) -> WorkflowCatalogResponse:
        entries = await self.repository.list_catalog(dept_id, category)
        return WorkflowCatalogResponse(items=[self._catalog_item(entry, None) for entry in entries])

    async def route(
        self,
        payload: ChatRouteRequest,
        *,
        dept_id: str,
        user_id: str,
        roles: list[str],
    ) -> ChatRouteResponse:
        decision = await self._route_internal(payload.content, dept_id=dept_id, user_id=user_id, roles=roles, session_id=payload.session_id)
        return ChatRouteResponse(
            route_type=decision.route_type,
            needs_confirmation=decision.needs_confirmation,
            candidate_workflows=[self._catalog_item(entry, None) for entry in decision.candidates],
            missing_inputs=decision.missing_inputs,
            execution_id=decision.execution_id,
            reply=decision.reply,
        )

    async def append_message_and_route(
        self,
        session_id: str,
        payload: ChatMessageCreateRequest,
        *,
        dept_id: str,
        user_id: str,
        roles: list[str],
    ) -> ChatMessageResponse:
        session = await self.repository.get_session_for_actor(session_id, dept_id, user_id)
        if session is None:
            raise ValueError("CHAT_SESSION_NOT_FOUND")

        user_message = ChatMessage(
            id=f"msg_{uuid4().hex[:12]}",
            session_id=session_id,
            dept_id=dept_id,
            role="user",
            message_type=payload.message_type,
            content=payload.content,
            payload=None,
            related_execution_id=None,
        )
        _ = await self.repository.create_message(user_message)

        decision = await self._route_internal(payload.content, dept_id=dept_id, user_id=user_id, roles=roles, session_id=session_id)
        assistant_payload: dict[str, object] = {
            "route_type": decision.route_type,
            "candidate_workflows": [self._catalog_item(entry, None).model_dump() for entry in decision.candidates],
            "missing_inputs": decision.missing_inputs,
        }
        assistant_message = ChatMessage(
            id=f"msg_{uuid4().hex[:12]}",
            session_id=session_id,
            dept_id=dept_id,
            role="assistant",
            message_type="text",
            content=decision.reply,
            payload=assistant_payload,
            related_execution_id=decision.execution_id,
        )
        _ = await self.repository.create_message(assistant_message)
        await self.repository.touch_session(session_id, last_message_at=datetime.now(timezone.utc))
        await self.repository.session.commit()
        return ChatMessageResponse(
            message_id=assistant_message.id,
            session_id=session_id,
            role=assistant_message.role,
            content=assistant_message.content,
            route_type=decision.route_type,
            related_execution_id=decision.execution_id,
            payload=assistant_message.payload,
        )

    async def list_messages(self, session_id: str) -> ChatMessageListResponse:
        messages = await self.repository.list_messages(session_id)
        return ChatMessageListResponse(
            session_id=session_id,
            items=[
                ChatMessageResponse(
                    message_id=message.id,
                    session_id=message.session_id,
                    role=message.role,
                    content=message.content,
                    route_type=cast(str | None, (message.payload or {}).get("route_type") if message.payload else None),
                    related_execution_id=message.related_execution_id,
                    payload=message.payload,
                )
                for message in messages
            ],
        )

    async def list_messages_for_actor(self, session_id: str, *, dept_id: str, user_id: str) -> ChatMessageListResponse:
        session = await self.repository.get_session_for_actor(session_id, dept_id, user_id)
        if session is None:
            raise ValueError("CHAT_SESSION_NOT_FOUND")
        messages = await self.repository.list_messages(session_id)
        return ChatMessageListResponse(
            session_id=session_id,
            items=[
                ChatMessageResponse(
                    message_id=message.id,
                    session_id=message.session_id,
                    role=message.role,
                    content=message.content,
                    route_type=cast(str | None, (message.payload or {}).get("route_type") if message.payload else None),
                    related_execution_id=message.related_execution_id,
                    payload=message.payload,
                )
                for message in messages
            ],
        )

    async def start_workflow_from_selection(
        self,
        session_id: str,
        workflow_id: str,
        payload: ChatWorkflowStartRequest,
        *,
        dept_id: str,
        user_id: str,
        roles: list[str],
    ) -> ChatMessageResponse:
        session = await self.repository.get_session_for_actor(session_id, dept_id, user_id)
        if session is None:
            raise ValueError("CHAT_SESSION_NOT_FOUND")

        entries = await self.repository.list_catalog(dept_id)
        selected = next((entry for entry in entries if entry.workflow_id == workflow_id), None)
        if selected is None:
            raise ValueError("WORKFLOW_NOT_FOUND")

        missing_inputs = self._missing_required_inputs(selected, payload.input_values)
        if missing_inputs:
            assistant_message = ChatMessage(
                id=f"msg_{uuid4().hex[:12]}",
                session_id=session_id,
                dept_id=dept_id,
                role="assistant",
                message_type="text",
                content=self._build_input_prompt(selected, missing_inputs),
                payload={
                    "route_type": "command",
                    "candidate_workflows": [self._catalog_item(selected, 1.0).model_dump()],
                    "missing_inputs": missing_inputs,
                    "source": payload.source,
                    "source_message_id": payload.source_message_id,
                },
                related_execution_id=None,
            )
            _ = await self.repository.create_message(assistant_message)
            await self.repository.touch_session(session_id, last_message_at=datetime.now(timezone.utc))
            await self.repository.session.commit()
            return ChatMessageResponse(
                message_id=assistant_message.id,
                session_id=session_id,
                role=assistant_message.role,
                content=assistant_message.content,
                route_type="command",
                related_execution_id=None,
                payload=assistant_message.payload,
            )

        user_note = payload.note or f"选择启动工作流：{selected.title}"
        user_message = ChatMessage(
            id=f"msg_{uuid4().hex[:12]}",
            session_id=session_id,
            dept_id=dept_id,
            role="user",
            message_type="workflow_start",
            content=user_note,
            payload={"source": payload.source, "workflow_id": workflow_id, "source_message_id": payload.source_message_id},
            related_execution_id=None,
        )
        _ = await self.repository.create_message(user_message)

        execution = await self.execution_service.start(
            ExecutionStartRequest(
                workflow_id=selected.workflow_id,
                version=selected.workflow_version,
                mode="released",
                trigger=ExecutionTrigger(type="chat", session_id=session_id, message_id=user_message.id),
                dept_id=dept_id,
                operator=ExecutionOperator(user_id=user_id, roles=roles),
                input={
                    "message": user_note,
                    "source": payload.source,
                    "input_values": payload.input_values or {},
                },
            ),
            dept_id=dept_id,
            user_id=user_id,
        )

        assistant_message = ChatMessage(
            id=f"msg_{uuid4().hex[:12]}",
            session_id=session_id,
            dept_id=dept_id,
            role="assistant",
            message_type="text",
            content=f"已根据你的选择启动工作流《{selected.title}》，execution_id={execution.execution_id}。",
            payload={
                "route_type": "command",
                "workflow": self._catalog_item(selected, 1.0).model_dump(),
                "input_values": payload.input_values or {},
            },
            related_execution_id=execution.execution_id,
        )
        _ = await self.repository.create_message(assistant_message)
        await self.repository.touch_session(session_id, last_message_at=datetime.now(timezone.utc))
        await self.repository.session.commit()
        return ChatMessageResponse(
            message_id=assistant_message.id,
            session_id=session_id,
            role=assistant_message.role,
            content=assistant_message.content,
            route_type="command",
            related_execution_id=assistant_message.related_execution_id,
            payload=assistant_message.payload,
        )

    async def _route_internal(
        self,
        content: str,
        *,
        dept_id: str,
        user_id: str,
        roles: list[str],
        session_id: str | None,
    ) -> RouteDecision:
        normalized = content.strip()
        if any(token in normalized for token in ("同意", "批准", "驳回", "拒绝")):
            return RouteDecision(
                route_type="approve",
                candidates=[],
                needs_confirmation=False,
                reply="已识别为审批操作，后续接入审批恢复主链。",
                missing_inputs=[],
            )

        entries = await self.repository.list_catalog(dept_id)
        scored = self._score_candidates(normalized, entries)
        command_keywords = ("启动", "执行", "发起", "运行", "触发", "帮我")
        is_command_like = any(keyword in normalized for keyword in command_keywords)
        if is_command_like and scored:
            top_score = scored[0][1]
            top_entries = [entry for entry, score in scored if score == top_score and score > 0]
            if len(top_entries) == 1:
                chosen = top_entries[0]
                missing_inputs = self._missing_required_inputs(chosen, None)
                if missing_inputs:
                    return RouteDecision(
                        route_type="command",
                        candidates=[chosen],
                        needs_confirmation=True,
                        reply=self._build_input_prompt(chosen, missing_inputs),
                        missing_inputs=missing_inputs,
                    )
                execution = await self.execution_service.start(
                    ExecutionStartRequest(
                        workflow_id=chosen.workflow_id,
                        version=chosen.workflow_version,
                        mode="released",
                        trigger=ExecutionTrigger(type="chat", session_id=session_id, message_id=None),
                        dept_id=dept_id,
                        operator=ExecutionOperator(user_id=user_id, roles=roles),
                        input={"message": normalized},
                    ),
                    dept_id=dept_id,
                    user_id=user_id,
                )
                reply = f"已为你启动工作流《{chosen.title}》，execution_id={execution.execution_id}。"
                return RouteDecision(
                    route_type="command",
                    candidates=[chosen],
                    needs_confirmation=False,
                    reply=reply,
                    missing_inputs=[],
                    execution_id=execution.execution_id,
                )

            if top_entries:
                return RouteDecision(
                    route_type="command",
                    candidates=top_entries,
                    needs_confirmation=True,
                    reply="我找到了多个候选 workflow，请在右侧目录确认你要启动哪一个。",
                    missing_inputs=[],
                )

        if is_command_like and len(entries) == 1:
            chosen = entries[0]
            missing_inputs = self._missing_required_inputs(chosen, None)
            if missing_inputs:
                return RouteDecision(
                    route_type="command",
                    candidates=[chosen],
                    needs_confirmation=True,
                    reply=self._build_input_prompt(chosen, missing_inputs),
                    missing_inputs=missing_inputs,
                )
            execution = await self.execution_service.start(
                ExecutionStartRequest(
                    workflow_id=chosen.workflow_id,
                    version=chosen.workflow_version,
                    mode="released",
                    trigger=ExecutionTrigger(type="chat", session_id=session_id, message_id=None),
                    dept_id=dept_id,
                    operator=ExecutionOperator(user_id=user_id, roles=roles),
                    input={"message": normalized},
                ),
                dept_id=dept_id,
                user_id=user_id,
            )
            reply = f"已为你启动工作流《{chosen.title}》，execution_id={execution.execution_id}。"
            return RouteDecision(
                route_type="command",
                candidates=[chosen],
                needs_confirmation=False,
                reply=reply,
                missing_inputs=[],
                execution_id=execution.execution_id,
            )

        return RouteDecision(
            route_type="ask",
            candidates=[],
            needs_confirmation=False,
            reply=await self._build_ask_reply(normalized, session_id=session_id, dept_id=dept_id),
            missing_inputs=[],
        )

    async def _build_ask_reply(self, content: str, *, session_id: str | None, dept_id: str) -> str:
        prompt_messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "你是大衍系统中的部门 AI 助手。你的主要职责是回答用户问题、解释当前部门工作流能力、"
                    "在不确定时说明边界，使用简洁中文回答，不要编造不存在的数据。"
                ),
            }
        ]

        if session_id:
            history = await self.repository.list_messages(session_id)
            for message in history[-10:]:
                if message.role not in {"user", "assistant"}:
                    continue
                prompt_messages.append({
                    "role": str(message.role),
                    "content": str(message.content),
                })
        else:
            prompt_messages.append({"role": "user", "content": content})

        try:
            reply = await self.llm_client.chat(messages=prompt_messages)
            return reply
        except (httpx.HTTPError, RuntimeError) as exc:
            fallback = (
                f"当前已识别为{dept_id}部门对话问答，但模型服务暂不可用。"
                f"你可以继续描述你的目标，我会先按部门流程与审批能力为你组织下一步。"
            )
            if str(exc) == "LLM_NOT_CONFIGURED":
                return fallback
            return f"{fallback}（模型网关返回异常：{exc}）"

    @staticmethod
    def _missing_required_inputs(
        entry: WorkflowRegistry,
        provided_inputs: dict[str, object] | None,
    ) -> list[str]:
        required = entry.required_inputs or []
        if not required:
            return []
        values = provided_inputs or {}
        missing: list[str] = []
        for field in required:
            value = values.get(field)
            if value is None:
                missing.append(field)
                continue
            if isinstance(value, str) and not value.strip():
                missing.append(field)
        return missing

    @staticmethod
    def _build_input_prompt(entry: WorkflowRegistry, missing_inputs: list[str]) -> str:
        fields = "、".join(missing_inputs)
        return f"启动《{entry.title}》前，还需要你补充这些参数：{fields}。填写后我会继续启动执行。"

    @staticmethod
    def _score_candidates(content: str, entries: list[WorkflowRegistry]) -> list[tuple[WorkflowRegistry, int]]:
        tokens = [token for token in content.replace("，", " ").replace("。", " ").split() if token]
        scored: list[tuple[WorkflowRegistry, int]] = []
        for entry in entries:
            haystacks = [entry.title, entry.summary]
            if entry.synonyms:
                haystacks.extend(entry.synonyms)
            score = 0
            for token in tokens:
                if any(token in item for item in haystacks):
                    score += 1
            if not tokens and any(keyword in content for keyword in (entry.title, entry.summary)):
                score += 1
            if entry.title in content:
                score += 2
            if score > 0:
                scored.append((entry, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    @staticmethod
    def _catalog_item(entry: WorkflowRegistry, confidence: float | None) -> WorkflowCatalogItem:
        return WorkflowCatalogItem(
            workflow_id=entry.workflow_id,
            title=entry.title,
            category=entry.category,
            summary=entry.summary,
            dept_id=entry.dept_id,
            confidence=confidence,
            required_inputs=list(entry.required_inputs or []),
            input_schema=entry.input_schema,
        )
