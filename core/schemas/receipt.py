from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from typing import Any


# === Схемы для позиций чека ===

class ReceiptItemBase(BaseModel):
    product_name: str = Field(..., max_length=500, description="Название товара из чека")
    count_product: float = Field(..., gt=0, description="Количество товара")
    unit_price: float = Field(..., ge=0, description="Цена за единицу")
    sum: float = Field(..., ge=0, description="Общая стоимость позиции")
    product_id: int | None = Field(None, description="ID товара из каталога (если сопоставлен)")
    category_name: str | None = Field(None, description="Категория товара")


class ReceiptItemCreate(ReceiptItemBase):
    pass


class ReceiptItemRead(ReceiptItemBase):
    id: int
    receipt_id: int

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_category_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        category_name = None
        if hasattr(data, 'product') and data.product:
            if hasattr(data.product, 'category') and data.product.category:
                category_name = data.product.category.name

        return {
            'id': data.id,
            'receipt_id': data.receipt_id,
            'product_name': data.product_name,
            'count_product': float(data.count_product),
            'unit_price': float(data.unit_price),
            'sum': float(data.sum),
            'product_id': data.product_id if hasattr(data, 'product_id') else None,
            'category_name': category_name,
        }



class ReceiptBase(BaseModel):
    fiscal_number: str | None = Field(None, max_length=50, description="ФН из QR-кода")
    fiscal_document: str | None = Field(None, max_length=50, description="ФД из QR-кода")
    fiscal_sign: str | None = Field(None, max_length=50, description="ФП из QR-кода")
    sum: float = Field(..., ge=0, description="Общая сумма чека")
    date_buy: datetime = Field(..., description="Дата покупки")
    name_supplier: str | None = Field(None, max_length=255, description="Название поставщика")


class ReceiptCreate(ReceiptBase):
    order_name: str | None = Field(None, max_length=255, description="Название заказа")
    items: list[ReceiptItemCreate] = Field(..., min_length=1, description="Позиции чека")


class ReceiptRead(ReceiptBase):
    id: int | None = Field(None, description="ID чека (None для нового)")
    order_name: str | None = None
    user_id: int | None = None
    date_create: datetime | None = None
    items: list[ReceiptItemRead] = []

    class Config:
        from_attributes = True


class QRCodeItem(BaseModel):
    name: str
    price: Decimal
    quantity: Decimal
    sum: Decimal


class QRCodeData(BaseModel):
    fiscal_number: str | None = None  # fn
    fiscal_document: str | None = None  # i (fd)
    fiscal_sign: str | None = None  # fp
    date_buy: str  # datetime из json.datetime или fns.datetime
    sum: Decimal  # Общая сумма
    name_supplier: str | None = None  # user
    items: list[QRCodeItem]


class ReceiptPreview(BaseModel):
    new_receipt: ReceiptRead
    existing_receipt: ReceiptRead | None = None
    has_duplicate: bool = False


class QRCodeParseResponse(BaseModel):
    success: bool
    data: QRCodeData | None = None
    error: str | None = None


class ReceiptUploadResponse(BaseModel):
    success: bool
    is_duplicate: bool = False
    message: str | None = None
    receipt: ReceiptRead | None = None
    error: str | None = None


class ReceiptValidateRequest(BaseModel):
    order_name: str | None
    qr_data: QRCodeData


class ReceiptConfirmRequest(BaseModel):
    order_name: str | None
    fiscal_number: str | None
    fiscal_document: str | None
    fiscal_sign: str | None
    sum: float
    date_buy: datetime
    name_supplier: str | None
    items: list[ReceiptItemBase]