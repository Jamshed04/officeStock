from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from typing import Any


# === Схемы для позиций чека ===

class ReceiptItemBase(BaseModel):
    """Базовая схема позиции чека"""
    product_name: str = Field(..., max_length=500, description="Название товара из чека")
    count_product: float = Field(..., gt=0, description="Количество товара")
    unit_price: float = Field(..., ge=0, description="Цена за единицу")
    sum: float = Field(..., ge=0, description="Общая стоимость позиции")
    product_id: int | None = Field(None, description="ID товара из каталога (если сопоставлен)")
    category_name: str | None = Field(None, description="Категория товара")


class ReceiptItemCreate(ReceiptItemBase):
    """Схема для создания позиции чека"""
    pass


class ReceiptItemRead(ReceiptItemBase):
    """Схема для чтения позиции чека"""
    id: int
    receipt_id: int

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_category_name(cls, data: Any) -> Any:
        """Извлекаем category_name из связанного объекта product"""
        # Если data - это словарь, просто возвращаем его
        if isinstance(data, dict):
            return data

        # Если это объект ORM, извлекаем данные
        category_name = None
        if hasattr(data, 'product') and data.product:
            if hasattr(data.product, 'category') and data.product.category:
                category_name = data.product.category.name

        # Возвращаем словарь с данными
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


# === Схемы для чека ===

class ReceiptBase(BaseModel):
    """Базовая схема чека"""
    fiscal_number: str | None = Field(None, max_length=50, description="ФН из QR-кода")
    fiscal_document: str | None = Field(None, max_length=50, description="ФД из QR-кода")
    fiscal_sign: str | None = Field(None, max_length=50, description="ФП из QR-кода")
    sum: float = Field(..., ge=0, description="Общая сумма чека")
    date_buy: datetime = Field(..., description="Дата покупки")
    name_supplier: str | None = Field(None, max_length=255, description="Название поставщика")


class ReceiptCreate(ReceiptBase):
    """Схема для создания чека"""
    order_name: str | None = Field(None, max_length=255, description="Название заказа")
    items: list[ReceiptItemCreate] = Field(..., min_length=1, description="Позиции чека")


class ReceiptRead(ReceiptBase):
    """Схема для чтения чека"""
    id: int | None = Field(None, description="ID чека (None для нового)")
    order_name: str | None = None
    user_id: int | None = None
    date_create: datetime | None = None
    items: list[ReceiptItemRead] = []

    class Config:
        from_attributes = True


# === Схема для парсинга QR-кода ===

class QRCodeItem(BaseModel):
    """Товар из QR-кода (от внешнего API)"""
    name: str
    price: Decimal
    quantity: Decimal
    sum: Decimal


class QRCodeData(BaseModel):
    """Данные из QR-кода после парсинга"""
    fiscal_number: str | None = None  # fn
    fiscal_document: str | None = None  # i (fd)
    fiscal_sign: str | None = None  # fp
    date_buy: str  # datetime из json.datetime или fns.datetime
    sum: Decimal  # Общая сумма
    name_supplier: str | None = None  # user
    items: list[QRCodeItem]


class ReceiptPreview(BaseModel):
    """Предпросмотр чека с категориями товаров"""
    new_receipt: ReceiptRead
    existing_receipt: ReceiptRead | None = None
    has_duplicate: bool = False


class QRCodeParseResponse(BaseModel):
    """Ответ от функции парсинга QR-кода (для клиента)"""
    success: bool
    data: QRCodeData | None = None
    error: str | None = None


class ReceiptUploadResponse(BaseModel):
    """Ответ на загрузку фото чека"""
    success: bool
    is_duplicate: bool = False
    message: str | None = None
    receipt: ReceiptRead | None = None
    error: str | None = None


class ReceiptValidateRequest(BaseModel):
    """Запрос на валидацию чека"""
    order_name: str | None
    qr_data: QRCodeData


class ReceiptConfirmRequest(BaseModel):
    """Подтверждение чека пользователем"""
    order_name: str | None
    fiscal_number: str | None
    fiscal_document: str | None
    fiscal_sign: str | None
    sum: float
    date_buy: datetime
    name_supplier: str | None
    items: list[ReceiptItemBase]