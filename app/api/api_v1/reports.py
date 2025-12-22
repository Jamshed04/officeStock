from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users_router import fastapi_users
from core.models import User, db_helper
from core.schemas.report import ExpenseReportCompanyResponse, ExpenseReportResponse
from crud.reports import get_expenses_by_company, get_expenses_by_category

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

current_user = fastapi_users.current_user(active=True)

@router.get("/expenses", response_model=ExpenseReportResponse)
async def get_expenses_report(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    start_date: date = Query(..., description="Start date of the report period"),
    end_date: date = Query(..., description="End date of the report period"),
    user: User = Depends(current_user),
):
    """
    Get expense report by category for a specific period.
    """
    return await get_expenses_by_category(
        session=session,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/expenses-by-company", response_model=ExpenseReportCompanyResponse)
async def get_expenses_by_company_report(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    start_date: date = Query(..., description="Start date of the report period"),
    end_date: date = Query(..., description="End date of the report period"),
    user: User = Depends(current_user),
):
    """
    Get expense report by company (supplier) for a specific period.
    """
    return await get_expenses_by_company(
        session=session,
        start_date=start_date,
        end_date=end_date
    )

