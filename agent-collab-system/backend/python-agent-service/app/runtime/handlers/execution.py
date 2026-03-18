from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Final
from string import Template
import json
from typing import Protocol, cast
from uuid import uuid4

import httpx

from app.db.models.approval import ApprovalTask
from app.domain.approvals.repository import ApprovalRepository
from app.domain.chat.repository import ChatRepository
from app.integrations.llm.client import LLMClient
from app.runtime.models import JsonValue, NodeExecutionResult, RuntimeNode, RuntimeState

JsonScalar = str | int | float | bool | None
StringMap = dict[str, str]


class DepartmentTableWriter(Protocol):
    async def write_row(self, payload: dict[str, JsonValue]) -> dict[str, JsonValue]: ...


@dataclass(slots=True)
class ExecutionContext:
    execution_id: str
    workflow_id: str
    workflow_version: int
    node_id: str
    dept_id: str
    operator_id: str
    trace_id: str | None = None
    decision_payload: dict[str, JsonValue] | None = None
    risk_level: str | None = None
    decision_summary: str | None = None
    decision_explanation: str | None = None
    recommended_actions: list[dict[str, JsonValue]] | None = None


SUPPORTED_OPERATIONS: Final[set[str]] = {"append_row", "upsert_row", "update_row"}


class ExecutionNodeHandler:
    department_table_writer: DepartmentTableWriter
    llm_client: LLMClient
    approval_repository: ApprovalRepository | None

    def __init__(
        self,
        department_table_writer: DepartmentTableWriter,
        llm_client: LLMClient | None = None,
        approval_repository: ApprovalRepository | None = None,
    ) -> None:
        self.department_table_writer = department_table_writer
        self.llm_client = llm_client or LLMClient.from_settings()
        self.approval_repository = approval_repository

    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        decision_output = next(reversed(state.decision_outputs.values()), None)
        context = ExecutionContext(
            execution_id=state.execution_id,
            workflow_id=state.workflow_id,
            workflow_version=state.workflow_version,
            node_id=node.id,
            dept_id=state.dept_id,
            operator_id=str(state.context.get("operator_id") or "system"),
            decision_payload=(
                cast(dict[str, JsonValue], decision_output.get("decision_payload"))
                if isinstance(decision_output, dict) and isinstance(decision_output.get("decision_payload"), dict)
                else cast(dict[str, JsonValue], state.input_payload.get("input_values"))
                if isinstance(state.input_payload.get("input_values"), dict)
                else None
            ),
            risk_level=(
                str(decision_output.get("risk_level"))
                if isinstance(decision_output, dict) and decision_output.get("risk_level") is not None
                else None
            ),
            decision_summary=(
                str(decision_output.get("decision_summary"))
                if isinstance(decision_output, dict) and decision_output.get("decision_summary") is not None
                else None
            ),
            decision_explanation=(
                str(decision_output.get("explanation"))
                if isinstance(decision_output, dict) and decision_output.get("explanation") is not None
                else None
            ),
            recommended_actions=(
                [cast(dict[str, JsonValue], item) for item in cast(list[object], decision_output.get("recommended_actions")) if isinstance(item, dict)]
                if isinstance(decision_output, dict) and isinstance(decision_output.get("recommended_actions"), list)
                else None
            ),
        )

        if self._should_pause_for_approval(node.config, state, context):
            if self.approval_repository is None:
                raise ValueError("APPROVAL_REPOSITORY_NOT_CONFIGURED")
            next_node = next_nodes[0] if next_nodes else None
            await self._create_execution_approval(node, state, next_node)
            return NodeExecutionResult(next_node_id=node.id, pause_execution=True, pause_reason="approval_pending")

        self._clear_execution_approval_context(node.id, state)
        execution_result = await self.run_config(node.config, context)
        state.tool_outputs[node.id] = cast(dict[str, object], execution_result)
        return NodeExecutionResult(next_node_id=next_nodes[0] if next_nodes else None)

    async def run_config(self, config: dict[str, object], context: ExecutionContext) -> dict[str, JsonValue]:
        self.validate_config(config)
        target, selection_reason = await self._pick_target(config, context)
        request_payload: dict[str, JsonValue] | None = None
        result: dict[str, JsonValue] | None = None
        selected_target_ref = "department_chat" if target is None else self._string_value(target, "target_ref")
        target_type = "department_chat"

        if target is not None:
            effective_target = {
                **target,
                "result_delivery": config.get("result_delivery"),
                "result_target_dept_id": config.get("result_target_dept_id"),
            }
            target_type = self._string_value(effective_target, "target_type")
            if target_type == "department_chat":
                request_payload = self.build_department_chat_request(effective_target, context)
                result = {
                    "status": "succeeded",
                    "operation": self._string_value(effective_target, "operation") or "send_report",
                    "summary": f"风险报告已发送到 {request_payload['dept_id']} 部门对话框",
                    "delivery_channel": "chat",
                }
            elif target_type == "department_table":
                request_payload = self.build_department_table_request(effective_target, context)
                result = await self.department_table_writer.write_row(request_payload)
            else:
                raise ValueError(f"UNSUPPORTED_EXECUTION_TARGET:{target_type}")
        elif self._string_value(config, "result_delivery") != "chat":
            raise ValueError("EXECUTION_TARGETS_REQUIRED")

        chat_delivery = self.build_chat_delivery(config, context, result=result)
        if request_payload is None:
            request_payload = {
                "execution_id": context.execution_id,
                "workflow_id": context.workflow_id,
                "workflow_version": context.workflow_version,
                "node_id": context.node_id,
                "dept_id": chat_delivery["target_dept_id"],
                "operator_id": context.operator_id,
                "target_code": "department_chat",
                "target_type": "department_chat",
                "provider": "chat",
                "operation": "send_report",
                "trace_id": context.trace_id,
                "risk_level": context.risk_level,
                "result_delivery": self._string_value(config, "result_delivery") or None,
                "result_target_dept_id": chat_delivery["target_dept_id"],
            }
        if result is None:
            result = {
                "status": "succeeded",
                "operation": "send_report",
                "summary": str(chat_delivery["summary"]),
                "delivery_channel": "chat",
            }

        return {
            "status": "succeeded",
            "target_type": target_type,
            "selected_target_ref": selected_target_ref,
            "selection_reason": selection_reason,
            "request_payload": request_payload,
            "result": result,
            "chat_delivery": chat_delivery,
        }

    def validate_config(self, config: dict[str, object]) -> None:
        raw_targets = config.get("execution_targets")
        if not isinstance(raw_targets, list):
            raw_targets = []
        targets = [cast(dict[str, object], item) for item in cast(list[object], raw_targets) if isinstance(item, dict)]
        active_targets = [item for item in targets if self._is_target_active(item)]

        if not active_targets and self._string_value(config, "result_delivery") == "chat":
            return

        if not active_targets:
            raise ValueError("EXECUTION_TARGETS_REQUIRED")

        for typed_target in active_targets:
            target_type = self._string_value(typed_target, "target_type")
            if target_type == "department_chat":
                continue
            if target_type != "department_table":
                raise ValueError("EXECUTION_TARGET_TYPE_UNSUPPORTED")

            required_fields = ["target_ref", "provider", "operation"]
            missing_fields = [field for field in required_fields if not self._string_value(typed_target, field)]
            if missing_fields:
                raise ValueError(f"EXECUTION_TARGET_MISSING_FIELDS:{','.join(missing_fields)}")

            if self._string_value(typed_target, "operation") not in SUPPORTED_OPERATIONS:
                raise ValueError("EXECUTION_TARGET_OPERATION_UNSUPPORTED")

    def build_chat_delivery(
        self,
        config: dict[str, object],
        context: ExecutionContext,
        *,
        result: dict[str, JsonValue] | None,
    ) -> dict[str, JsonValue]:
        chat_report = self._extract_chat_report(context)
        target_dept_id = self._string_value(config, "result_target_dept_id") or self._resolve_chat_target_dept_id(context)
        raw_chat_delivery = config.get("chat_delivery")
        chat_delivery_config = cast(dict[str, object], raw_chat_delivery) if isinstance(raw_chat_delivery, dict) else {}
        send_summary = self._bool_value(chat_delivery_config.get("send_summary"), default=True)
        template = str(config.get("result_template") or "").replace("{{", "${").replace("}}", "}")
        summary = self._stringify_json_value(chat_report.get("content")) or self._build_chat_summary(context)
        explanation = context.decision_explanation or ""
        actions_text = self._stringify_recommended_actions(context.recommended_actions)
        result_summary = str(result.get("summary")) if isinstance(result, dict) and result.get("summary") is not None else ""
        decision_payload_text = json.dumps(context.decision_payload or {}, ensure_ascii=False, indent=2)
        template_vars = {
            "workflow_id": context.workflow_id,
            "execution_id": context.execution_id,
            "dept_id": target_dept_id,
            "operator_id": context.operator_id,
            "risk_level": context.risk_level or "unknown",
            "decision_summary": context.decision_summary or summary,
            "decision_explanation": explanation,
            "recommended_actions": actions_text,
            "result_summary": result_summary,
            "target_item_id": self._stringify_json_value((context.decision_payload or {}).get("target_item_id")),
            "recommended_quantity": self._stringify_json_value((context.decision_payload or {}).get("recommended_quantity")),
            "chat_report_title": self._stringify_json_value(chat_report.get("title")),
            "chat_report_content": self._stringify_json_value(chat_report.get("content")),
            "chat_report_audience": self._stringify_json_value(chat_report.get("audience")),
            "decision_payload": decision_payload_text,
        }
        if template:
            content = Template(template).safe_substitute(template_vars).strip()
        else:
            content = self._build_default_chat_report(
                summary=summary if send_summary else "",
                risk_level=context.risk_level,
                explanation=explanation,
                actions_text=actions_text,
                result_summary=result_summary,
            )
        return {
            "channel": "chat",
            "target_dept_id": target_dept_id,
            "summary": f"风险报告已发送到 {target_dept_id} 部门对话框",
            "content": content,
        }

    def build_department_chat_request(self, target: dict[str, object], context: ExecutionContext) -> dict[str, JsonValue]:
        target_dept_id = self._resolve_target_dept_id(target, context)
        return {
            "execution_id": context.execution_id,
            "workflow_id": context.workflow_id,
            "workflow_version": context.workflow_version,
            "node_id": context.node_id,
            "dept_id": target_dept_id,
            "operator_id": context.operator_id,
            "target_code": self._string_value(target, "target_ref") or f"department_chat.{target_dept_id}",
            "target_type": "department_chat",
            "provider": self._string_value(target, "provider") or "chat",
            "operation": self._string_value(target, "operation") or "send_report",
            "trace_id": context.trace_id,
            "risk_level": context.risk_level,
            "result_delivery": self._string_value(target, "result_delivery") or None,
            "result_target_dept_id": target_dept_id,
        }

    def build_department_table_request(self, target: dict[str, object], context: ExecutionContext) -> dict[str, JsonValue]:
        target_dept_id = self._resolve_target_dept_id(target, context)
        row_mapping = self._coerce_mapping(target.get("row_mapping"))
        default_values = self._coerce_mapping(target.get("default_values"))
        default_row_payload = self._extract_table_write_payload(context)
        row_payload: dict[str, JsonValue] = {
            **default_row_payload,
            **default_values,
            **{column: self._resolve_value(path, context) for column, path in row_mapping.items()},
        }
        idempotency_template = str(
            target.get("idempotency_key_template") or "${dept_id}:${execution_id}:${node_id}"
        ).replace("{{", "${").replace("}}", "}")
        idempotency_key = Template(idempotency_template).safe_substitute(
            dept_id=target_dept_id,
            execution_id=context.execution_id,
            node_id=context.node_id,
            workflow_id=context.workflow_id,
        )
        write_result_contract = target.get("write_result_contract")
        write_options: dict[str, JsonValue] = (
            cast(dict[str, JsonValue], write_result_contract)
            if isinstance(write_result_contract, dict)
            else {"return_row_id": True, "return_sheet_name": True}
        )

        return {
            "execution_id": context.execution_id,
            "workflow_id": context.workflow_id,
            "workflow_version": context.workflow_version,
            "node_id": context.node_id,
            "dept_id": target_dept_id,
            "operator_id": context.operator_id,
            "target_code": self._string_value(target, "target_ref"),
            "target_type": "department_table",
            "provider": self._string_value(target, "provider"),
            "operation": self._string_value(target, "operation"),
            "idempotency_key": idempotency_key,
            "row_payload": row_payload,
            "write_options": write_options,
            "trace_id": context.trace_id,
            "risk_level": context.risk_level,
            "result_delivery": self._string_value(target, "result_delivery") or None,
            "result_target_dept_id": self._string_value(target, "result_target_dept_id") or None,
        }

    async def _pick_target(self, config: dict[str, object], context: ExecutionContext) -> tuple[dict[str, object] | None, str]:
        raw_targets = config.get("execution_targets")
        targets = cast(list[object], raw_targets) if isinstance(raw_targets, list) else []
        typed_targets: list[dict[str, object]] = []
        for raw_item in targets:
            if not isinstance(raw_item, dict):
                continue
            typed_item = cast(dict[str, object], raw_item)
            if self._is_target_active(typed_item):
                typed_targets.append(typed_item)
        if not typed_targets:
            if self._string_value(config, "result_delivery") == "chat":
                return None, "chat_delivery_only"
            raise ValueError("EXECUTION_TARGET_INVALID")
        target_mode = str(config.get("execution_target_mode") or "manual")
        if target_mode != "ai_select" or len(typed_targets) == 1 or not self.llm_client.enabled:
            return typed_targets[0], "manual_or_fallback_first_target"

        messages = self._build_target_selection_messages(typed_targets, context)
        try:
            result = await self.llm_client.chat_json(messages=messages)
        except (httpx.HTTPError, RuntimeError):
            return typed_targets[0], "llm_selection_failed_fallback_first_target"

        selected_ref = result.get("selected_target_ref")
        if isinstance(selected_ref, str):
            matched = next((item for item in typed_targets if self._string_value(item, "target_ref") == selected_ref), None)
            if matched is not None:
                reason = str(result.get("reason") or "llm_selected_target")
                return matched, reason
        return typed_targets[0], "llm_selection_invalid_fallback_first_target"

    @staticmethod
    def _build_target_selection_messages(
        targets: list[dict[str, object]],
        context: ExecutionContext,
    ) -> list[dict[str, str]]:
        target_lines = "\n".join(
            f"- target_ref={str(item.get('target_ref') or '')}, provider={str(item.get('provider') or '')}, operation={str(item.get('operation') or '')}"
            for item in targets
        )
        return [
            {
                "role": "system",
                "content": (
                    "你是大衍系统执行型智能体的目标选择器。"
                    "请从候选 execution_targets 中选择一个最合适的 target_ref。"
                    "只输出 JSON 对象，包含 selected_target_ref 和 reason。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"当前部门：{context.dept_id}\n"
                    f"风险等级：{context.risk_level or 'unknown'}\n"
                    f"决策载荷：{context.decision_payload or {}}\n"
                    f"候选目标：\n{target_lines}"
                ),
            },
        ]

    @staticmethod
    def _coerce_mapping(value: object) -> StringMap:
        if not isinstance(value, dict):
            return {}
        return {
            str(raw_key): str(raw_value)
            for raw_key, raw_value in cast(dict[object, object], value).items()
            if isinstance(raw_key, str) and raw_value is not None
        }

    @staticmethod
    def _string_value(payload: Mapping[str, object], key: str) -> str:
        value = payload.get(key)
        return value if isinstance(value, str) else ""

    @staticmethod
    def _resolve_value(path: str, context: ExecutionContext) -> JsonValue:
        if not path:
            return None
        if path == "dept_id":
            return context.dept_id
        if path == "risk_level":
            return context.risk_level

        root, _, remainder = path.partition(".")
        if root == "decision_payload":
            current: JsonValue = context.decision_payload or {}
            for key in filter(None, remainder.split(".")):
                if not isinstance(current, dict):
                    return None
                current = current.get(key)
            return current
        return None

    def _resolve_target_dept_id(self, target: Mapping[str, object], context: ExecutionContext) -> str:
        route_mode = self._string_value(target, "dept_route_mode") or "current_dept"
        if route_mode == "fixed_dept":
            fixed_dept_id = self._string_value(target, "fixed_dept_id")
            return fixed_dept_id or context.dept_id
        if route_mode == "derived" and isinstance(context.decision_payload, dict):
            chat_report = context.decision_payload.get("chat_report") if isinstance(context.decision_payload.get("chat_report"), dict) else {}
            derived = (chat_report.get("audience") if isinstance(chat_report, dict) else None) or context.decision_payload.get("target_dept_id") or context.decision_payload.get("dept_id")
            if isinstance(derived, str) and derived:
                return derived
        return context.dept_id

    @staticmethod
    def _is_target_active(target: Mapping[str, object]) -> bool:
        target_type = ExecutionNodeHandler._string_value(target, "target_type")
        if target_type == "department_chat":
            return True
        return bool(ExecutionNodeHandler._string_value(target, "target_ref"))

    def _should_pause_for_approval(self, config: dict[str, object], state: RuntimeState, context: ExecutionContext) -> bool:
        if not bool(config.get("approval_required", True)):
            return False
        approval_mode = str(config.get("approval_mode") or "risk_based")
        if approval_mode == "never":
            return False
        if self._is_approval_granted_for_node(state, context.node_id):
            return False
        if approval_mode == "always":
            return True
        return (context.risk_level or "").lower() in {"high"}

    @staticmethod
    def _is_approval_granted_for_node(state: RuntimeState, node_id: str) -> bool:
        return state.context.get("approval_decision") == "approved" and state.context.get("approval_current_node") == node_id

    @staticmethod
    def _clear_execution_approval_context(node_id: str, state: RuntimeState) -> None:
        if state.context.get("approval_current_node") != node_id:
            return
        for key in ("approval_decision", "approval_comment", "approval_current_node", "approval_next_node", "approval_title", "approval_summary", "active_approval_go_id", "active_approval_task_id"):
            state.context.pop(key, None)

    async def _create_execution_approval(self, node: RuntimeNode, state: RuntimeState, next_node: str | None) -> None:
        if self.approval_repository is None:
            raise ValueError("APPROVAL_REPOSITORY_NOT_CONFIGURED")
        go_approval_id = f"go_appr_{uuid4().hex[:12]}"
        task = ApprovalTask(
            id=f"appr_{uuid4().hex[:12]}",
            go_approval_id=go_approval_id,
            execution_id=state.execution_id,
            status="pending",
        )
        _ = await self.approval_repository.create_task(task)
        state.context["active_approval_go_id"] = go_approval_id
        state.context["active_approval_task_id"] = task.id
        state.context["approval_title"] = str(node.config.get("approvalTitle") or f"执行审批：{node.name}")
        state.context["approval_summary"] = str(node.config.get("description") or self._build_execution_approval_summary(node, state))
        state.context["approval_current_node"] = node.id
        state.context["approval_next_node"] = node.id
        session_id = state.context.get("chat_session_id")
        if isinstance(session_id, str) and session_id:
            chat_repository = ChatRepository(self.approval_repository.session)
            _ = await chat_repository.append_assistant_message(
                session_id=session_id,
                dept_id=state.dept_id,
                content=f"执行审批已送达当前部门对话框：《{state.context['approval_title']}》等待处理。",
                payload={
                    "message_kind": "approval_pending",
                    "approval_task_id": task.id,
                    "go_approval_id": go_approval_id,
                    "execution_id": state.execution_id,
                    "title": state.context["approval_title"],
                    "summary": state.context["approval_summary"],
                    "resume_to_node": next_node,
                },
                related_execution_id=state.execution_id,
            )

    @staticmethod
    def _build_execution_approval_summary(node: RuntimeNode, state: RuntimeState) -> str:
        latest_decision = next(reversed(state.decision_outputs.values()), None)
        summary = latest_decision.get("decision_summary") if isinstance(latest_decision, dict) else None
        risk_level = latest_decision.get("risk_level") if isinstance(latest_decision, dict) else None
        if isinstance(summary, str) and summary:
            return f"{summary}（风险等级：{risk_level or 'unknown'}）"
        return f"执行节点 {node.name} 需要审批后继续。"

    @staticmethod
    def _bool_value(value: object, *, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        return default

    @staticmethod
    def _resolve_chat_target_dept_id(context: ExecutionContext) -> str:
        if isinstance(context.decision_payload, dict):
            chat_report = context.decision_payload.get("chat_report") if isinstance(context.decision_payload.get("chat_report"), dict) else {}
            derived = (chat_report.get("audience") if isinstance(chat_report, dict) else None) or context.decision_payload.get("target_dept_id") or context.decision_payload.get("dept_id")
            if isinstance(derived, str) and derived:
                return derived
        return context.dept_id

    @staticmethod
    def _extract_chat_report(context: ExecutionContext) -> dict[str, JsonValue]:
        if isinstance(context.decision_payload, dict):
            raw_chat_report = context.decision_payload.get("chat_report")
            if isinstance(raw_chat_report, dict):
                return cast(dict[str, JsonValue], raw_chat_report)
        return {}

    @staticmethod
    def _extract_table_write_payload(context: ExecutionContext) -> dict[str, JsonValue]:
        if isinstance(context.decision_payload, dict):
            raw_table_write = context.decision_payload.get("table_write")
            if isinstance(raw_table_write, dict):
                return cast(dict[str, JsonValue], raw_table_write)
        return {}

    @staticmethod
    def _build_chat_summary(context: ExecutionContext) -> str:
        target_item = (context.decision_payload or {}).get("target_item_id")
        risk_level = context.risk_level or "unknown"
        if target_item is not None:
            return f"检测到物料 {target_item} 存在 {risk_level} 风险。"
        return context.decision_summary or f"检测到一条 {risk_level} 风险，请及时关注。"

    @staticmethod
    def _stringify_recommended_actions(actions: list[dict[str, JsonValue]] | None) -> str:
        if not actions:
            return "无"
        lines: list[str] = []
        for item in actions:
            action_type = item.get("action_type")
            params = item.get("params") if isinstance(item.get("params"), dict) else {}
            lines.append(f"- {ExecutionNodeHandler._stringify_json_value(action_type)}：{ExecutionNodeHandler._stringify_json_value(params)}")
        return "\n".join(lines)

    @staticmethod
    def _build_default_chat_report(*, summary: str, risk_level: str | None, explanation: str, actions_text: str, result_summary: str) -> str:
        lines = ["【AI 风险报告】"]
        if summary:
            lines.append(summary)
        if risk_level:
            lines.append(f"风险等级：{risk_level}")
        if explanation:
            lines.append(f"分析说明：{explanation}")
        if actions_text and actions_text != "无":
            lines.append("建议动作：")
            lines.append(actions_text)
        if result_summary:
            lines.append(f"执行回传：{result_summary}")
        return "\n".join(lines)

    @staticmethod
    def _stringify_json_value(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float, bool)):
            return str(value)
        return json.dumps(value, ensure_ascii=False)
