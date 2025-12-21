from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Warehouse


async def get_or_create_warehouse_record(
        session: AsyncSession,
        product_id: int,
) -> Warehouse:
    """
    Получить или создать запись склада для товара.

    Args:
        session: Сессия БД
        product_id: ID товара

    Returns:
        Запись склада
    """
    # Ищем запись склада
    stmt = select(Warehouse).where(Warehouse.product_id == product_id)
    result = await session.execute(stmt)
    warehouse_record = result.scalar_one_or_none()

    if warehouse_record:
        return warehouse_record

    # Если записи нет, создаем новую
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

    Args:
        session: Сессия БД
        product_id: ID товара
        quantity: Количество для добавления

    Returns:
        Обновленная запись склада
    """
    # Получаем или создаем запись склада
    warehouse_record = await get_or_create_warehouse_record(session, product_id)

    # Добавляем количество
    warehouse_record.rest += quantity

    await session.flush()

    return warehouse_record
