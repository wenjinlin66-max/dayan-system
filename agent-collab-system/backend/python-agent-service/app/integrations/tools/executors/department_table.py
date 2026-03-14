from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import cast
from uuid import uuid4

from app.integrations.go_client.records import GoRecordsClient
from app.mock_records.repository.records_repository import MockRecordsRepository
from app.db.session import get_mock_session_factory
from app.runtime.models import JsonValue


@dataclass(slots=True)
class DepartmentTableRoute:
    target_code: str
    table_id: str
    provider: str
    dept_id: str | None = None


class MockRecordsGateway:
    @staticmethod
    def _serialize_record_value(value: object) -> JsonValue:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return cast(JsonValue, value)

    async def append_row(self, route: DepartmentTableRoute, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        dept_id = str(payload.get("dept_id") or route.dept_id or "unknown")
        row_payload = payload.get("row_payload") if isinstance(payload.get("row_payload"), dict) else {}
        serialized_row_payload: dict[str, JsonValue] = {}
        table_name = route.table_id
        if not isinstance(row_payload, dict):
            row_payload = {}

        async with get_mock_session_factory()() as session:
            repository = MockRecordsRepository(session)
            try:
                operation = str(payload.get("operation") or "append_row")
                allowed_fields = set(repository.get_model(table_name).__mapper__.columns.keys()) - {"updated_at"}
                sanitized_payload = {key: value for key, value in dict(row_payload).items() if key in allowed_fields}
                object_payload: dict[str, object] = {key: value for key, value in sanitized_payload.items()}
                if operation == "update_row":
                    record_id = DepartmentTableExecutor.extract_record_id(payload)
                    if not record_id:
                        raise ValueError("DEPARTMENT_TABLE_RECORD_ID_REQUIRED")
                    record = await repository.update_row(table_name, record_id, object_payload)
                elif operation == "upsert_row":
                    record_id = DepartmentTableExecutor.extract_record_id(payload)
                    if record_id:
                        existing = await repository.get_row(table_name, record_id)
                        if existing is not None:
                            record = await repository.update_row(table_name, record_id, object_payload)
                        else:
                            record = await repository.create_row(table_name, {**object_payload, "id": record_id})
                    else:
                        record = await repository.create_row(table_name, object_payload)
                else:
                    record = await repository.create_row(table_name, object_payload)
                await session.commit()
                serialized_row_payload = {
                    field_name: self._serialize_record_value(cast(object, getattr(record, field_name)))
                    for field_name in record.__mapper__.columns.keys()
                }
            except ValueError:
                await session.rollback()
                raise
        return {
            "status": "succeeded",
            "adapter_mode": "mock",
            "target_code": route.target_code,
            "table_id": route.table_id,
            "provider": route.provider,
            "operation": payload.get("operation"),
            "dept_id": dept_id,
            "sheet_name": f"{dept_id} 部门登记表",
            "row_id": str(serialized_row_payload.get("id") or f"row_{uuid4().hex[:10]}"),
            "summary": f"已向 {route.table_id} 写入一条结构化记录",
            "trace_id": f"toolrun_{uuid4().hex[:10]}",
            "row_payload": serialized_row_payload,
        }


class DepartmentTableExecutor:
    route_map: dict[str, dict[str, str]]
    tenant_id: str
    client: GoRecordsClient | None
    mock_gateway: MockRecordsGateway
    enable_mock_fallback: bool

    def __init__(
        self,
        *,
        route_map: dict[str, dict[str, str]],
        tenant_id: str,
        client: GoRecordsClient | None,
        mock_gateway: MockRecordsGateway,
        enable_mock_fallback: bool,
    ) -> None:
        self.route_map = route_map
        self.tenant_id = tenant_id
        self.client = client
        self.mock_gateway = mock_gateway
        self.enable_mock_fallback = enable_mock_fallback

    async def write_row(self, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        route = self._resolve_route(payload)
        operation = str(payload.get("operation") or "append_row")

        if self.client is None:
            if not self.enable_mock_fallback:
                raise ValueError("GO_RECORDS_CLIENT_NOT_CONFIGURED")
            return await self.mock_gateway.append_row(route, payload)

        records_request = self._build_records_request(route, payload)
        if operation == "update_row":
            record_id = self.extract_record_id(payload)
            if not record_id:
                raise ValueError("DEPARTMENT_TABLE_RECORD_ID_REQUIRED")
            response = await self.client.update_record(route.table_id, record_id, records_request)
        else:
            response = await self.client.create_record(route.table_id, records_request)

        response["adapter_mode"] = "records_api"
        response["target_code"] = route.target_code
        response["table_id"] = route.table_id
        response["provider"] = route.provider
        return response

    def _resolve_route(self, payload: dict[str, JsonValue]) -> DepartmentTableRoute:
        target_code = str(payload.get("target_code") or "department_table")
        mapped = self.route_map.get(target_code, {})
        provider = str(mapped.get("provider") or payload.get("provider") or "custom_table")
        table_id = str(mapped.get("table_id") or target_code)
        dept_id = mapped.get("dept_id")
        return DepartmentTableRoute(
            target_code=target_code,
            table_id=table_id,
            provider=provider,
            dept_id=dept_id,
        )

    def _build_records_request(self, route: DepartmentTableRoute, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        dept_id = str(payload.get("dept_id") or route.dept_id or "default")
        operator_id = str(payload.get("operator_id") or "system")
        return {
            "tenant_id": self.tenant_id,
            "dept_id": dept_id,
            "operator": {
                "user_id": operator_id,
                "roles": [],
            },
            "trace_id": payload.get("trace_id"),
            "idempotency_key": payload.get("idempotency_key"),
            "payload": payload.get("row_payload") if isinstance(payload.get("row_payload"), dict) else {},
            "execution_context": {
                "execution_id": payload.get("execution_id"),
                "workflow_id": payload.get("workflow_id"),
                "workflow_version": payload.get("workflow_version"),
                "node_id": payload.get("node_id"),
                "target_code": route.target_code,
                "provider": route.provider,
            },
        }

    @staticmethod
    def extract_record_id(payload: dict[str, JsonValue]) -> str:
        row_payload = payload.get("row_payload")
        if not isinstance(row_payload, dict):
            return ""
        raw = row_payload.get("record_id") or row_payload.get("id")
        return str(raw) if isinstance(raw, (str, int)) else ""
