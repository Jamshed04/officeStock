from datetime import date
from decimal import Decimal
from pydantic import BaseModel

class ExpenseReportItem(BaseModel):
    category_name: str
    total_amount: Decimal

class ExpenseReportResponse(BaseModel):
    total: Decimal
    by_category: list[ExpenseReportItem]

class ExpenseReportCompanyItem(BaseModel):
    company_name: str | None
    total_amount: Decimal

class ExpenseReportCompanyResponse(BaseModel):
    total: Decimal
    by_company: list[ExpenseReportCompanyItem]
