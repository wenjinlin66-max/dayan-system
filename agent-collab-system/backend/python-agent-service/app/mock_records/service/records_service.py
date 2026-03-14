from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
from datetime import date, datetime
from typing import cast
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.approvals.repository import ApprovalRepository
from app.domain.executions.repository import ExecutionRepository
from app.domain.executions.service import ExecutionService
from app.domain.workflows.repository import WorkflowRepository
from app.mock_records.db.models import DeviceStatusRecord, InventoryStockRecord, ProductionOrderRecord, SensorChangeLogRecord
from app.mock_records.repository.records_repository import MockRecordsRepository
from app.mock_records.schemas.records import (
    MockRecordMutationResponse,
    MockRecordsRecentEventItem,
    MockRecordsRecentEventsResponse,
    MockRecordsRowListResponse,
    MockRecordsSourceItem,
    MockRecordsSourcesResponse,
    MockRecordsTableItem,
    MockRecordsTablesResponse,
    MockRecordsTableSchemaField,
    MockRecordsTableSchemaResponse,
)
from app.schemas.execution import ExecutionOperator, ExecutionStartRequest, ExecutionTrigger


@dataclass(slots=True)
class TableConfig:
    table_name: str
    label: str
    description: str
    source_system: str
    model: type[InventoryStockRecord | ProductionOrderRecord | DeviceStatusRecord]
    fields: list[MockRecordsTableSchemaField]


TABLE_CONFIGS = {
    "inventory_stock": TableConfig(
        table_name="inventory_stock",
        label="库存表",
        description="低库存、补货等感知型场景的核心测试表",
        source_system="dayan_mock_records",
        model=InventoryStockRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="item_id", label="物料编码", field_type="string"),
            MockRecordsTableSchemaField(name="stock_count", label="库存数量", field_type="number"),
            MockRecordsTableSchemaField(name="safety_limit", label="安全库存", field_type="number"),
            MockRecordsTableSchemaField(name="warehouse_id", label="仓库编码", field_type="string"),
            MockRecordsTableSchemaField(name="status", label="库存状态", field_type="string"),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
    "production_order": TableConfig(
        table_name="production_order",
        label="生产工单",
        description="工单延迟、进度波动等感知型测试表",
        source_system="dayan_mock_records",
        model=ProductionOrderRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="order_id", label="工单编号", field_type="string"),
            MockRecordsTableSchemaField(name="progress", label="进度", field_type="number"),
            MockRecordsTableSchemaField(name="order_status", label="工单状态", field_type="string"),
            MockRecordsTableSchemaField(name="workshop_id", label="车间编码", field_type="string"),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
    "device_status": TableConfig(
        table_name="device_status",
        label="设备状态",
        description="设备温度、振动、在线状态等感知型测试表",
        source_system="dayan_mock_records",
        model=DeviceStatusRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="device_id", label="设备编号", field_type="string"),
            MockRecordsTableSchemaField(name="temperature", label="温度", field_type="number"),
            MockRecordsTableSchemaField(name="vibration", label="振动值", field_type="number"),
            MockRecordsTableSchemaField(name="device_state", label="设备状态", field_type="string"),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
}


class MockRecordsService:
    repository: MockRecordsRepository
    main_session: AsyncSession
    workflow_repository: WorkflowRepository
    execution_service: ExecutionService

    def __init__(self, mock_session: AsyncSession, main_session: AsyncSession) -> None:
        self.repository = MockRecordsRepository(mock_session)
        self.main_session = main_session
        self.workflow_repository = WorkflowRepository(main_session)
        self.execution_service = ExecutionService(
            execution_repository=ExecutionRepository(main_session),
            workflow_repository=self.workflow_repository,
            approval_repository=ApprovalRepository(main_session),
        )

    def list_sources(self) -> MockRecordsSourcesResponse:
        return MockRecordsSourcesResponse(sources=[MockRecordsSourceItem(source_system="dayan_mock_records", label="Mock Records 独立测试库")])

    def list_tables(self) -> MockRecordsTablesResponse:
        return MockRecordsTablesResponse(
            tables=[
                MockRecordsTableItem(
                    table_name=config.table_name,
                    label=config.label,
                    source_system=config.source_system,
                    description=config.description,
                )
                for config in TABLE_CONFIGS.values()
            ]
        )

    def get_table_schema(self, table_name: str) -> MockRecordsTableSchemaResponse:
        config = self._get_table_config(table_name)
        return MockRecordsTableSchemaResponse(
            table_name=config.table_name,
            label=config.label,
            source_system=config.source_system,
            fields=config.fields,
        )

    async def list_rows(self, table_name: str) -> MockRecordsRowListResponse:
        rows = await self.repository.list_rows(table_name)
        return MockRecordsRowListResponse(table_name=table_name, rows=[self._serialize_row(row) for row in rows])

    async def create_row(self, table_name: str, values: dict[str, object], *, dept_id: str, user_id: str) -> MockRecordMutationResponse:
        before = None
        row = await self.repository.create_row(table_name, self._sanitize_values(table_name, values, allow_record_id=False))
        after = self._serialize_row(row)
        return await self._finalize_mutation(table_name, row.id, "created", before, after, dept_id=dept_id, user_id=user_id)

    async def update_row(self, table_name: str, record_id: str, values: dict[str, object], *, dept_id: str, user_id: str) -> MockRecordMutationResponse:
        existing = await self.repository.get_row(table_name, record_id)
        if existing is None:
            raise ValueError("RECORD_NOT_FOUND")
        before = self._serialize_row(existing)
        row = await self.repository.update_row(table_name, record_id, self._sanitize_values(table_name, values, allow_record_id=False))
        after = self._serialize_row(row)
        return await self._finalize_mutation(table_name, row.id, "updated", before, after, dept_id=dept_id, user_id=user_id)

    async def delete_row(self, table_name: str, record_id: str, *, dept_id: str, user_id: str) -> MockRecordMutationResponse:
        existing = await self.repository.get_row(table_name, record_id)
        if existing is None:
            raise ValueError("RECORD_NOT_FOUND")
        before = self._serialize_row(existing)
        row = await self.repository.delete_row(table_name, record_id)
        return await self._finalize_mutation(table_name, row.id, "deleted", before, before or {}, dept_id=dept_id, user_id=user_id)

    async def list_recent_events(self) -> MockRecordsRecentEventsResponse:
        events = await self.repository.list_recent_events()
        return MockRecordsRecentEventsResponse(
            events=[
                MockRecordsRecentEventItem(
                    change_event_id=item.id,
                    table_name=item.table_name,
                    record_id=item.record_id,
                    operation=item.operation,
                    event_type=item.event_type,
                    changed_fields=list(item.changed_fields or []),
                    triggered_execution_ids=list(item.triggered_execution_ids or []),
                    created_at=item.created_at.replace(tzinfo=timezone.utc).isoformat() if item.created_at else None,
                )
                for item in events
            ]
        )

    async def _finalize_mutation(
        self,
        table_name: str,
        record_id: str,
        operation: str,
        before: dict[str, object] | None,
        after: dict[str, object],
        *,
        dept_id: str,
        user_id: str,
    ) -> MockRecordMutationResponse:
        event_type = f"record.{operation}"
        event_id = f"evt_mock_{uuid4().hex[:10]}"
        changed_fields = self._calculate_changed_fields(before, after, operation=operation)
        triggered_execution_ids = await self._trigger_matching_workflows(
            table_name=table_name,
            event_id=event_id,
            event_type=event_type,
            operation=operation,
            before=before,
            after=after,
            dept_id=dept_id,
            user_id=user_id,
        )

        _ = await self.repository.append_change_log(
            SensorChangeLogRecord(
                id=event_id,
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                event_type=event_type,
                source_system="dayan_mock_records",
                changed_fields=changed_fields,
                before_data=before,
                after_data=after,
                triggered_execution_ids=triggered_execution_ids,
                note="Triggered from temporary mock records workbench",
            )
        )
        await self.repository.session.commit()
        await self.main_session.commit()
        return MockRecordMutationResponse(
            table_name=table_name,
            record_id=record_id,
            row=after,
            change_event_id=event_id,
            triggered_execution_ids=triggered_execution_ids,
        )

    async def _trigger_matching_workflows(
        self,
        *,
        table_name: str,
        event_id: str,
        event_type: str,
        operation: str,
        before: dict[str, object] | None,
        after: dict[str, object],
        dept_id: str,
        user_id: str,
    ) -> list[str]:
        workflows = await self.workflow_repository.list_workflows_by_dept(dept_id)
        execution_ids: list[str] = []
        for workflow in workflows:
            release = await self.workflow_repository.get_current_release(workflow.id)
            if release is None or release.compile_status != "success" or not release.execution_dag:
                continue
            if not self._release_matches_event(release.execution_dag, table_name=table_name, event_type=event_type, operation=operation):
                continue
            response = await self.execution_service.start(
                ExecutionStartRequest(
                    workflow_id=workflow.id,
                    version=release.version,
                    mode="released",
                    dept_id=dept_id,
                    trigger=ExecutionTrigger(type="event", event_id=event_id),
                    operator=ExecutionOperator(user_id=user_id, roles=[]),
                    input={
                        "event": {
                            "event_id": event_id,
                            "event_type": event_type,
                            "source": "records_workbench",
                            "dept_id": dept_id,
                            "payload": {
                                "source_system": "dayan_mock_records",
                                "table": table_name,
                                "operation": operation,
                                "before": before,
                                "after": after,
                                "changed_fields": self._calculate_changed_fields(before, after, operation=operation),
                            },
                        }
                    },
                ),
                dept_id=dept_id,
                user_id=user_id,
            )
            execution_ids.append(response.execution_id)
        return execution_ids

    def _release_matches_event(self, execution_dag: dict[str, object], *, table_name: str, event_type: str, operation: str) -> bool:
        raw_nodes = execution_dag.get("nodes")
        if not isinstance(raw_nodes, list):
            return False
        for raw_item in cast(list[object], raw_nodes):
            if not isinstance(raw_item, dict):
                continue
            item = cast(dict[str, object], raw_item)
            if item.get("type") != "sensor_agent":
                continue
            raw_config = item.get("config")
            if not isinstance(raw_config, dict):
                continue
            config = cast(dict[str, object], raw_config)
            source_system = str(config.get("source_system") or "")
            source_table = str(config.get("source_table") or "")
            source_event_key = str(config.get("source_event_key") or "")
            if source_system and source_system != "dayan_mock_records":
                continue
            if source_table and source_table != table_name:
                continue
            if source_event_key and source_event_key not in {event_type, operation}:
                continue
            return True
        return False

    def _get_table_config(self, table_name: str) -> TableConfig:
        config = TABLE_CONFIGS.get(table_name)
        if config is None:
            raise ValueError("RECORDS_TABLE_NOT_FOUND")
        return config

    def _sanitize_values(self, table_name: str, values: dict[str, object], *, allow_record_id: bool) -> dict[str, object]:
        config = self._get_table_config(table_name)
        allowed_fields = {field.name for field in config.fields if field.editable}
        sanitized = {key: value for key, value in values.items() if key in allowed_fields}
        if not sanitized and values:
            raise ValueError("RECORDS_MUTATION_FIELDS_INVALID")
        if allow_record_id:
            raw_record_id = values.get("record_id") or values.get("id")
            if isinstance(raw_record_id, str) and raw_record_id:
                sanitized["id"] = raw_record_id
        return sanitized

    def _serialize_row(self, row: InventoryStockRecord | ProductionOrderRecord | DeviceStatusRecord) -> dict[str, object]:
        result: dict[str, object] = {}
        for field_name in row.__mapper__.columns.keys():
            value = cast(object, getattr(row, field_name))
            if isinstance(value, datetime):
                result[field_name] = value.isoformat()
            elif isinstance(value, date):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result

    def _calculate_changed_fields(self, before: dict[str, object] | None, after: dict[str, object], *, operation: str) -> list[str]:
        if before is None:
            return [key for key in after.keys() if key != "updated_at"]
        if operation == "deleted":
            return [key for key in before.keys() if key != "updated_at"]
        if not after:
            return [key for key in before.keys() if key != "updated_at"]
        changed: list[str] = []
        for key, value in after.items():
            if before.get(key) != value:
                changed.append(key)
        return changed
