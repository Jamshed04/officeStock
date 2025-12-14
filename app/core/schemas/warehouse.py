from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class WarehouseRead(BaseModel):
    """Данные о товаре на складе"""
    id: int
    product_id: int
    product_name: str
    category_name: str
    rest: Decimal
    last_update: datetime

    class Config:
        from_attributes = True


class WarehouseUpdate(BaseModel):
    """Обновление остатка товара на складе"""
    product_id: int = Field(..., description="ID товара")
    rest: Decimal = Field(..., ge=0, description="Новый остаток товара")
