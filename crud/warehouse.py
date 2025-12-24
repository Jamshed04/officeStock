from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.websockets import manager
from core.models import Warehouse
from core.schemas.notification import NotificationSchema


async def get_or_create_warehouse_record(
        session: AsyncSession,
        product_id: int,
) -> Warehouse:
    """
    Получить или создать запись склада для товара.
    """
    stmt = select(Warehouse).where(Warehouse.product_id == product_id)
    result = await session.execute(stmt)
    warehouse_record = result.scalar_one_or_none()

    if warehouse_record:
        return warehouse_record

    warehouse_record = Warehouse(
        product_id=product_id,
        rest=0,
    )
    session.add(warehouse_record)
    await session.flush()

    return warehouse_record


async def update_warehouse_stock(
        session: AsyncSession,
        product_id: int,
        quantity: Decimal,
) -> Warehouse:
    """
    Обновить остаток товара на складе (добавить количество).
    """
    warehouse_record = await get_or_create_warehouse_record(session, product_id)

    warehouse_record.rest += quantity

    if warehouse_record.rest < 3:
        notification = NotificationSchema(
            type="low_stock",
            payload={
                "product_id": product_id,
                "current_stock": warehouse_record.rest,
                "message": f"Low stock alert: Product {product_id} has {warehouse_record.rest} left!"
            }
        )
        await manager.broadcast(notification)

    await session.flush()

    return warehouse_record
