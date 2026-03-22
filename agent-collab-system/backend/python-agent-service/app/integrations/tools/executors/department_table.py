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
        rows_payload = payload.get("rows_payload") if isinstance(payload.get("rows_payload"), list) else []
        serialized_row_payload: dict[str, JsonValue] = {}
        table_name = route.table_id
        if not isinstance(row_payload, dict):
            row_payload = {}

        async with get_mock_session_factory()() as session:
            from app.db.session import get_session_factory
            from app.mock_records.service.records_service import MockRecordsService

            async with get_session_factory()() as main_session:
                repository = MockRecordsRepository(session)
                service = MockRecordsService(session, main_session)
                operator_id = str(payload.get("operator_id") or "system")
                try:
                    operation = str(payload.get("operation") or "append_row")
                    allowed_fields = set(repository.get_model(table_name).__mapper__.columns.keys()) - {"updated_at"}
                    sanitized_payload = {key: value for key, value in dict(row_payload).items() if key in allowed_fields}
                    object_payload: dict[str, object] = {key: value for key, value in sanitized_payload.items()}
                    object_rows_payload: list[dict[str, object]] = [
                        {key: value for key, value in cast(dict[str, JsonValue], item).items() if key in allowed_fields}
                        for item in rows_payload
                        if isinstance(item, dict)
                    ]
                    if operation == "update_row":
                        record_id = DepartmentTableExecutor.extract_record_id(payload)
                        if not record_id:
                            raise ValueError("DEPARTMENT_TABLE_RECORD_ID_REQUIRED")
                        mutation = await service.update_row(
                            table_name,
                            record_id,
                            object_payload,
                            dept_id=dept_id,
                            user_id=operator_id,
                            internal_write=True,
                        )
                        serialized_row_payload = cast(dict[str, JsonValue], mutation.row)
                    elif operation == "upsert_row":
                        record_id = DepartmentTableExecutor.extract_record_id(payload)
                        if record_id:
                            existing = await repository.get_row(table_name, record_id)
                            if existing is None and table_name == "customer_order":
                                existing_orders = await repository.list_rows_by_field(
                                    table_name,
                                    "order_no",
                                    object_payload.get("order_no"),
                                ) if object_payload.get("order_no") is not None else []
                                existing = existing_orders[0] if existing_orders else None
                            if existing is not None:
                                mutation = await service.update_row(
                                    table_name,
                                    str(getattr(existing, "id")),
                                    object_payload,
                                    dept_id=dept_id,
                                    user_id=operator_id,
                                    internal_write=True,
                                )
                            else:
                                mutation = await service.create_row(
                                    table_name,
                                    object_payload,
                                    dept_id=dept_id,
                                    user_id=operator_id,
                                    record_id=record_id,
                                    internal_write=True,
                                )
                        else:
                            mutation = await service.create_row(
                                table_name,
                                object_payload,
                                dept_id=dept_id,
                                user_id=operator_id,
                                internal_write=True,
                            )
                        serialized_row_payload = cast(dict[str, JsonValue], mutation.row)
                    elif operation in {"append_rows", "upsert_rows", "replace_rows"}:
                        replace_by_field = str(payload.get("replace_by_field") or "")
                        replace_by_value = payload.get("replace_by_value")
                        mutations = await service.write_rows(
                            table_name,
                            object_rows_payload,
                            dept_id=dept_id,
                            user_id=operator_id,
                            operation=operation,
                            replace_by_field=replace_by_field or None,
                            replace_by_value=cast(object | None, replace_by_value),
                            internal_write=True,
                        )
                        first_row = mutations[0].row if mutations else {}
                        serialized_row_payload = cast(dict[str, JsonValue], first_row)
                    else:
                        mutation = await service.create_row(
                            table_name,
                            object_payload,
                            dept_id=dept_id,
                            user_id=operator_id,
                            internal_write=True,
                        )
                        serialized_row_payload = cast(dict[str, JsonValue], mutation.row)
                except ValueError:
                    await session.rollback()
                    await main_session.rollback()
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
            "summary": f"已向 {route.table_id} 写入{'多条' if str(payload.get('operation') or '').endswith('rows') else '一条'}结构化记录",
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
