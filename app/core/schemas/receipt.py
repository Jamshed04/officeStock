from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# === Схемы для позиций чека ===

class ReceiptItemBase(BaseModel):
    """Базовая схема позиции чека"""
    product_name: str = Field(..., max_length=500, description="Название товара из чека")
    count_product: Decimal = Field(..., gt=0, description="Количество товара")
    unit_price: Decimal = Field(..., ge=0, description="Цена за единицу")
    sum: Decimal = Field(..., ge=0, description="Общая стоимость позиции")
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


# === Схемы для чека ===

class ReceiptBase(BaseModel):
    """Базовая схема чека"""
    fiscal_number: str | None = Field(None, max_length=50, description="ФН из QR-кода")
    fiscal_document: str | None = Field(None, max_length=50, description="ФД из QR-кода")
    fiscal_sign: str | None = Field(None, max_length=50, description="ФП из QR-кода")
    sum: Decimal = Field(..., ge=0, description="Общая сумма чека")
    date_buy: datetime = Field(..., description="Дата покупки")
    name_supplier: str | None = Field(None, max_length=255, description="Название поставщика")


class ReceiptCreate(ReceiptBase):
    """Схема для создания чека"""
    order_id: int = Field(..., description="ID заказа")
    items: list[ReceiptItemCreate] = Field(..., min_length=1, description="Позиции чека")


class ReceiptRead(ReceiptBase):
    """Схема для чтения чека"""
    id: int | None = Field(None, description="ID чека (None для нового)")
    order_id: int
    is_duplicate: bool = False
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


class ReceiptValidateRequest(BaseModel):
    """Запрос на валидацию чека"""
    order_id: int
    qr_data: QRCodeData


class ReceiptConfirmRequest(BaseModel):
    """Подтверждение чека пользователем"""
    order_id: int
    fiscal_number: str | None
    fiscal_document: str | None
    fiscal_sign: str | None
    sum: Decimal
    date_buy: datetime
    name_supplier: str | None
    items: list[ReceiptItemBase]


class OrderCreate(BaseModel):
    """Создание заказа"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class OrderRead(BaseModel):
    """Чтение заказа"""
    id: int
    name: str
    description: str | None
    status_id: int
    user_id: int
    date_create: datetime
    date_update: datetime

    class Config:
        from_attributes = True


class OrderListItem(BaseModel):
    """Элемент списка заказов"""
    id: int
    name: str
    description: str | None

    class Config:
        from_attributes = True