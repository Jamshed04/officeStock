from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Order
from core.schemas.receipt import OrderCreate


async def get_order_by_name(
        session: AsyncSession,
        order_name: str,
) -> Order | None:
    """
    Получить заказ по названию.

    Args:
        session: Сессия БД
        order_name: Название заказа

    Returns:
        Заказ или None
    """
    stmt = select(Order).where(Order.name == order_name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_order(
        session: AsyncSession,
        order_data: OrderCreate,
        user_id: int,
) -> Order:
    """
    Создать новый заказ.

    Args:
        session: Сессия БД
        order_data: Данные заказа
        user_id: ID пользователя-создателя

    Returns:
        Созданный заказ

    Raises:
        ValueError: Если заказ с таким названием уже существует
    """
    # Проверяем существование заказа с таким названием
    existing_order = await get_order_by_name(session, order_data.name)
    if existing_order:
        raise ValueError(f"Заказ с названием '{order_data.name}' уже существует")

    # Создаем заказ (status_id=1 по умолчанию из схемы БД)
    new_order = Order(
        name=order_data.name,
        description=order_data.description,
        status_id=1,  # Начальный статус
        user_id=user_id,
    )

    session.add(new_order)
    await session.commit()
    await session.refresh(new_order)

    return new_order


async def get_all_orders(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
) -> list[Order]:
    """
    Получить список всех заказов.

    Args:
        session: Сессия БД
        skip: Пропустить N записей
        limit: Максимум записей

    Returns:
        Список заказов
    """
    stmt = select(Order).offset(skip).limit(limit).order_by(Order.date_create.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_order_by_id(
        session: AsyncSession,
        order_id: int,
) -> Order | None:
    """
    Получить заказ по ID.

    Args:
        session: Сессия БД
        order_id: ID заказа

    Returns:
        Заказ или None
    """
    stmt = select(Order).where(Order.id == order_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()