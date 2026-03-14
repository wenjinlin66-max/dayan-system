from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Final
from string import Template
from typing import Protocol, cast

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


SUPPORTED_OPERATIONS: Final[set[str]] = {"append_row", "upsert_row", "update_row"}


class ExecutionNodeHandler:
    department_table_writer: DepartmentTableWriter

    def __init__(self, department_table_writer: DepartmentTableWriter) -> None:
        self.department_table_writer = department_table_writer

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
                else cast(dict[str, JsonValue] | None, state.input_payload.get("input_values"))
            ),
            risk_level=(
                str(decision_output.get("risk_level"))
                if isinstance(decision_output, dict) and decision_output.get("risk_level") is not None
                else None
            ),
        )
        execution_result = await self.run_config(node.config, context)
        state.tool_outputs[node.id] = cast(dict[str, object], execution_result)
        return NodeExecutionResult(next_node_id=next_nodes[0] if next_nodes else None)

    async def run_config(self, config: dict[str, object], context: ExecutionContext) -> dict[str, JsonValue]:
        self.validate_config(config)
        target = self._pick_target(config)
        target_type = self._string_value(target, "target_type")

        if target_type != "department_table":
            raise ValueError(f"UNSUPPORTED_EXECUTION_TARGET:{target_type}")

        request_payload = self.build_department_table_request(target, context)
        result = await self.department_table_writer.write_row(request_payload)
        return {
            "status": "succeeded",
            "target_type": "department_table",
            "request_payload": request_payload,
            "result": result,
        }

    def validate_config(self, config: dict[str, object]) -> None:
        raw_targets = config.get("execution_targets")
        if not isinstance(raw_targets, list) or not raw_targets:
            raise ValueError("EXECUTION_TARGETS_REQUIRED")
        targets = cast(list[object], raw_targets)

        target = targets[0]
        if not isinstance(target, dict):
            raise ValueError("EXECUTION_TARGET_INVALID")

        typed_target = cast(dict[str, object], target)
        target_type = self._string_value(typed_target, "target_type")
        if target_type != "department_table":
            raise ValueError("EXECUTION_TARGET_TYPE_UNSUPPORTED")

        required_fields = ["target_ref", "provider", "operation"]
        missing_fields = [field for field in required_fields if not self._string_value(typed_target, field)]
        if missing_fields:
            raise ValueError(f"EXECUTION_TARGET_MISSING_FIELDS:{','.join(missing_fields)}")

        if self._string_value(typed_target, "operation") not in SUPPORTED_OPERATIONS:
            raise ValueError("EXECUTION_TARGET_OPERATION_UNSUPPORTED")

    def build_department_table_request(self, target: dict[str, object], context: ExecutionContext) -> dict[str, JsonValue]:
        row_mapping = self._coerce_mapping(target.get("row_mapping"))
        default_values = self._coerce_mapping(target.get("default_values"))
        row_payload: dict[str, JsonValue] = {
            **default_values,
            **{column: self._resolve_value(path, context) for column, path in row_mapping.items()},
        }
        idempotency_template = str(
            target.get("idempotency_key_template") or "${dept_id}:${execution_id}:${node_id}"
        ).replace("{{", "${").replace("}}", "}")
        idempotency_key = Template(idempotency_template).safe_substitute(
            dept_id=context.dept_id,
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
            "dept_id": context.dept_id,
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
        }

    @staticmethod
    def _pick_target(config: dict[str, object]) -> dict[str, object]:
        targets = config.get("execution_targets")
        if not isinstance(targets, list) or not targets or not isinstance(targets[0], dict):
            raise ValueError("EXECUTION_TARGET_INVALID")
        return cast(dict[str, object], targets[0])

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
