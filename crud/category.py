from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from core.models import Category
from ml.model_loader import get_predictor


async def categorize_products(product_names: list[str]) -> dict[str, str]:

    if not product_names:
        return {}

    predictor = get_predictor()
    loop = asyncio.get_running_loop()

    try:
        ml_result = await loop.run_in_executor(
            None,
            predictor.predict,
            product_names
        )

        if not ml_result:
            return {name: "неизвестно" for name in product_names}

        categories = {
            name: data[1] if data and len(data) > 1 and data[1] else "неизвестно"
            for name, data in ml_result.items()
        }

        return categories

    except Exception as e:
        print(f"Ошибка при категоризации товаров: {e}")
        return {name: "неизвестно" for name in product_names}


async def get_category_by_name(
        session: AsyncSession,
        category_name: str,
) -> Category | None:
    """
    Получить категорию по названию.
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
    """
    category = await get_category_by_name(session, category_name)

    if category:
        return category

    category = Category(name=category_name)
    session.add(category)
    await session.flush()
    return category