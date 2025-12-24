"""
Эндпоинты для работы с категориями товаров.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.authentication.perm import current_user, require_permission
from core.config import settings
from core.models import db_helper, Category, User
from core.schemas.category import (
    CategoryRead,
    CategoryCreate,
    CategoryDelete,
)
from core.permissions import Permission

router = APIRouter(
    prefix=settings.api.v1.categories,
    tags=["Categories"],
)


@router.get("/", response_model=list[CategoryRead])
async def get_all_categories(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(current_user),
):
    """
    Получить список всех категорий.
    """
    stmt = select(Category).order_by(Category.name)
    result = await session.execute(stmt)
    categories = result.scalars().all()
    return list(categories)


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(require_permission(Permission.CATEGORY_CREATE)),
):
    """
    Создать новую категорию.
    """
    stmt = select(Category).where(Category.name == category_data.name)
    result = await session.execute(stmt)
    existing_category = result.scalar_one_or_none()

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Категория с названием '{category_data.name}' уже существует",
        )

    new_category = Category(name=category_data.name)
    session.add(new_category)
    await session.commit()
    await session.refresh(new_category)

    return new_category


@router.delete("/", status_code=status.HTTP_200_OK)
async def delete_category(
    category_data: CategoryDelete,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(require_permission(Permission.CATEGORY_DELETE)),
):
    """
    Удалить категорию по названию.
    """
    stmt = select(Category).where(Category.name == category_data.name)
    result = await session.execute(stmt)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Категория с названием '{category_data.name}' не найдена",
        )

    await session.delete(category)
    await session.commit()

    return {
        "success": True,
        "message": f"Категория '{category_data.name}' успешно удалена",
    }
