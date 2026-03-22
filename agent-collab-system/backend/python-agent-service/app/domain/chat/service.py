from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timezone
import re
from uuid import uuid4
from typing import cast

import httpx
from sqlalchemy import select

from app.db.models.chat import ChatMessage, ChatSession
from app.db.models.workflow import WorkflowRegistry
from app.domain.chat.repository import ChatRepository
from app.domain.executions.service import ExecutionService
from app.db.session import get_mock_session_factory
from app.integrations.llm.client import LLMClient
from app.mock_records.db.models import ProductMasterRecord
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
    suggested_inputs: dict[str, object]
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
            last_message_at=self._serialize_datetime(session.last_message_at),
        )

    async def delete_session(self, session_id: str, *, dept_id: str, user_id: str) -> None:
        deleted = await self.repository.delete_session_for_actor(session_id, dept_id=dept_id, user_id=user_id)
        if not deleted:
            raise ValueError("CHAT_SESSION_NOT_FOUND")
        await self.repository.session.commit()

    async def delete_session_in_scope(self, session_id: str, *, dept_id: str | None, user_id: str, include_all: bool) -> None:
        deleted = await self.repository.delete_session_in_scope(session_id, dept_id=dept_id, user_id=user_id, include_all=include_all)
        if not deleted:
            raise ValueError("CHAT_SESSION_NOT_FOUND")
        await self.repository.session.commit()

    async def list_catalog(self, *, dept_id: str | None, category: str | None = None, include_all: bool = False, roles: list[str] | None = None) -> WorkflowCatalogResponse:
        effective_category = category or "dialog_trigger"
        entries = await self.repository.list_catalog_in_scope(dept_id=dept_id, category=effective_category, include_all=include_all)
        entries = self._dedupe_registry_entries(entries)
        entries = self._filter_entries_by_roles(entries, roles or [])
        deduped: list[WorkflowRegistry] = []
        seen_workflow_ids: set[str] = set()
        for entry in entries:
            if entry.workflow_id in seen_workflow_ids:
                continue
            seen_workflow_ids.add(entry.workflow_id)
            deduped.append(entry)
        return WorkflowCatalogResponse(items=[self._catalog_item(entry, None) for entry in deduped])

    async def route(
        self,
        payload: ChatRouteRequest,
        *,
        dept_id: str,
        user_id: str,
        roles: list[str],
    ) -> ChatRouteResponse:
        decision = await self._route_internal(payload.content, dept_id=dept_id, user_id=user_id, roles=roles, session_id=payload.session_id)
        deduped_candidates = self._dedupe_registry_entries(decision.candidates)
        return ChatRouteResponse(
            route_type=decision.route_type,
            needs_confirmation=decision.needs_confirmation,
            candidate_workflows=[self._catalog_item(entry, None) for entry in deduped_candidates],
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
        return await self._append_message_and_route_for_session(
            session,
            payload,
            dept_id=dept_id,
            user_id=user_id,
            roles=roles,
        )

    async def append_message_and_route_in_scope(
        self,
        session_id: str,
        payload: ChatMessageCreateRequest,
        *,
        dept_id: str | None,
        user_id: str,
        roles: list[str],
        include_all: bool,
    ) -> ChatMessageResponse:
        session = await self.repository.get_session_in_scope(session_id, dept_id=dept_id, user_id=user_id, include_all=include_all)
        if session is None:
            raise ValueError("CHAT_SESSION_NOT_FOUND")
        effective_dept_id = session.dept_id
        return await self._append_message_and_route_for_session(
            session,
            payload,
            dept_id=effective_dept_id,
            user_id=user_id,
            roles=roles,
        )

    async def _append_message_and_route_for_session(
        self,
        session: ChatSession,
        payload: ChatMessageCreateRequest,
        *,
        dept_id: str,
        user_id: str,
        roles: list[str],
    ) -> ChatMessageResponse:
        session_id = session.id

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
        deduped_candidates = self._dedupe_registry_entries(decision.candidates)
        assistant_payload: dict[str, object] = {
            "route_type": decision.route_type,
            "candidate_workflows": [self._catalog_item(entry, None).model_dump() for entry in deduped_candidates],
            "missing_inputs": decision.missing_inputs,
            "suggested_input_values": decision.suggested_inputs,
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
            dept_id=assistant_message.dept_id,
            created_at=self._serialize_datetime(assistant_message.created_at),
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
                    dept_id=message.dept_id,
                    created_at=self._serialize_datetime(message.created_at),
                    role=message.role,
                    content=message.content,
                    route_type=cast(str | None, (message.payload or {}).get("route_type") if message.payload else None),
                    related_execution_id=message.related_execution_id,
                    payload=message.payload,
                )
                for message in messages
            ],
        )

    async def list_messages_for_scope(self, session_id: str, *, dept_id: str | None, user_id: str, include_all: bool) -> ChatMessageListResponse:
        session = await self.repository.get_session_in_scope(session_id, dept_id=dept_id, user_id=user_id, include_all=include_all)
        if session is None:
            raise ValueError("CHAT_SESSION_NOT_FOUND")
        messages = await self.repository.list_messages(session_id)
        return ChatMessageListResponse(
            session_id=session_id,
            items=[
                ChatMessageResponse(
                    message_id=message.id,
                    session_id=message.session_id,
                    dept_id=message.dept_id,
                    created_at=self._serialize_datetime(message.created_at),
                    role=message.role,
                    content=message.content,
                    route_type=cast(str | None, (message.payload or {}).get("route_type") if message.payload else None),
                    related_execution_id=message.related_execution_id,
                    payload=message.payload,
                )
                for message in messages
            ],
        )

    async def list_sessions_in_scope(self, *, dept_id: str | None, user_id: str, include_all: bool) -> list[ChatSessionResponse]:
        sessions = await self.repository.list_sessions_in_scope(dept_id=dept_id, user_id=user_id, include_all=include_all)
        return [
            ChatSessionResponse(
                session_id=item.id,
                title=item.title or "新会话",
                dept_id=item.dept_id,
                last_message_at=self._serialize_datetime(item.last_message_at),
            )
            for item in sessions
        ]

    @staticmethod
    def _serialize_datetime(value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat()

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
        return await self._start_workflow_for_session(
            session,
            workflow_id,
            payload,
            dept_id=dept_id,
            user_id=user_id,
            roles=roles,
        )

    async def start_workflow_from_selection_in_scope(
        self,
        session_id: str,
        workflow_id: str,
        payload: ChatWorkflowStartRequest,
        *,
        dept_id: str | None,
        user_id: str,
        roles: list[str],
        include_all: bool,
    ) -> ChatMessageResponse:
        session = await self.repository.get_session_in_scope(session_id, dept_id=dept_id, user_id=user_id, include_all=include_all)
        if session is None:
            raise ValueError("CHAT_SESSION_NOT_FOUND")
        effective_dept_id = session.dept_id
        return await self._start_workflow_for_session(
            session,
            workflow_id,
            payload,
            dept_id=effective_dept_id,
            user_id=user_id,
            roles=roles,
        )

    async def _start_workflow_for_session(
        self,
        session: ChatSession,
        workflow_id: str,
        payload: ChatWorkflowStartRequest,
        *,
        dept_id: str,
        user_id: str,
        roles: list[str],
    ) -> ChatMessageResponse:
        session_id = session.id

        entries = self._filter_entries_by_roles(
            self._dedupe_registry_entries(await self.repository.list_catalog(dept_id, category="dialog_trigger")),
            roles,
        )
        selected = next((entry for entry in entries if entry.workflow_id == workflow_id), None)
        if selected is None:
            raise ValueError("WORKFLOW_NOT_FOUND")

        merged_input_values = await self._merge_input_values_from_source_message(
            payload.input_values or {},
            payload.source_message_id,
        )
        missing_inputs = self._missing_required_inputs(selected, merged_input_values)
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
                    "suggested_input_values": merged_input_values,
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
                created_at=assistant_message.created_at.isoformat() if assistant_message.created_at else None,
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
                    "input_values": merged_input_values,
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
                "input_values": merged_input_values,
            },
            related_execution_id=execution.execution_id,
        )
        _ = await self.repository.create_message(assistant_message)
        await self.repository.touch_session(session_id, last_message_at=datetime.now(timezone.utc))
        await self.repository.session.commit()
        return ChatMessageResponse(
            message_id=assistant_message.id,
            session_id=session_id,
            created_at=assistant_message.created_at.isoformat() if assistant_message.created_at else None,
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
                suggested_inputs={},
            )

        entries = self._dedupe_registry_entries(await self.repository.list_catalog(dept_id, category="dialog_trigger"))
        entries = self._filter_entries_by_roles(entries, roles)
        scored = self._score_candidates(normalized, entries)
        command_keywords = ("启动", "执行", "发起", "运行", "触发", "录入", "登记")
        question_hints = ("什么", "怎么", "为何", "为什么", "吗", "？", "?")
        is_question_like = any(keyword in normalized for keyword in question_hints)
        is_command_like = (any(keyword in normalized for keyword in command_keywords) or any(score >= 2 for _, score in scored)) and not is_question_like
        if is_command_like and scored:
            top_score = scored[0][1]
            top_entries = [entry for entry, score in scored if score == top_score and score > 0]
            if len(top_entries) == 1:
                chosen = top_entries[0]
                suggested_inputs = await self._extract_structured_inputs(chosen, normalized)
                missing_inputs = self._missing_required_inputs(chosen, suggested_inputs)
                if missing_inputs:
                    return RouteDecision(
                        route_type="command",
                        candidates=[chosen],
                        needs_confirmation=True,
                        reply=self._build_input_prompt(chosen, missing_inputs),
                        missing_inputs=missing_inputs,
                        suggested_inputs=suggested_inputs,
                    )
                execution = await self.execution_service.start(
                    ExecutionStartRequest(
                        workflow_id=chosen.workflow_id,
                        version=chosen.workflow_version,
                        mode="released",
                        trigger=ExecutionTrigger(type="chat", session_id=session_id, message_id=None),
                        dept_id=dept_id,
                        operator=ExecutionOperator(user_id=user_id, roles=roles),
                        input={"message": normalized, "input_values": suggested_inputs},
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
                    suggested_inputs=suggested_inputs,
                    execution_id=execution.execution_id,
                )

            if top_entries:
                return RouteDecision(
                    route_type="command",
                    candidates=top_entries,
                    needs_confirmation=True,
                    reply="我找到了多个候选 workflow，请在右侧目录确认你要启动哪一个。",
                    missing_inputs=[],
                    suggested_inputs={},
                )

        if is_command_like and len(entries) == 1:
            chosen = entries[0]
            suggested_inputs = await self._extract_structured_inputs(chosen, normalized)
            missing_inputs = self._missing_required_inputs(chosen, suggested_inputs)
            if missing_inputs:
                return RouteDecision(
                    route_type="command",
                    candidates=[chosen],
                    needs_confirmation=True,
                    reply=self._build_input_prompt(chosen, missing_inputs),
                    missing_inputs=missing_inputs,
                    suggested_inputs=suggested_inputs,
                )
            execution = await self.execution_service.start(
                ExecutionStartRequest(
                    workflow_id=chosen.workflow_id,
                    version=chosen.workflow_version,
                    mode="released",
                    trigger=ExecutionTrigger(type="chat", session_id=session_id, message_id=None),
                    dept_id=dept_id,
                    operator=ExecutionOperator(user_id=user_id, roles=roles),
                    input={"message": normalized, "input_values": suggested_inputs},
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
                suggested_inputs=suggested_inputs,
                execution_id=execution.execution_id,
            )

        return RouteDecision(
            route_type="ask",
            candidates=[],
            needs_confirmation=False,
            reply=await self._build_ask_reply(normalized, session_id=session_id, dept_id=dept_id),
            missing_inputs=[],
            suggested_inputs={},
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
        normalized_content = content.strip().lower()
        scored: list[tuple[WorkflowRegistry, int]] = []
        for entry in entries:
            haystacks = [entry.title, entry.summary]
            if entry.synonyms:
                haystacks.extend(entry.synonyms)
            if entry.example_utterances:
                haystacks.extend(entry.example_utterances)
            score = 0
            for token in tokens:
                if any(token in item for item in haystacks):
                    score += 1
            for item in haystacks:
                normalized_item = item.strip().lower()
                if normalized_item and (normalized_item in normalized_content or normalized_content in normalized_item):
                    score += 1
            if entry.title in content:
                score += 2
            if entry.example_utterances and any(example and example in content for example in entry.example_utterances):
                score += 3
            if score > 0:
                scored.append((entry, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    @staticmethod
    def _filter_entries_by_roles(entries: list[WorkflowRegistry], roles: list[str]) -> list[WorkflowRegistry]:
        role_set = {role.strip() for role in roles if role.strip()}
        filtered: list[WorkflowRegistry] = []
        for entry in entries:
            if not entry.allowed_roles:
                filtered.append(entry)
                continue
            allowed = {role.strip() for role in entry.allowed_roles if isinstance(role, str) and role.strip()}
            if not allowed or allowed.intersection(role_set):
                filtered.append(entry)
        return filtered

    @staticmethod
    def _dedupe_registry_entries(entries: list[WorkflowRegistry]) -> list[WorkflowRegistry]:
        deduped: list[WorkflowRegistry] = []
        seen_workflow_ids: set[str] = set()
        sorted_entries = sorted(entries, key=lambda item: (item.workflow_version, item.updated_at), reverse=True)
        for entry in sorted_entries:
            if entry.workflow_id in seen_workflow_ids:
                continue
            seen_workflow_ids.add(entry.workflow_id)
            deduped.append(entry)
        return deduped

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

    async def _merge_input_values_from_source_message(
        self,
        input_values: dict[str, object],
        source_message_id: str | None,
    ) -> dict[str, object]:
        merged = dict(input_values)
        if not source_message_id:
            return merged
        source_message = await self.repository.get_message(source_message_id)
        if source_message is None or not isinstance(source_message.payload, dict):
            return merged
        suggested = source_message.payload.get("suggested_input_values")
        if not isinstance(suggested, dict):
            return merged
        return {**cast(dict[str, object], suggested), **merged}

    async def _extract_structured_inputs(self, entry: WorkflowRegistry, content: str) -> dict[str, object]:
        required = set(entry.required_inputs or [])
        sales_order_required = {"order_no", "customer_name", "product_code", "product_name", "ordered_qty", "unit_price"}
        if not required.intersection(sales_order_required):
            return {}

        extracted = await self._extract_sales_order_inputs(content)
        return {key: value for key, value in extracted.items() if key in required or key == "order_status"}

    async def _extract_sales_order_inputs(self, content: str) -> dict[str, object]:
        normalized = content.strip()
        extracted: dict[str, object] = {}

        order_match = re.search(r"(?:订单号|单号|order\s*no\.?)[：:\s]*([A-Za-z0-9_-]{4,64})", normalized, re.IGNORECASE)
        if order_match:
            extracted["order_no"] = order_match.group(1).strip()
        else:
            so_match = re.search(r"\bSO-[A-Za-z0-9_-]{4,64}\b", normalized, re.IGNORECASE)
            if so_match:
                extracted["order_no"] = so_match.group(0).strip()

        customer_patterns = [
            r"客户[：:\s]*([^，。,；;\n]+?)(?:下单|订购|采购|，|。|；|;|$)",
            r"([^，。,；;\n]+?)下单",
            r"([^，。,；;\n]+?)订购",
        ]
        for pattern in customer_patterns:
            customer_match = re.search(pattern, normalized)
            if customer_match:
                customer_name = customer_match.group(1).strip()
                if customer_name and len(customer_name) <= 64:
                    extracted["customer_name"] = customer_name
                    break

        quantity_match = re.search(r"(\d+)\s*(?:台|个|套|部|件)", normalized)
        if quantity_match:
            extracted["ordered_qty"] = int(quantity_match.group(1))
        else:
            generic_quantity = re.search(r"数量[：:\s]*(\d+)", normalized)
            if generic_quantity:
                extracted["ordered_qty"] = int(generic_quantity.group(1))

        price_match = re.search(r"(?:单价|价格|金额)[：:\s]*([0-9]+(?:\.[0-9]+)?)", normalized)
        if price_match:
            extracted["unit_price"] = float(price_match.group(1))

        product_catalog = await self._load_product_catalog()
        lowered = normalized.lower()
        matched_product = next(
            (
                item
                for item in product_catalog
                if str(item["product_code"]).lower() in lowered
                or str(item["product_name"]).lower() in lowered
                or any(alias in lowered for alias in cast(list[str], item.get("aliases") or []))
            ),
            None,
        )
        if matched_product is not None:
            extracted["product_code"] = matched_product["product_code"]
            extracted["product_name"] = matched_product["product_name"]
            if extracted.get("unit_price") in {None, 0, 0.0}:
                extracted["unit_price"] = matched_product["unit_price"]

        if extracted:
            extracted.setdefault("order_status", "draft")
        return extracted

    async def _load_product_catalog(self) -> list[dict[str, object]]:
        async with get_mock_session_factory()() as session:
            result = await session.execute(select(ProductMasterRecord).order_by(ProductMasterRecord.updated_at.desc()))
            items = list(result.scalars().all())
        catalog: list[dict[str, object]] = []
        for item in items:
            aliases: list[str] = []
            product_name = item.product_name.lower()
            product_code = item.product_code.lower()
            aliases.append(product_code)
            aliases.append(product_name)
            if "苹果手机" in product_name or "phone" in product_code:
                aliases.extend(["苹果手机", "iphone", "手机"])
            if "平板" in product_name or "pad" in product_code:
                aliases.extend(["平板", "pad", "平板电脑"])
            catalog.append(
                {
                    "product_code": item.product_code,
                    "product_name": item.product_name,
                    "unit_price": item.unit_price,
                    "aliases": aliases,
                }
            )
        return catalog
