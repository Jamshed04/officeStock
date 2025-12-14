from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users_router import fastapi_users
from core.config import settings
from core.models import User, db_helper
from utils import QRCodeScanner
from core.schemas.receipt import (
    ReceiptRead,
    ReceiptPreview,
    ReceiptValidateRequest,
    ReceiptConfirmRequest,
    QRCodeParseResponse,
    QRCodeData,
    QRCodeItem,
)
from crud.receipt import (
    prepare_receipt_preview,
    save_receipt,
    get_receipt_by_id,
)

router = APIRouter(
    prefix=settings.api.v1.receipts,
    tags=["Receipts"],
)

current_user = fastapi_users.current_user(active=True)

# Инициализация QR сканера
qr_scanner = QRCodeScanner(
    api_token=settings.receipt_api.token,
    api_url=settings.receipt_api.url
)


# ============================================================================
# RECEIPTS - Работа с чеками
# ============================================================================

@router.post("/parse-qr", response_model=QRCodeParseResponse)
async def parse_qr_code(file: UploadFile = File(...)):
    """
    Парсинг QR-кода с фотографии чека.

    Принимает изображение чека, сканирует QR-код и получает данные о чеке от API.

    Поддерживает:
    - Фотографии чеков целиком (не только QR-код)
    - Разные углы съёмки
    - Плохое освещение
    - Низкое качество изображения

    Returns:
        QRCodeParseResponse с данными чека или ошибкой
    """
    # Проверяем тип файла
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть изображением (JPEG, PNG и т.д.)"
        )

    # Читаем изображение
    try:
        image_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось прочитать файл: {str(e)}"
        )

    # Сканируем QR-код и получаем данные
    result = await qr_scanner.scan_receipt_image(image_bytes)
    print("DEBUG: QR raw:", result.get("qr_raw"))

    if not result["success"]:
        return QRCodeParseResponse(
            success=False,
            error=result.get("message", "Не удалось обработать изображение")
        )

    # Проверяем успешность получения данных от API
    api_response = result.get("api_response", {})
    if not api_response.get("success"):
        return QRCodeParseResponse(
            success=False,
            error=api_response.get("error", "API вернул ошибку")
        )

    # Извлекаем данные чека из API ответа
    try:
        api_data = api_response.get("data", {}).get("json", {})

        # Формируем данные чека
        qr_data = QRCodeData(
            fiscal_number=result["fns"].get("fn"),
            fiscal_document=result["fns"].get("i"),
            fiscal_sign=result["fns"].get("fp"),
            date_buy=result["fns"].get("datetime", api_data.get("dateTime", "")),
            sum=float(api_data.get("totalSum", 0)) / 100,  # API возвращает сумму в копейках
            name_supplier=api_data.get("user", api_data.get("userInn", "")),
            items=[
                QRCodeItem(
                    name=item.get("name", ""),
                    price=float(item.get("price", 0)) / 100,
                    quantity=float(item.get("quantity", 0)),
                    sum=float(item.get("sum", 0)) / 100,
                )
                for item in result.get("items", [])
            ],
        )

        return QRCodeParseResponse(
            success=True,
            data=qr_data,
        )

    except Exception as e:
        return QRCodeParseResponse(
            success=False,
            error=f"Ошибка обработки данных чека: {str(e)}"
        )


@router.post("/validate", response_model=ReceiptPreview)
async def validate_receipt(
        request: ReceiptValidateRequest,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Валидировать чек перед сохранением.

    Шаг 1: Клиент отправляет данные из QR-кода

    Сервер:
    1. Проверяет дубликаты (возвращает старый чек если есть)
    2. Категоризирует товары через AI/ML
    3. Возвращает новый чек с категориями + старый чек (если дубликат)

    Клиент показывает оба чека пользователю для выбора.
    """
    # Подготавливаем предпросмотр
    preview = await prepare_receipt_preview(
        session,
        request.order_name,
        request.qr_data,
    )

    return preview


@router.post("/confirm", response_model=ReceiptRead, status_code=status.HTTP_201_CREATED)
async def confirm_and_save_receipt(
        request: ReceiptConfirmRequest,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Подтвердить и сохранить чек.

    Шаг 2: Пользователь выбрал чек (новый или старый) и нажал "Подтвердить"

    Сервер:
    1. Создает чек в БД
    2. Для каждого товара создает/находит Product в каталоге
    3. Создает ReceiptItem с привязкой к Product
    4. Обновляет остатки на складе
    5. Возвращает сохраненный чек
    """
    # Сохраняем чек
    receipt = await save_receipt(
        session=session,
        order_name=request.order_name,
        fiscal_number=request.fiscal_number,
        fiscal_document=request.fiscal_document,
        fiscal_sign=request.fiscal_sign,
        sum=request.sum,
        date_buy=request.date_buy,
        name_supplier=request.name_supplier,
        items=request.items,
        user_id=user.id,
    )

    return receipt


@router.get("/{receipt_id}", response_model=ReceiptRead)
async def get_receipt(
        receipt_id: int,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Получить чек по ID со всеми позициями.
    """
    receipt = await get_receipt_by_id(session, receipt_id)

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Чек с ID {receipt_id} не найден",
        )

    return receipt


# @router.get("/", response_model=list[ReceiptRead])
# async def get_all_receipts_list(
#         session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
#         user: User = Depends(current_user),
#         skip: int = 0,
#         limit: int = 100,
# ):
#     """
#     Получить список всех чеков.
#     """
#     receipts = await get_all_receipts(session, skip, limit)
#     return receipts