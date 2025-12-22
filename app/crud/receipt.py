from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Receipt, ReceiptItem, Product, Category
from core.schemas.receipt import (
    ReceiptRead,
    ReceiptItemRead,
    ReceiptItemBase,
    QRCodeData,
    ReceiptPreview,
)
from crud.category import categorize_products, get_category_by_name, get_or_create_category
from crud.warehouse import update_warehouse_stock


async def find_duplicate_receipt(
        session: AsyncSession,
        fiscal_number: str | None,
        fiscal_document: str | None,
        fiscal_sign: str | None,
) -> Receipt | None:
    """
    Найти дубликат чека по фискальным данным.

    Returns:
        Существующий чек или None
    """
    if not all([fiscal_number, fiscal_document, fiscal_sign]):
        return None

    stmt = (
        select(Receipt)
        .where(
            Receipt.fiscal_number == fiscal_number,
            Receipt.fiscal_document == fiscal_document,
            Receipt.fiscal_sign == fiscal_sign,
        )
        .options(selectinload(Receipt.items))
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def prepare_receipt_preview(
        session: AsyncSession,
        order_name: str | None,
        qr_data: QRCodeData,
) -> ReceiptPreview:
    """
    Подготовить предпросмотр чека с категоризацией товаров.

    1. Проверяет дубликаты
    2. Категоризирует товары через ML/AI
    3. Возвращает новый чек и (если есть) существующий

    Args:
        session: Сессия БД
        order_name: Название заказа
        qr_data: Данные из QR-кода

    Returns:
        ReceiptPreview с новым и возможно существующим чеком
    """
    # 1. Проверяем дубликаты
    existing_receipt = await find_duplicate_receipt(
        session,
        qr_data.fiscal_number,
        qr_data.fiscal_document,
        qr_data.fiscal_sign,
    )

    # 2. Категоризируем товары из нового чека
    product_names = [item.name for item in qr_data.items]
    categories = await categorize_products(product_names)

    # 3. Формируем новый чек (не сохраняем в БД!)
    date_buy = datetime.fromisoformat(
        qr_data.date_buy.replace('T', ' ').split('.')[0]
    )

    new_items = []
    for idx, item in enumerate(qr_data.items):
        new_items.append(
            ReceiptItemRead(
                id=-(idx + 1),  # Временный отрицательный ID
                receipt_id=-1,  # Временный ID
                product_name=item.name,
                count_product=item.quantity,
                unit_price=item.price,
                sum=item.sum,
                product_id=None,
                category_name=categories.get(item.name),
            )
        )

    new_receipt = ReceiptRead(
        id=None,  # Новый чек не имеет ID
        order_name=order_name,
        fiscal_number=qr_data.fiscal_number,
        fiscal_document=qr_data.fiscal_document,
        fiscal_sign=qr_data.fiscal_sign,
        sum=qr_data.sum,
        date_buy=date_buy,
        name_supplier=qr_data.name_supplier,
        user_id=None,
        date_create=None,
        items=new_items,
    )

    # 4. Если есть существующий чек, преобразуем его
    existing_receipt_read = None
    if existing_receipt:
        existing_items = [
            ReceiptItemRead(
                id=item.id,
                receipt_id=item.receipt_id,
                product_name=item.product_name,
                count_product=item.count_product,
                unit_price=item.unit_price,
                sum=item.sum,
                product_id=item.product_id,
                category_name=None,  # У старого чека может не быть
            )
            for item in existing_receipt.items
        ]

        existing_receipt_read = ReceiptRead(
            id=existing_receipt.id,
            order_name=existing_receipt.order_name,
            fiscal_number=existing_receipt.fiscal_number,
            fiscal_document=existing_receipt.fiscal_document,
            fiscal_sign=existing_receipt.fiscal_sign,
            sum=existing_receipt.sum,
            date_buy=existing_receipt.date_buy,
            name_supplier=existing_receipt.name_supplier,
            user_id=existing_receipt.user_id,
            date_create=existing_receipt.date_create,
            items=existing_items,
        )

    return ReceiptPreview(
        new_receipt=new_receipt,
        existing_receipt=existing_receipt_read,
        has_duplicate=existing_receipt is not None,
    )


async def get_or_create_product(
        session: AsyncSession,
        product_name: str,
        category_name: str,
) -> Product:
    """
    Получить товар из каталога или создать новый.

    Args:
        session: Сессия БД
        product_name: Название товара
        category_name: Название категории

    Returns:
        Товар из каталога
    """
    # Ищем товар по названию
    stmt = select(Product).where(Product.name == product_name)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if product:
        return product

    # Если товара нет, создаем
    category = await get_or_create_category(session, category_name)

    product = Product(
        name=product_name,
        category_id=category.id,
    )
    session.add(product)
    await session.flush()

    return product


async def save_receipt(
        session: AsyncSession,
        order_name: str | None,
        fiscal_number: str | None,
        fiscal_document: str | None,
        fiscal_sign: str | None,
        sum: float,
        date_buy: datetime,
        name_supplier: str | None,
        items: list[ReceiptItemBase],
        user_id: int,
) -> Receipt:
    """
    Сохранить подтвержденный чек в БД.

    1. Создает чек
    2. Для каждого товара создает/находит Product
    3. Создает ReceiptItem с привязкой к Product

    Args:
        session: Сессия БД
        order_name, fiscal_*, sum, date_buy, name_supplier: Данные чека
        items: Позиции чека с категориями
        user_id: ID пользователя

    Returns:
        Сохраненный чек
    """
    # 1. Проверяем дубликат еще раз
    existing = await find_duplicate_receipt(
        session, fiscal_number, fiscal_document, fiscal_sign
    )
    is_duplicate = existing is not None

    # 2. Создаем чек
    new_receipt = Receipt(
        order_name=order_name,
        fiscal_number=fiscal_number,
        fiscal_document=fiscal_document,
        fiscal_sign=fiscal_sign,
        sum=sum,
        date_buy=date_buy,
        name_supplier=name_supplier,
        is_duplicate=is_duplicate,
        user_id=user_id,
    )

    session.add(new_receipt)
    await session.flush()

    # 3. Создаем позиции чека и обновляем склад
    for item_data in items:
        # Получаем/создаем товар в каталоге
        product = None
        if item_data.category_name:
            product = await get_or_create_product(
                session,
                item_data.product_name,
                item_data.category_name,
            )

        # Создаем позицию чека
        receipt_item = ReceiptItem(
            receipt_id=new_receipt.id,
            product_name=item_data.product_name,
            count_product=item_data.count_product,
            unit_price=item_data.unit_price,
            sum=item_data.sum,
            product_id=product.id if product else None,
        )
        session.add(receipt_item)

        # Обновляем остаток на складе (если товар создан/найден)
        if product:
            await update_warehouse_stock(
                session,
                product.id,
                Decimal(item_data.count_product),
            )

    await session.commit()

    # Загружаем позиции
    stmt = (
        select(Receipt)
        .where(Receipt.id == new_receipt.id)
        .options(
            selectinload(Receipt.items).selectinload(ReceiptItem.product).selectinload(Product.category)
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_receipt_by_id(
        session: AsyncSession,
        receipt_id: int,
) -> Receipt | None:
    """Получить чек по ID с позициями"""
    from core.models import Product, Category

    stmt = (
        select(Receipt)
        .where(Receipt.id == receipt_id)
        .options(
            selectinload(Receipt.items).selectinload(ReceiptItem.product).selectinload(Product.category)
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()



async def get_all_receipts(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
) -> list[Receipt]:
    """Получить все чеки с пагинацией"""
    from core.models import Product, Category

    stmt = (
        select(Receipt)
        .options(
            selectinload(Receipt.items).selectinload(ReceiptItem.product).selectinload(Product.category)
        )
        .offset(skip)
        .limit(limit)
        .order_by(Receipt.date_create.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())