"""
Эндпоинты для работы со складом.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.dependencies.authentication.perm import current_user, require_permission
from core.config import settings
from core.models import db_helper, Warehouse, Product, Category, User
from core.schemas.warehouse import (
    WarehouseRead,
    WarehouseUpdate,
)
from core.permissions import Permission

router = APIRouter(
    prefix=settings.api.v1.warehouse,
    tags=["Warehouse"],
)


@router.get("/products", response_model=list[WarehouseRead])
async def get_warehouse_products(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(require_permission(Permission.WAREHOUSE_READ)),
    skip: int = 0,
    limit: int = 100,
):
    """
    Получить список товаров на складе с остатками.
    """
    stmt = (
        select(Warehouse)
        .options(
            selectinload(Warehouse.product).selectinload(Product.category)
        )
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    warehouse_items = result.scalars().all()

    items_list = []
    for item in warehouse_items:
        items_list.append(
            WarehouseRead(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                category_name=item.product.category.name if item.product.category else None,
                rest=item.rest,
                last_update=item.last_update,
            )
        )

    return items_list


@router.get("/products/{product_id}", response_model=WarehouseRead)
async def get_warehouse_product(
    product_id: int,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(require_permission(Permission.WAREHOUSE_READ)),
):
    """
    Получить информацию о конкретном товаре на складе.
    """
    stmt = (
        select(Warehouse)
        .where(Warehouse.product_id == product_id)
        .options(
            selectinload(Warehouse.product).selectinload(Product.category)
        )
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден на складе",
        )

    return WarehouseRead(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product.name,
        category_name=item.product.category.name if item.product.category else None,
        rest=item.rest,
        last_update=item.last_update,
    )


@router.patch("/products/{product_id}", response_model=WarehouseRead)
async def update_warehouse_product(
    product_id: int,
    update_data: WarehouseUpdate,
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    user: User = Depends(require_permission(Permission.WAREHOUSE_UPDATE)),
):
    """
    Обновить остаток товара на складе.
    """
    stmt = (
        select(Warehouse)
        .where(Warehouse.product_id == product_id)
        .options(
            selectinload(Warehouse.product).selectinload(Product.category)
        )
    )
    result = await session.execute(stmt)
    warehouse_item = result.scalar_one_or_none()

    if not warehouse_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден на складе",
        )

    if update_data.rest == 0:
        await session.delete(warehouse_item)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Товар удален из склада (остаток = 0)",
        )

    warehouse_item.rest = update_data.rest

    await session.commit()

    await session.refresh(warehouse_item)
    stmt_reload = (
        select(Warehouse)
        .where(Warehouse.id == warehouse_item.id)
        .options(
            selectinload(Warehouse.product).selectinload(Product.category)
        )
    )
    result_reload = await session.execute(stmt_reload)
    warehouse_item = result_reload.scalar_one()

    return WarehouseRead(
        id=warehouse_item.id,
        product_id=warehouse_item.product_id,
        product_name=warehouse_item.product.name,
        category_name=warehouse_item.product.category.name if warehouse_item.product.category else None,
        rest=warehouse_item.rest,
        last_update=warehouse_item.last_update,
    )
