from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import WriteOffSchedule, Warehouse, Product


async def get_active_writeoff_schedules(
        session: AsyncSession,
) -> list[WriteOffSchedule]:
    """
    Получить все активные расписания списания.

    Args:
        session: Сессия БД

    Returns:
        Список активных расписаний
    """
    stmt = (
        select(WriteOffSchedule)
        .where(WriteOffSchedule.is_active == True)
        .options(selectinload(WriteOffSchedule.product))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def process_writeoffs(session: AsyncSession) -> dict:
    """
    Обработать все расписания списания.

    Проверяет каждое активное расписание:
    - Если прошло достаточно дней с последнего списания, списывает товар
    - Если товара нет на складе или остаток стал 0, деактивирует расписание

    Args:
        session: Сессия БД

    Returns:
        Словарь с результатами обработки
    """
    schedules = await get_active_writeoff_schedules(session)
    now = datetime.now()

    results = {
        "processed": 0,
        "written_off": 0,
        "deactivated": 0,
        "errors": []
    }

    for schedule in schedules:
        try:
            # Проверяем, нужно ли списывать
            should_writeoff = False

            if schedule.last_writeoff_date is None:
                # Первое списание - списываем сразу
                should_writeoff = True
            else:
                # Проверяем, прошло ли достаточно дней
                days_since_last = (now - schedule.last_writeoff_date).days
                if days_since_last >= schedule.interval_days:
                    should_writeoff = True

            if not should_writeoff:
                continue

            results["processed"] += 1

            # Получаем запись склада для товара
            stmt = select(Warehouse).where(Warehouse.product_id == schedule.product_id)
            result = await session.execute(stmt)
            warehouse_record = result.scalar_one_or_none()

            # Если товара нет на складе, деактивируем расписание
            if warehouse_record is None:
                schedule.is_active = False
                results["deactivated"] += 1
                await session.flush()
                continue

            # Проверяем остаток
            if warehouse_record.rest <= 0:
                # Остаток уже 0, деактивируем расписание
                schedule.is_active = False
                results["deactivated"] += 1
                await session.flush()
                continue

            # Списываем товар
            quantity_to_writeoff = schedule.quantity_per_writeoff

            # Если остаток меньше количества для списания, списываем весь остаток
            if warehouse_record.rest < quantity_to_writeoff:
                quantity_to_writeoff = warehouse_record.rest

            warehouse_record.rest -= quantity_to_writeoff

            # Обновляем дату последнего списания
            schedule.last_writeoff_date = now

            # Если остаток стал 0, деактивируем расписание
            if warehouse_record.rest <= 0:
                schedule.is_active = False
                results["deactivated"] += 1

            results["written_off"] += 1
            await session.flush()

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

    Args:
        session: Сессия БД
        product_id: ID товара
        interval_days: Интервал списания в днях
        quantity_per_writeoff: Количество для списания за раз

    Returns:
        Созданное расписание
    """
    # Проверяем, нет ли уже расписания для этого товара
    stmt = select(WriteOffSchedule).where(WriteOffSchedule.product_id == product_id)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # Обновляем существующее расписание
        existing.interval_days = interval_days
        existing.quantity_per_writeoff = quantity_per_writeoff
        existing.is_active = True
        await session.flush()
        return existing

    # Создаем новое расписание
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

    Args:
        session: Сессия БД
        schedule_id: ID расписания
        interval_days: Новый интервал списания
        quantity_per_writeoff: Новое количество для списания
        is_active: Активность расписания

    Returns:
        Обновленное расписание или None
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

    Args:
        session: Сессия БД
        schedule_id: ID расписания

    Returns:
        True если удалено, False если не найдено
    """
    stmt = select(WriteOffSchedule).where(WriteOffSchedule.id == schedule_id)
    result = await session.execute(stmt)
    schedule = result.scalar_one_or_none()

    if not schedule:
        return False

    await session.delete(schedule)
    await session.flush()
    return True

