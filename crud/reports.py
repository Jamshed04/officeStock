from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import Receipt, ReceiptItem, Product, Category
from core.schemas.report import (
    ExpenseReportItem,
    ExpenseReportResponse,
    ExpenseReportCompanyItem,
    ExpenseReportCompanyResponse
)

async def get_expenses_by_category(
    session: AsyncSession,
    start_date: date,
    end_date: date
) -> ExpenseReportResponse:
    """
    Получить отчет по категориям за определенный период.
    """
    # Convert dates to datetime for comparison
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    stmt = (
        select(
            Category.name,
            func.sum(ReceiptItem.sum).label("total")
        )
        .join(Product, ReceiptItem.product_id == Product.id)
        .join(Category, Product.category_id == Category.id)
        .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
        .where(
            and_(
                Receipt.date_buy >= start_dt,
                Receipt.date_buy <= end_dt
            )
        )
        .group_by(Category.name)
    )

    result = await session.execute(stmt)
    rows = result.all()

    items = []
    total_sum = Decimal(0)

    for row in rows:
        amount = row.total or Decimal(0)
        items.append(ExpenseReportItem(
            category_name=row.name,
            total_amount=amount
        ))
        total_sum += amount

    return ExpenseReportResponse(
        total=total_sum,
        by_category=items
    )


async def get_expenses_by_company(
    session: AsyncSession,
    start_date: date,
    end_date: date
) -> ExpenseReportCompanyResponse:
    """
    Получить отчет по поставщикам за определенный период.
    """
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    stmt = (
        select(
            Receipt.name_supplier,
            func.sum(ReceiptItem.sum).label("total")
        )
        .join(Receipt, ReceiptItem.receipt_id == Receipt.id)
        .where(
            and_(
                Receipt.date_buy >= start_dt,
                Receipt.date_buy <= end_dt
            )
        )
        .group_by(Receipt.name_supplier)
    )

    result = await session.execute(stmt)
    rows = result.all()

    items = []
    total_sum = Decimal(0)

    for row in rows:
        amount = row.total or Decimal(0)
        items.append(ExpenseReportCompanyItem(
            company_name=row.name_supplier or "Unknown",
            total_amount=amount
        ))
        total_sum += amount

    return ExpenseReportCompanyResponse(
        total=total_sum,
        by_company=items
    )

