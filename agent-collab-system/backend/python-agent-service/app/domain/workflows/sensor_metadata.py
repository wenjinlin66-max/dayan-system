from __future__ import annotations

from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.sensor_metadata import (
    SensorEventKeyOption,
    SensorFieldOption,
    SensorMetadataResponse,
    SensorOperatorOption,
    SensorSourceOption,
    SensorSourceTypeOption,
    SensorTableOption,
)


class SensorMetadataService:
    def build_default_metadata(self) -> SensorMetadataResponse:
        return SensorMetadataResponse(
            source_types=[
                SensorSourceTypeOption(value="form_change", label="数据库记录变更"),
                SensorSourceTypeOption(value="iot", label="IoT 状态上报"),
                SensorSourceTypeOption(value="supply_chain_event", label="供应链事件"),
                SensorSourceTypeOption(value="third_party_notice", label="第三方通知"),
                SensorSourceTypeOption(value="schedule", label="定时巡检"),
                SensorSourceTypeOption(value="manual", label="手动 / Mock"),
            ],
            operators=[
                SensorOperatorOption(value="eq", label="等于", supported_field_types=["string", "number", "boolean"]),
                SensorOperatorOption(value="ne", label="不等于", supported_field_types=["string", "number", "boolean"]),
                SensorOperatorOption(value=">", label="大于", supported_field_types=["number"]),
                SensorOperatorOption(value=">=", label="大于等于", supported_field_types=["number"]),
                SensorOperatorOption(value="<", label="小于", supported_field_types=["number"]),
                SensorOperatorOption(value="<=", label="小于等于", supported_field_types=["number"]),
            ],
            sources=[
                SensorSourceOption(
                    value="erp_prod",
                    label="ERP 生产库",
                    source_type="form_change",
                    tables=[
                        SensorTableOption(
                            value="inventory_stock",
                            label="库存表 inventory_stock",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="item_id", label="物料编码", field_type="string"),
                                SensorFieldOption(value="stock_count", label="库存数量", field_type="number"),
                                SensorFieldOption(value="safety_limit", label="安全库存", field_type="number"),
                                SensorFieldOption(
                                    value="warehouse_id",
                                    label="仓库编码",
                                    field_type="string",
                                    suggested_values=["W-01", "W-02", "W-03"],
                                ),
                                SensorFieldOption(
                                    value="status",
                                    label="库存状态",
                                    field_type="string",
                                    suggested_values=["healthy", "warning", "critical"],
                                ),
                            ],
                        ),
                        SensorTableOption(
                            value="production_order",
                            label="生产工单 production_order",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="order_id", label="工单编号", field_type="string"),
                                SensorFieldOption(value="progress", label="进度", field_type="number"),
                                SensorFieldOption(
                                    value="order_status",
                                    label="工单状态",
                                    field_type="string",
                                    suggested_values=["pending", "running", "done", "delayed"],
                                ),
                            ],
                        ),
                    ],
                ),
                SensorSourceOption(
                    value="mock_erp",
                    label="Mock ERP 事件源",
                    source_type="manual",
                    tables=[
                        SensorTableOption(
                            value="inventory_stock",
                            label="库存表 inventory_stock",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="inventory.low_stock", label="低库存事件"),
                            ],
                            fields=[
                                SensorFieldOption(value="item_id", label="物料编码", field_type="string"),
                                SensorFieldOption(value="stock_count", label="库存数量", field_type="number"),
                                SensorFieldOption(value="safety_limit", label="安全库存", field_type="number"),
                                SensorFieldOption(
                                    value="warehouse_id",
                                    label="仓库编码",
                                    field_type="string",
                                    suggested_values=["W-01", "W-02"],
                                ),
                            ],
                        )
                    ],
                ),
                SensorSourceOption(
                    value="dayan_mock_records",
                    label="业务表格区临时测试源",
                    source_type="form_change",
                    tables=[
                        SensorTableOption(
                            value="inventory_stock",
                            label="库存表 inventory_stock",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="item_id", label="物料编码", field_type="string"),
                                SensorFieldOption(value="stock_count", label="库存数量", field_type="number"),
                                SensorFieldOption(value="safety_limit", label="安全库存", field_type="number"),
                                SensorFieldOption(value="warehouse_id", label="仓库编码", field_type="string", suggested_values=["W-01", "W-02", "W-03"]),
                                SensorFieldOption(value="status", label="库存状态", field_type="string", suggested_values=["healthy", "warning", "critical", "decision_validation"]),
                            ],
                        ),
                        SensorTableOption(
                            value="production_order",
                            label="生产工单 production_order",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="order_id", label="工单编号", field_type="string"),
                                SensorFieldOption(value="progress", label="进度", field_type="number"),
                                SensorFieldOption(value="order_status", label="工单状态", field_type="string", suggested_values=["pending", "running", "done", "delayed"]),
                                SensorFieldOption(value="workshop_id", label="车间编码", field_type="string"),
                            ],
                        ),
                        SensorTableOption(
                            value="device_status",
                            label="设备状态 device_status",
                            event_keys=[
                                SensorEventKeyOption(value="record.updated", label="记录更新"),
                                SensorEventKeyOption(value="record.created", label="记录新增"),
                            ],
                            fields=[
                                SensorFieldOption(value="device_id", label="设备编号", field_type="string"),
                                SensorFieldOption(value="temperature", label="温度", field_type="number"),
                                SensorFieldOption(value="vibration", label="振动值", field_type="number"),
                                SensorFieldOption(value="device_state", label="设备状态", field_type="string", suggested_values=["online", "offline", "alarm"]),
                            ],
                        ),
                    ],
                ),
                SensorSourceOption(
                    value="mes_iot_gateway",
                    label="MES IoT 网关",
                    source_type="iot",
                    tables=[
                        SensorTableOption(
                            value="device_status",
                            label="设备状态 device_status",
                            event_keys=[
                                SensorEventKeyOption(value="iot.status_reported", label="状态上报"),
                            ],
                            fields=[
                                SensorFieldOption(value="device_id", label="设备编号", field_type="string"),
                                SensorFieldOption(value="temperature", label="温度", field_type="number"),
                                SensorFieldOption(value="vibration", label="振动值", field_type="number"),
                                SensorFieldOption(
                                    value="device_state",
                                    label="设备状态",
                                    field_type="string",
                                    suggested_values=["online", "offline", "alarm"],
                                ),
                            ],
                        )
                    ],
                ),
            ],
        )

    async def get_metadata(self, session: AsyncSession) -> SensorMetadataResponse:
        metadata = self.build_default_metadata()
        live_source = await self._build_live_database_source(session)
        if live_source is not None:
            metadata.sources.insert(0, live_source)
        return metadata

    async def _build_live_database_source(self, session: AsyncSession) -> SensorSourceOption | None:
        result = await session.execute(
            text(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """
            )
        )
        rows = result.mappings().all()
        if not rows:
            return None

        tables: dict[str, list[SensorFieldOption]] = defaultdict(list)
        for row in rows:
            table_name = str(row.get("table_name") or "")
            column_name = str(row.get("column_name") or "")
            data_type = str(row.get("data_type") or "")
            if not table_name or not column_name:
                continue
            tables[table_name].append(
                SensorFieldOption(
                    value=column_name,
                    label=column_name,
                    field_type=self._map_field_type(data_type),
                )
            )

        table_options = [
            SensorTableOption(
                value=table_name,
                label=f"实时数据库表 {table_name}",
                event_keys=[
                    SensorEventKeyOption(value="record.updated", label="记录更新"),
                    SensorEventKeyOption(value="record.created", label="记录新增"),
                    SensorEventKeyOption(value="record.deleted", label="记录删除"),
                ],
                fields=fields,
            )
            for table_name, fields in tables.items()
        ]

        return SensorSourceOption(
            value="postgres_live",
            label="当前后端数据库（实时表结构）",
            source_type="form_change",
            tables=table_options,
        )

    @staticmethod
    def _map_field_type(data_type: str) -> str:
        normalized = data_type.lower()
        if any(keyword in normalized for keyword in ["int", "numeric", "double", "real", "decimal"]):
            return "number"
        if normalized in {"boolean", "bool"}:
            return "boolean"
        return "string"
