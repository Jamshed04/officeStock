from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class WriteOffScheduleBase(BaseModel):
    product_id: int = Field(..., description="ID товара")
    interval_days: int = Field(..., gt=0, description="Интервал списания в днях")
    quantity_per_writeoff: float = Field(..., gt=0, description="Количество для списания за раз")


class WriteOffScheduleCreate(WriteOffScheduleBase):
    pass


class WriteOffScheduleUpdate(BaseModel):
    interval_days: int | None = Field(None, gt=0, description="Интервал списания в днях")
    quantity_per_writeoff: float | None = Field(None, gt=0, description="Количество для списания за раз")
    is_active: bool | None = Field(None, description="Активность расписания")


class WriteOffScheduleRead(WriteOffScheduleBase):
    id: int
    is_active: bool
    last_writeoff_date: datetime | None = None
    date_create: datetime

    class Config:
        from_attributes = True

