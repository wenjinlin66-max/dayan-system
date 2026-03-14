from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mock_records.db.models import DeviceStatusRecord, InventoryStockRecord, ProductionOrderRecord


async def seed_mock_records(session: AsyncSession) -> None:
    inventory_count = await session.scalar(select(func.count()).select_from(InventoryStockRecord))
    if not inventory_count:
        session.add_all(
            [
                InventoryStockRecord(id="rec_stock_001", item_id="A-1001", stock_count=16, safety_limit=20, warehouse_id="W-01", status="warning"),
                InventoryStockRecord(id="rec_stock_002", item_id="A-1002", stock_count=58, safety_limit=18, warehouse_id="W-02", status="healthy"),
            ]
        )

    order_count = await session.scalar(select(func.count()).select_from(ProductionOrderRecord))
    if not order_count:
        session.add_all(
            [
                ProductionOrderRecord(id="rec_order_001", order_id="PO-240315-01", progress=62, order_status="running", workshop_id="WS-01"),
                ProductionOrderRecord(id="rec_order_002", order_id="PO-240315-02", progress=18, order_status="pending", workshop_id="WS-02"),
            ]
        )

    device_count = await session.scalar(select(func.count()).select_from(DeviceStatusRecord))
    if not device_count:
        session.add_all(
            [
                DeviceStatusRecord(id="rec_device_001", device_id="DEV-01", temperature=64.3, vibration=1.2, device_state="online"),
                DeviceStatusRecord(id="rec_device_002", device_id="DEV-02", temperature=79.8, vibration=3.7, device_state="alarm"),
            ]
        )

    await session.commit()
