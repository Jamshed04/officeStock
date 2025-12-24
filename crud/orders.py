# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from core.models import Order
# from core.models import Category
# from core.schemas.receipt import OrderCreate
#
#
# async def get_order_by_name(
#         session: AsyncSession,
#         order_name: str,
# ) -> Order | None:
#     """
#     Получить заказ по названию.
#     """
#     stmt = select(Order).where(Order.name == order_name)
#     result = await session.execute(stmt)
#     return result.scalar_one_or_none()
#
#
# async def create_order(
#         session: AsyncSession,
#         order_data: OrderCreate,
#         user_id: int,
# ) -> Order:
#     """
#     Создать новый заказ.
#     """
#     existing_order = await get_order_by_name(session, order_data.name)
#     if existing_order:
#         raise ValueError(f"Заказ с названием '{order_data.name}' уже существует")
#
#     new_order = Order(
#         name=order_data.name,
#         description=order_data.description,
#         status_id=1,
#         user_id=user_id,
#     )
#
#     session.add(new_order)
#     await session.commit()
#     await session.refresh(new_order)
#
#     return new_order
#
#
# async def get_all_orders(
#         session: AsyncSession,
#         skip: int = 0,
#         limit: int = 100,
# ) -> list[Order]:
#     """
#     Получить список всех заказов.
#     """
#     stmt = select(Order).offset(skip).limit(limit).order_by(Order.date_create.desc())
#     result = await session.execute(stmt)
#     return list(result.scalars().all())
#
#
# async def get_order_by_id(
#         session: AsyncSession,
#         order_id: int,
# ) -> Order | None:
#     """
#     Получить заказ по ID.
#     """
#     stmt = select(Order).where(Order.id == order_id)
#     result = await session.execute(stmt)
#     return result.scalar_one_or_none()