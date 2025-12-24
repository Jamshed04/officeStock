"""
QR-код сканер для чеков с улучшенной обработкой изображений.
"""
from typing import Optional
import re
import io
from decimal import Decimal

from PIL import Image, ImageEnhance, ImageFilter
from pyzbar.pyzbar import decode, ZBarSymbol
import httpx


class QRCodeScanner:
    """Сканер QR-кодов с предобработкой изображений"""

    def __init__(self, api_token: str, api_url: str):
        self.api_token = api_token
        self.api_url = api_url

    def decode_qr_from_image(self, image: Image.Image) -> Optional[str]:
        """
        Извлекает QR-код из изображения с применением различных методов обработки.

        Пробует несколько стратегий:
        1. Исходное изображение
        2. Увеличение контраста
        3. Перевод в ч/б с высоким контрастом
        4. Повышение резкости
        5. Увеличение изображения
        6. Комбинация всех методов

        Args:
            image: PIL Image объект

        Returns:
            Строка с данными QR-кода или None
        """
        # Конвертируем в RGB если нужно
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Стратегия 1: Попытка с оригинальным изображением
        qr_data = self._try_decode(image)
        if qr_data:
            return qr_data

        # Стратегия 2: Увеличение контраста
        enhancer = ImageEnhance.Contrast(image)
        high_contrast = enhancer.enhance(2.0)
        qr_data = self._try_decode(high_contrast)
        if qr_data:
            return qr_data

        # Стратегия 3: Перевод в ч/б с пороговым значением
        grayscale = image.convert('L')
        # Адаптивная бинаризация через точечное преобразование
        threshold = 128
        bw_image = grayscale.point(lambda x: 255 if x > threshold else 0, mode='1')
        qr_data = self._try_decode(bw_image)
        if qr_data:
            return qr_data

        # Стратегия 4: Повышение резкости
        sharpened = image.filter(ImageFilter.SHARPEN)
        qr_data = self._try_decode(sharpened)
        if qr_data:
            return qr_data

        # Стратегия 5: Увеличение изображения (upscaling)
        # QR код может быть маленьким на фото
        width, height = image.size
        scaled_image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        qr_data = self._try_decode(scaled_image)
        if qr_data:
            return qr_data

        # Стратегия 6: Комбинация - масштабирование + контраст + резкость
        scaled_enhanced = scaled_image.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Contrast(scaled_enhanced)
        final_image = enhancer.enhance(2.5)
        qr_data = self._try_decode(final_image)
        if qr_data:
            return qr_data

        # Стратегия 7: Попробуем с разными порогами бинаризации
        grayscale = image.convert('L')
        for threshold in [100, 150, 180]:
            bw = grayscale.point(lambda x: 255 if x > threshold else 0, mode='1')
            qr_data = self._try_decode(bw)
            if qr_data:
                return qr_data

        return None

    def _try_decode(self, image: Image.Image) -> Optional[str]:
        """
        Пытается декодировать QR-код из изображения.

        Args:
            image: PIL Image объект

        Returns:
            Строка с данными QR-кода или None
        """
        try:
            decoded_objects = decode(image, symbols=[ZBarSymbol.QRCODE])
            if decoded_objects:
                return decoded_objects[0].data.decode('utf-8', errors='ignore')
        except Exception:
            pass
        return None

    def extract_fns_from_text(self, text: str) -> dict:
        """
        Извлекает параметры ФНС из строки QR-кода.

        Args:
            text: Строка с данными QR-кода

        Returns:
            Словарь с извлеченными параметрами
        """
        patterns = {
            "t": r"t[=/]([\dT]+)",
            "s": r"s[=/]([\d.]+)",
            "fn": r"fn[=/](\d+)",
            "i": r"i[=/](\d+)",
            "fp": r"fp[=/](\d+)",
            "n": r"n[=/](\d+)",
        }
        result = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result[key] = match.group(1)

        # Парсинг даты и времени из параметра t
        if "t" in result:
            raw = result["t"]
            if "T" in raw:
                date, time = raw.split("T")
                result["date"] = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
                result["time"] = f"{time[:2]}:{time[2:4]}"
                if len(time) >= 6:
                    result["time"] += f":{time[4:6]}"
                result["datetime"] = f"{result['date']} {result['time']}"

        return result

    async def fetch_receipt_from_api(self, qr_raw: str) -> dict:
        """
        Получает данные о чеке из внешнего API.

        Args:
            qr_raw: Строка с данными QR-кода

        Returns:
            Словарь с данными чека от API
        """
        payload = {
            "token": self.api_token,
            "qrraw": qr_raw
        }

        print("DEBUG: Sending to API:", payload)

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                r = await client.post(self.api_url, json=payload)
                print("DEBUG: API response status:", r.status_code)
                print("DEBUG: API response text:", r.text)
                resp_json = r.json()
                return {
                    "success": resp_json.get("code") == 1,
                    "data": resp_json.get("data"),
                    "error": resp_json.get("error", None)
                }
            except Exception as e:
                print("DEBUG: API request failed:", e)
                return {
                    "success": False,
                    "error": f"API request failed: {str(e)}"
                }

    async def scan_receipt_image(self, image_bytes: bytes) -> dict:
        """
        Полный цикл сканирования: изображение -> QR -> данные чека.

        Args:
            image_bytes: Байты изображения

        Returns:
            Словарь с результатом сканирования:
            {
                "success": bool,
                "qr_raw": str,
                "fns": dict,
                "items": list,
                "api_response": dict,
                "message": str (опционально при ошибке)
            }
        """
        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            return {
                "success": False,
                "message": f"Не удалось открыть изображение: {str(e)}"
            }

        # Декодируем QR-код
        qr_raw = self.decode_qr_from_image(image)

        if not qr_raw:
            return {
                "success": False,
                "message": "QR-код не найден на изображении. Попробуйте сфотографировать чек при лучшем освещении."
            }

        # Извлекаем параметры ФНС
        fns_data = self.extract_fns_from_text(qr_raw)

        if len(fns_data) < 4:
            return {
                "success": False,
                "message": "Найден QR-код, но не удалось извлечь параметры чека ФНС",
                "qr_raw": qr_raw,
                "fns": fns_data
            }

        # Получаем данные от API
        api_response = await self.fetch_receipt_from_api(qr_raw)

        # Извлекаем товары из ответа
        items = []
        if api_response.get("success"):
            items = (
                api_response
                .get("data", {})
                .get("json", {})
                .get("items", [])
            )

        return {
            "success": True,
            "qr_raw": qr_raw,
            "fns": fns_data,
            "items": items,
            "api_response": api_response
        }
