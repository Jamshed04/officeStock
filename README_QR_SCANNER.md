# QR Scanner для чеков - Инструкция по установке и использованию

## Установка зависимостей

### 1. Установка библиотек Python

Выполните команду для установки зависимостей через Poetry:

```bash
poetry install
```

Это установит следующие библиотеки:

- **Pillow** - обработка изображений
- **pyzbar** - декодирование QR-кодов
- **httpx** - асинхронные HTTP-запросы к API

### 2. Установка системных зависимостей для pyzbar

`pyzbar` требует установки библиотеки ZBar на системном уровне.

#### Windows:

1. Скачайте и установите vcpkg:
   ````bash
   git clone https://github.com/Microsoft/vcpkg.git
   cd vcpkg
   bootstrap-vcpkg.bat
   ```1
   1
   ````
2. Установите ZBar:
   ```bash
   vcpkg install zbar:x64-windows
   ```

**Альтернативный способ для Windows:**

- Скачайте готовые DLL файлы ZBar с [GitHub](https://github.com/NaturalHistoryMuseum/pyzbar#installation)
- Поместите файлы в папку `C:\Windows\System32` или в папку с проектом

#### Linux (Ubuntu/Debian):

```bash
sudo apt-get install libzbar0
```

#### macOS:

```bash
brew install zbar
```

## Использование

### API Endpoint

**POST** `/api/v1/receipts/parse-qr`

Загружает изображение чека и возвращает распознанные данные.

### Пример запроса (curl)

```bash
curl -X POST "http://localhost:8001/api/v1/receipts/parse-qr" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/receipt_photo.jpg"
```

### Пример запроса (Python)

```python
import httpx

async with httpx.AsyncClient() as client:
    with open("receipt_photo.jpg", "rb") as f:
        files = {"file": f}
        response = await client.post(
            "http://localhost:8001/api/v1/receipts/parse-qr",
            files=files
        )
        data = response.json()
        print(data)
```

### Пример ответа

```json
{
  "success": true,
  "data": {
    "fiscal_number": "7381440800700882",
    "fiscal_document": "10642",
    "fiscal_sign": "1776221652",
    "date_buy": "2025-09-24 21:20",
    "sum": 52.0,
    "name_supplier": "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"СОВЕТСКАЯ АПТЕКА\"",
    "items": [
      {
        "name": "ЙОДИНОЛ р-р 100мл Самарамедпром",
        "price": 52.0,
        "quantity": 1.0,
        "sum": 52.0
      }
    ]
  }
}
```

### Пример ответа с ошибкой

```json
{
  "success": false,
  "error": "QR-код не найден на изображении. Попробуйте сфотографировать чек при лучшем освещении."
}
```

## Особенности реализации

### Улучшенное распознавание QR-кодов

Сканер применяет несколько стратегий обработки изображения:

1. **Исходное изображение** - прямое сканирование
2. **Увеличение контраста** - для слабого освещения
3. **Чёрно-белое преобразование** - для улучшения читаемости
4. **Повышение резкости** - для размытых фото
5. **Увеличение масштаба** - для маленьких QR-кодов
6. **Комбинированная обработка** - все методы вместе
7. **Адаптивная бинаризация** - с разными порогами

Это позволяет распознавать QR-коды даже при:

- Плохом освещении
- Наклоне камеры
- Низком разрешении фото
- QR-код занимает малую часть изображения

### Конфигурация

API токен и URL настраиваются в файле конфигурации:

```python
# app/core/config.py
class ReceiptApiConfig(BaseModel):
    token: str = "ВАШ_ТОКЕН"  # Замените на свой токен
    url: str = "https://proverkacheka.com/api/v1/check/get"
```

Либо через переменные окружения в `.env`:

```env
APP_CONFIG__RECEIPT_API__TOKEN=ваш_токен
APP_CONFIG__RECEIPT_API__URL=https://proverkacheka.com/api/v1/check/get
```

## Тестирование

Для тестирования откройте Swagger UI:

```
http://localhost:8001/docs
```

Найдите endpoint `/api/v1/receipts/parse-qr` и загрузите фото чека.

## Рекомендации для фотографирования чеков

1. Хорошее освещение
2. QR-код должен быть в кадре (не обязательно только QR-код, весь чек тоже можно)
3. Избегайте бликов на чеке
4. Держите камеру параллельно чеку
5. Фокус на QR-коде

## Troubleshooting

### pyzbar не находит QR-код

- Проверьте, установлена ли системная библиотека ZBar
- Попробуйте улучшить качество фотографии
- Убедитесь, что QR-код читаемый (не поврежден, не смазан)

### Ошибка импорта pyzbar

- Убедитесь, что установлены системные зависимости ZBar
- Перезапустите IDE/терминал после установки ZBar

### API возвращает ошибку

- Проверьте API токен в конфигурации
- Убедитесь, что сервис proverkacheka.com доступен
- Проверьте, что QR-код содержит валидные данные чека ФНС
