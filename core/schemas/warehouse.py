from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class WarehouseRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    category_name: str | None
    rest: Decimal
    last_update: datetime

    class Config:
        from_attributes = True


class WarehouseUpdate(BaseModel):
    rest: Decimal = Field(..., ge=0, description="Новый остаток товара")
