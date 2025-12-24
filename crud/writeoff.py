from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.websockets import manager
from core.models import WriteOffSchedule, Warehouse, Product
from core.schemas.notification import NotificationSchema


async def get_active_writeoff_schedules(
        session: AsyncSession,
) -> list[WriteOffSchedule]:
    """
    Получить все активные расписания списания.
    """
    stmt = (
        select(WriteOffSchedule)
        .where(WriteOffSchedule.is_active == True)
        .options(selectinload(WriteOffSchedule.product))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def process_writeoffs(session: AsyncSession, delete_when_zero: bool = True) -> dict:
    """
    Обработать все расписания списания.

    Проверяет каждое активное расписание:
    - Если прошло достаточно дней с последнего списания, списывает товар
    - Если товара нет на складе или остаток стал 0:
      * Если delete_when_zero=True: удаляет расписание из БД
      * Если delete_when_zero=False: деактивирует расписание
    """
    schedules = await get_active_writeoff_schedules(session)
    now = datetime.now()

    results = {
        "processed": 0,
        "written_off": 0,
        "deactivated": 0,
        "deleted": 0,
        "errors": []
    }

    for schedule in schedules:
        try:
            should_writeoff = False

            if schedule.last_writeoff_date is None:
                should_writeoff = True
            else:
                days_since_last = (now - schedule.last_writeoff_date).days
                if days_since_last >= schedule.interval_days:
                    should_writeoff = True

            if not should_writeoff:
                continue

            results["processed"] += 1

            stmt = select(Warehouse).where(Warehouse.product_id == schedule.product_id)
            result = await session.execute(stmt)
            warehouse_record = result.scalar_one_or_none()

            if warehouse_record is None:
                if delete_when_zero:
                    await session.delete(schedule)
                    results["deleted"] += 1
                else:
                    schedule.is_active = False
                    results["deactivated"] += 1
                await session.flush()
                continue

            if warehouse_record.rest <= 0:
                if delete_when_zero:
                    await session.delete(schedule)
                    results["deleted"] += 1
                else:
                    schedule.is_active = False
                    results["deactivated"] += 1
                await session.flush()
                continue

            previous_rest = warehouse_record.rest
            quantity_to_writeoff = schedule.quantity_per_writeoff

            if warehouse_record.rest < quantity_to_writeoff:
                quantity_to_writeoff = warehouse_record.rest

            warehouse_record.rest -= quantity_to_writeoff

            schedule.last_writeoff_date = now

            if warehouse_record.rest <= 0:
                if delete_when_zero:
                    await session.delete(schedule)
                    results["deleted"] += 1
                else:
                    schedule.is_active = False
                    results["deactivated"] += 1

            results["written_off"] += 1
            await session.flush()

            if warehouse_record.rest < 3:
                notification = NotificationSchema(
                    type="low_stock",
                    payload={
                        "product_id": schedule.product_id,
                        "current_stock": warehouse_record.rest,
                        "message": f"Low stock alert: Product {schedule.product_id} has {warehouse_record.rest} left!"
                    }
                )
                await manager.broadcast(notification)

        except Exception as e:
            results["errors"].append({
                "schedule_id": schedule.id,
                "product_id": schedule.product_id,
                "error": str(e)
            })

    await session.commit()
    return results


async def create_writeoff_schedule(
        session: AsyncSession,
        product_id: int,
        interval_days: int,
        quantity_per_writeoff: float = 1.0,
) -> WriteOffSchedule:
    """
    Создать расписание списания для товара.
    """
    stmt = select(WriteOffSchedule).where(WriteOffSchedule.product_id == product_id)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.interval_days = interval_days
        existing.quantity_per_writeoff = quantity_per_writeoff
        existing.is_active = True
        await session.flush()
        return existing

    schedule = WriteOffSchedule(
        product_id=product_id,
        interval_days=interval_days,
        quantity_per_writeoff=quantity_per_writeoff,
        is_active=True,
    )
    session.add(schedule)
    await session.flush()
    return schedule


async def update_writeoff_schedule(
        session: AsyncSession,
        schedule_id: int,
        interval_days: int | None = None,
        quantity_per_writeoff: float | None = None,
        is_active: bool | None = None,
) -> WriteOffSchedule | None:
    """
    Обновить расписание списания.
    """
    stmt = select(WriteOffSchedule).where(WriteOffSchedule.id == schedule_id)
    result = await session.execute(stmt)
    schedule = result.scalar_one_or_none()

    if not schedule:
        return None

    if interval_days is not None:
        schedule.interval_days = interval_days
    if quantity_per_writeoff is not None:
        schedule.quantity_per_writeoff = quantity_per_writeoff
    if is_active is not None:
        schedule.is_active = is_active

    await session.flush()
    return schedule


async def delete_writeoff_schedule(
        session: AsyncSession,
        schedule_id: int,
) -> bool:
    """
    Удалить расписание списания.
    """
    stmt = select(WriteOffSchedule).where(WriteOffSchedule.id == schedule_id)
    result = await session.execute(stmt)
    schedule = result.scalar_one_or_none()

    if not schedule:
        return False

    await session.delete(schedule)
    await session.flush()
    return True