import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Category


async def categorize_products(product_names: list[str]) -> dict[str, str]:
    """
    ТЕСТОВАЯ функция категоризации товаров.

    В продакшене здесь будет ML-модель или AI API для определения категории.
    Сейчас возвращает случайную категорию из списка.

    Args:
        product_names: Список названий товаров

    Returns:
        Словарь {название_товара: категория}
    """
    # Тестовые категории
    test_categories = [
        "Молочные продукты",
        "Канцтовары",
        "Сладости",
        "Лекарства",
    ]

    result = {}
    for product_name in product_names:
        # В реальности здесь будет умная логика
        # Пока просто случайная категория
        result[product_name] = random.choice(test_categories)

    return result


async def get_category_by_name(
        session: AsyncSession,
        category_name: str,
) -> Category | None:
    """
    Получить категорию по названию.

    Args:
        session: Сессия БД
        category_name: Название категории

    Returns:
        Категория или None
    """
    stmt = select(Category).where(Category.name == category_name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_category(
        session: AsyncSession,
        category_name: str,
) -> Category:
    """
    Получить категорию или создать новую, если не существует.

    Args:
        session: Сессия БД
        category_name: Название категории

    Returns:
        Категория
    """
    category = await get_category_by_name(session, category_name)

    if not category:
        category = Category(name=category_name)
        session.add(category)
        await session.flush()

    return category