from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users_router import fastapi_users
from core.config import settings
from core.models import User, db_helper
from core.schemas.writeoff import (
    WriteOffScheduleCreate,
    WriteOffScheduleRead,
    WriteOffScheduleUpdate,
)
from crud.writeoff import (
    create_writeoff_schedule,
    update_writeoff_schedule,
    delete_writeoff_schedule,
    get_active_writeoff_schedules,
)
from sqlalchemy import select
from core.models import WriteOffSchedule

router = APIRouter(
    prefix="/writeoff",
    tags=["Write-off Schedules"],
)

current_user = fastapi_users.current_user(active=True)


@router.post("/", response_model=WriteOffScheduleRead, status_code=status.HTTP_201_CREATED)
async def create_schedule(
        schedule_data: WriteOffScheduleCreate,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Создать расписание списания для товара.
    """
    schedule = await create_writeoff_schedule(
        session=session,
        product_id=schedule_data.product_id,
        interval_days=schedule_data.interval_days,
        quantity_per_writeoff=schedule_data.quantity_per_writeoff,
    )
    await session.commit()
    await session.refresh(schedule)
    return schedule


@router.get("/", response_model=list[WriteOffScheduleRead])
async def get_all_schedules(
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
        active_only: bool = False,
):
    """
    Получить все расписания списания.

    Args:
        active_only: Если True, возвращает только активные расписания
    """
    if active_only:
        schedules = await get_active_writeoff_schedules(session)
    else:
        stmt = select(WriteOffSchedule)
        result = await session.execute(stmt)
        schedules = list(result.scalars().all())

    return schedules


@router.get("/{schedule_id}", response_model=WriteOffScheduleRead)
async def get_schedule(
        schedule_id: int,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Получить расписание списания по ID.
    """
    stmt = select(WriteOffSchedule).where(WriteOffSchedule.id == schedule_id)
    result = await session.execute(stmt)
    schedule = result.scalar_one_or_none()

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Расписание с ID {schedule_id} не найдено"
        )

    return schedule


@router.patch("/{schedule_id}", response_model=WriteOffScheduleRead)
async def update_schedule(
        schedule_id: int,
        schedule_data: WriteOffScheduleUpdate,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Обновить расписание списания.
    """
    schedule = await update_writeoff_schedule(
        session=session,
        schedule_id=schedule_id,
        interval_days=schedule_data.interval_days,
        quantity_per_writeoff=schedule_data.quantity_per_writeoff,
        is_active=schedule_data.is_active,
    )

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Расписание с ID {schedule_id} не найдено"
        )

    await session.commit()
    await session.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
        schedule_id: int,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Удалить расписание списания.
    """
    deleted = await delete_writeoff_schedule(session=session, schedule_id=schedule_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Расписание с ID {schedule_id} не найдено"
        )

    await session.commit()

