from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.api_v1.fastapi_users_router import fastapi_users
from api.dependencies.authentication.perm import require_permission
from core.config import settings
from core.models import User, db_helper
from core.permissions import Permission
from utils import QRCodeScanner
from core.schemas.receipt import (
    ReceiptRead,
    ReceiptConfirmRequest,
    ReceiptUploadResponse,
)
from crud.receipt import (
    save_receipt,
    get_receipt_by_id,
    find_duplicate_receipt,
    get_all_receipts, delete_receipt_by_id,
)
from crud.category import categorize_products

router = APIRouter(
    prefix=settings.api.v1.receipts,
    tags=["Receipts"],
)

current_user = fastapi_users.current_user(active=True)

qr_scanner = QRCodeScanner(
    api_token=settings.receipt_api.token,
    api_url=settings.receipt_api.url
)

@router.post("/upload", response_model=ReceiptUploadResponse)
async def upload_receipt_photo(
        file: UploadFile = File(...),
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)] = None,
        user: User = Depends(current_user),
):
    """
    Загрузить фото чека и получить обработанные данные.

    1. Принимает фото чека
    2. Сканирует QR-код и получает данные от API
    3. Проверяет, существует ли уже такой чек
    4. Если чек уже есть - возвращает сообщение о дубликате
    5. Если чек новый - категоризирует товары и возвращает чек с категориями
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        return ReceiptUploadResponse(
            success=False,
            error="Файл должен быть изображением (JPEG, PNG и т.д.)"
        )

    try:
        image_bytes = await file.read()
    except Exception as e:
        return ReceiptUploadResponse(
            success=False,
            error=f"Не удалось прочитать файл: {str(e)}"
        )

    result = await qr_scanner.scan_receipt_image(image_bytes)

    if not result["success"]:
        return ReceiptUploadResponse(
            success=False,
            error=result.get("message", "Не удалось обработать изображение")
        )

    api_response = result.get("api_response", {})
    if not api_response.get("success"):
        return ReceiptUploadResponse(
            success=False,
            error=api_response.get("error", "API вернул ошибку")
        )

    try:
        from datetime import datetime
        from core.schemas.receipt import ReceiptItemRead

        api_data = api_response.get("data", {}).get("json", {})

        fiscal_number = result["fns"].get("fn")
        fiscal_document = result["fns"].get("i")
        fiscal_sign = result["fns"].get("fp")

        existing_receipt = await find_duplicate_receipt(
            session,
            fiscal_number,
            fiscal_document,
            fiscal_sign,
        )

        if existing_receipt:
            return ReceiptUploadResponse(
                success=True,
                is_duplicate=True,
                message="Чек с такими фискальными данными уже существует в системе",
            )

        items_data = result.get("items", [])
        product_names = [item.get("name", "") for item in items_data]
        categories = await categorize_products(product_names)

        # Формируем данные чека
        date_buy_str = result["fns"].get("datetime", api_data.get("dateTime", ""))
        date_buy = datetime.fromisoformat(
            date_buy_str.replace('T', ' ').split('.')[0]
        )

        receipt_items = []
        for item in items_data:
            item_name = item.get("name", "")
            receipt_items.append(
                ReceiptItemRead(
                    id=0,
                    receipt_id=0,
                    product_name=item_name,
                    count_product=float(item.get("quantity", 0)),
                    unit_price=float(item.get("price", 0)) / 100,
                    sum=float(item.get("sum", 0)) / 100,
                    category_name=categories.get(item_name),
                )
            )

        new_receipt = ReceiptRead(
            id=None,
            order_name=None,
            fiscal_number=fiscal_number,
            fiscal_document=fiscal_document,
            fiscal_sign=fiscal_sign,
            sum=float(api_data.get("totalSum", 0)) / 100,
            date_buy=date_buy,
            name_supplier=api_data.get("user", api_data.get("userInn", "")),
            user_id=user.id,
            date_create=None,
            items=receipt_items,
        )

        return ReceiptUploadResponse(
            success=True,
            is_duplicate=False,
            receipt=new_receipt,
            message="Чек успешно обработан и категоризирован",
        )

    except Exception as e:
        return ReceiptUploadResponse(
            success=False,
            error=f"Ошибка обработки данных чека: {str(e)}"
        )


@router.post("/confirm", response_model=ReceiptRead, status_code=status.HTTP_201_CREATED)
async def confirm_and_save_receipt(
        request: ReceiptConfirmRequest,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Подтвердить и сохранить чек.

    1. Создаем чек в БД
    2. Для каждого товара создаем/находим Product в каталоге
    3. Создаем ReceiptItem с привязкой к Product
    4. Обновляем остатки на складе
    5. Возвращаем сохраненный чек
    """
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


@router.get("/", response_model=list[ReceiptRead])
async def get_all_receipts_list(
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
        skip: int = 0,
        limit: int = 100,
):
    """
    Получить список всех чеков
    """
    receipts = await get_all_receipts(session, skip, limit)
    return receipts


@router.get("/{receipt_id}", response_model=ReceiptRead)
async def get_receipt(
        receipt_id: int,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(current_user),
):
    """
    Получить чек по ID.
    """
    receipt = await get_receipt_by_id(session, receipt_id)

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Чек с ID {receipt_id} не найден",
        )

    return receipt


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receipt(
        receipt_id: int,
        session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
        user: User = Depends(require_permission(Permission.RECEIPT_DELETE)),
):
    """
    Удалить чек по ID.
    """
    success = await delete_receipt_by_id(session, receipt_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Чек с ID {receipt_id} не найден",
        )

    return None