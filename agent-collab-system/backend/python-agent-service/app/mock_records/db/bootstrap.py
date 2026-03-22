from __future__ import annotations

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.mock_records.db.models import (
    CustomerOrderRecord,
    CustomerSupplyRequestRecord,
    ManufacturingRequestRecord,
    PartsDemandRecord,
    ProductBomRecord,
    ProductMasterRecord,
    PurchaseRequestRecord,
    SensorChangeLogRecord,
)


LEGACY_TABLE_NAMES = ("inventory_stock", "production_order", "device_status")


async def seed_mock_records(session: AsyncSession) -> None:
    await cleanup_legacy_mock_records(session)

    product_count = await session.scalar(select(func.count()).select_from(ProductMasterRecord))
    if not product_count:
        session.add_all(
            [
                ProductMasterRecord(
                    id="rec_product_001",
                    product_code="PHONE-001",
                    product_name="苹果手机 demo 款",
                    product_version="V1",
                    category="智能终端",
                    unit_price=6999,
                    customer_notes="最小闭环样例产品，用于订单拆解演示。",
                ),
                ProductMasterRecord(
                    id="rec_product_002",
                    product_code="PAD-001",
                    product_name="平板电脑 demo 款",
                    product_version="V1",
                    category="智能终端",
                    unit_price=3999,
                    customer_notes="第二个样例产品，便于扩展 BOM。",
                ),
            ]
        )

    bom_count = await session.scalar(select(func.count()).select_from(ProductBomRecord))
    if not bom_count:
        session.add_all(
            [
                ProductBomRecord(id="rec_bom_001", product_code="PHONE-001", part_code="CAM-001", part_name="摄像头模组", qty_per_unit=2, source_type="purchase", unit_cost=280, source_ref="销售/采购部"),
                ProductBomRecord(id="rec_bom_002", product_code="PHONE-001", part_code="CHIP-001", part_name="主控芯片", qty_per_unit=1, source_type="manufacture", unit_cost=850, source_ref="生产部"),
                ProductBomRecord(id="rec_bom_003", product_code="PHONE-001", part_code="SCREEN-001", part_name="显示屏", qty_per_unit=1, source_type="customer", unit_cost=420, source_ref="客户提供"),
                ProductBomRecord(id="rec_bom_004", product_code="PAD-001", part_code="SHELL-001", part_name="平板外壳", qty_per_unit=1, source_type="manufacture", unit_cost=110, source_ref="生产部"),
            ]
        )

    order_count = await session.scalar(select(func.count()).select_from(CustomerOrderRecord))
    if not order_count:
        session.add(
            CustomerOrderRecord(
                id="rec_cus_order_001",
                order_no="SO-20260321-001",
                customer_name="果链客户A",
                product_code="PHONE-001",
                product_name="苹果手机 demo 款",
                ordered_qty=10,
                unit_price=6999,
                total_amount=69990,
                order_status="draft",
            )
        )

    demand_count = await session.scalar(select(func.count()).select_from(PartsDemandRecord))
    if not demand_count:
        session.add_all(
            [
                PartsDemandRecord(
                    id="dem_SO-20260321-001_CAM-001_purchase",
                    order_no="SO-20260321-001",
                    customer_name="果链客户A",
                    product_code="PHONE-001",
                    product_name="苹果手机 demo 款",
                    part_code="CAM-001",
                    part_name="摄像头模组",
                    source_type="purchase",
                    required_qty=20,
                    purchase_qty=20,
                    manufacture_qty=0,
                    customer_qty=0,
                    unit_cost=280,
                    total_cost=5600,
                ),
                PartsDemandRecord(
                    id="dem_SO-20260321-001_CHIP-001_manufacture",
                    order_no="SO-20260321-001",
                    customer_name="果链客户A",
                    product_code="PHONE-001",
                    product_name="苹果手机 demo 款",
                    part_code="CHIP-001",
                    part_name="主控芯片",
                    source_type="manufacture",
                    required_qty=10,
                    purchase_qty=0,
                    manufacture_qty=10,
                    customer_qty=0,
                    unit_cost=850,
                    total_cost=8500,
                ),
                PartsDemandRecord(
                    id="dem_SO-20260321-001_SCREEN-001_customer",
                    order_no="SO-20260321-001",
                    customer_name="果链客户A",
                    product_code="PHONE-001",
                    product_name="苹果手机 demo 款",
                    part_code="SCREEN-001",
                    part_name="显示屏",
                    source_type="customer",
                    required_qty=10,
                    purchase_qty=0,
                    manufacture_qty=0,
                    customer_qty=10,
                    unit_cost=420,
                    total_cost=4200,
                ),
            ]
        )

    await session.commit()


async def cleanup_legacy_mock_records(session: AsyncSession) -> None:
    await session.execute(delete(SensorChangeLogRecord).where(SensorChangeLogRecord.table_name.in_(LEGACY_TABLE_NAMES)))
    for table_name in LEGACY_TABLE_NAMES:
        await session.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
    await session.commit()
