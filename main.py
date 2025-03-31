import os
import re
import json
import requests
import openai
import asyncio

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from google.oauth2 import service_account
import gspread

# Инициализация FastAPI приложения
app = FastAPI()

# Настройка API ключей и учетных данных из переменных окружения
WAZZUP_API_KEY = os.getenv("WAZZUP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_SHEETS_CREDENTIALS") or os.getenv("GOOGLE_CREDENTIALS_JSON") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# Проверка наличия необходимых ключей
if not WAZZUP_API_KEY:
    raise RuntimeError("WAZZUP_API_KEY not set in environment")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")
if not GOOGLE_SHEET_ID:
    raise RuntimeError("GOOGLE_SHEET_ID not set in environment")
if not GOOGLE_CREDENTIALS_JSON:
    raise RuntimeError("Google service account credentials JSON not set in environment")

# Установка API ключа OpenAI
openai.api_key = OPENAI_API_KEY

# Настройка учетных данных для Google Sheets API с использованием переменной окружения
try:
    credentials_info = json.loads(GOOGLE_CREDENTIALS_JSON)
except json.JSONDecodeError:
    # Если переменная окружения содержит путь к JSON файлу (как fallback, не рекомендуется)
    if os.path.exists(GOOGLE_CREDENTIALS_JSON):
        with open(GOOGLE_CREDENTIALS_JSON, 'r') as f:
            credentials_info = json.load(f)
    else:
        raise RuntimeError("Failed to parse Google credentials JSON from environment")
credentials = service_account.Credentials.from_service_account_info(
    credentials_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)

# Создание клиента для Google Sheets (gspread)
try:
    gs_client = gspread.authorize(credentials)
    spreadsheet = gs_client.open_by_key(GOOGLE_SHEET_ID)
except Exception as e:
    raise RuntimeError(f"Failed to authorize or open Google Sheet: {e}")

# Функция для поиска цены в прайсе Google Sheets
def find_price_in_sheet(user_text: str):
    """
    Парсит текст запроса пользователя и ищет соответствующую цену в Google Sheets.
    Возвращает найденную цену (число или строку) или None, если не найдена.
    """
    text = user_text.lower()

    # 1. Определяем количество (quantity) и размер (если указан) из текста
    quantity = None
    size = None
    # Ищем шаблон размера вида AxB или AxB (с русской 'x' тоже)
    size_match = re.search(r'(\d+)\s*[xх×]\s*(\d+)', text)
    if size_match:
        # Форматируем размер как "N x M"
        size = f"{size_match.group(1)}x{size_match.group(2)}"
    # Ищем первое число, которое может быть количеством (игнорируем числа из размера)
    # Найдем все числовые подстроки
    numbers = re.findall(r'\d+', text)
    if numbers:
        # Удаляем из списка чисел те, которые относятся к размеру
        if size_match:
            # remove the two numbers that formed the size
            num1 = size_match.group(1)
            num2 = size_match.group(2)
            numbers = [n for n in numbers if n != num1 and n != num2]
        if numbers:
            # Берем первое оставшееся число как количество
            quantity = int(numbers[0])

    # 2. Определяем тип продукта (по ключевым словам)
    product_keywords = []
    if "визит" in text:
        product_keywords.append("визит")
    if "листов" in text or "листовок" in text or "flyer" in text:
        product_keywords.append("листов")
    if "баннер" in text or "banner" in text:
        product_keywords.append("баннер")
    if "наклей" in text or "стикер" in text:
        product_keywords.append("наклей")
    if "буклет" in text:
        product_keywords.append("буклет")
    if "брошюр" in text:
        product_keywords.append("брошюр")
    # Можно добавить другие категории при необходимости

    # 3. Определяем двусторонность/односторонность
    double_side = False
    single_side = False
    if "двухсторон" in text or "двусторон" in text or "2 сторон" in text or "двух сторон" in text:
        double_side = True
    elif "односторон" in text or "1 сторон" in text:
        single_side = True

    # Если явно не указано, предполагаем одностороннюю по умолчанию?
    # Но лучше оставить single_side=False, double_side=False как неизвестно.

    # 4. Получаем все значения из таблицы (прайса)
    try:
        # Предполагаем, что прайс находится на первом листе (можно настроить имя листа при необходимости)
        sheet = spreadsheet.sheet1
        data = sheet.get_all_values()
    except Exception as e:
        print(f"Ошибка при получении данных из Google Sheets: {e}")
        return None

    if not data:
        return None

    # Найденная цена
    found_price = None

    # 5. Ищем соответствие в данных прайса
    # Попробуем разные стратегии поиска:
    # (a) Если прайс в виде таблицы: первая колонка - описание товара, первая строка - количества (или наоборот).
    # (b) Если прайс разделен по категориям, находим строку и колонку пересечения.

    # Приводим все к нижнему регистру для поиска
    data_lower = [[str(cell).lower() if cell is not None else "" for cell in row] for row in data]

    # Если известно количество
    quantity_str = str(quantity) if quantity is not None else None

    # 5a. Если вариант: первая колонка - описание товара (с указанием размера и сторон), заголовки колонок - количества.
    if quantity_str:
        # Ищем заголовок колонки, равный количеству
        header_row_index = None
        quantity_col_index = None
        for j, val in enumerate(data_lower[0]):
            # Первую строку считаем заголовком
            if val == quantity_str or val == quantity_str + "шт" or val == quantity_str + " шт":
                quantity_col_index = j
                header_row_index = 0
                break
        if quantity_col_index is None and len(data_lower) > 1:
            # Если не нашли в первой строке, попробуем искать в первой колонке (т.е. другой ориентации)
            for i, val in enumerate(row[0] for row in data_lower):
                if val == quantity_str or val == quantity_str + "шт" or val == quantity_str + " шт":
                    header_row_index = None  # quantity is in first col, so header row might not be needed
                    quantity_col_index = 0
                    quantity_row_index = i
                    # If quantity is first column, we have quantity_row_index as i
                    # Now need to find correct column by product description
                    break
        if quantity_col_index is not None:
            # Если количество найдено в заголовках колонок
            if quantity_col_index == 0:
                # Это случай, когда количество находится в первой колонке (ориентация наоборот)
                # Уже определили quantity_row_index
                pass
            else:
                # Ищем строку, которая соответствует описанию товара
                for i, row in enumerate(data_lower):
                    if i == header_row_index:
                        continue  # пропускаем строку заголовков
                    row_text = " ".join(row)
                    if size and size in row_text:
                        # Условие: строка содержит указанный размер
                        if double_side and ("двух" in row_text or "двухсторон" in row_text or "2 сторон" in row_text or "4+4" in row_text):
                            found_price = row[quantity_col_index]
                            break
                        elif single_side and ("одно" in row_text or "односторон" in row_text or "1 сторон" in row_text or "4+0" in row_text):
                            found_price = row[quantity_col_index]
                            break
                        elif not double_side and not single_side:
                            # Если не указана сторона, берем первую подходящую (может быть одностороннюю по умолчанию)
                            found_price = row[quantity_col_index]
                            break
                    elif size is None:
                        # Если размер не указан, ищем по ключевым словам продукта
                        match = True
                        for kw in product_keywords:
                            if kw and kw not in row_text:
                                match = False
                                break
                        if not match:
                            continue
                        # Также фильтруем по стороне если указано
                        if double_side and not ("двух" in row_text or "двусторон" in row_text or "4+4" in row_text):
                            continue
                        if single_side and not ("одно" in row_text or "односторон" in row_text or "4+0" in row_text):
                            continue
                        if match:
                            found_price = row[quantity_col_index]
                            break
                    # Если нашли цену, выходим из цикла строк
                if found_price is not None:
                    # Завершаем поиск, если нашли
                    pass

    # 5b. Если вариант: первая колонка - количество, первая строка - названия товаров (варианты)
    if found_price is None and quantity_str:
        # Найдем колонку с подходящим описанием товара, строку с количеством
        # Поиск колонки: проверяем первую строку и вторую строку на наличие ключевых слов товара
        target_col_index = None
        header_rows_to_check = 2 if len(data_lower) > 1 else 1
        for j in range(1, len(data_lower[0]) if data_lower else 0):
            header_cell_text = " ".join([data_lower[r][j] for r in range(header_rows_to_check) if j < len(data_lower[r])])
            # Проверяем наличие ключевых слов товара и размера в заголовках столбцов (может быть объединено на 1-2 строках)
            if size and size in header_cell_text:
                if double_side and re.search(r"двух|двусторон|4\+4|2 ?стор", header_cell_text):
                    target_col_index = j
                    break
                elif single_side and re.search(r"одно|односторон|4\+0|1 ?стор", header_cell_text):
                    target_col_index = j
                    break
                elif not double_side and not single_side:
                    # если сторона не указана, достаточно совпадения размера
                    target_col_index = j
                    break
            elif size is None:
                # если размер не указан, но, например, категория в заголовке
                match = True
                for kw in product_keywords:
                    if kw and kw not in header_cell_text:
                        match = False
                        break
                if not match:
                    continue
                # фильтр по стороне
                if double_side and not re.search(r"двух|двусторон|4\+4|2 ?стор", header_cell_text):
                    continue
                if single_side and not re.search(r"одно|односторон|4\+0|1 ?стor", header_cell_text):
                    continue
                target_col_index = j
                break

        if target_col_index is not None:
            # Ищем строку (в первой колонке) с нашим количеством
            quantity_row_index = None
            for i, row in enumerate(data_lower):
                if row and row[0] == quantity_str or row and row[0] == quantity_str + "шт" or row and row[0] == quantity_str + " шт":
                    quantity_row_index = i
                    break
            if quantity_row_index is not None:
                # Получаем цену как пересечение найденной строки и столбца
                if quantity_row_index < len(data) and target_col_index < len(data[quantity_row_index]):
                    found_price = data[quantity_row_index][target_col_index]

    # Если цена найдена, возвращаем ее
    if found_price:
        # Убираем возможные пробелы и переводим в число, если возможно
        price_str = str(found_price).strip()
        # Если строка содержит только цифры (и, возможно, запятую/точку)
        if re.match(r'^\d+([.,]\d+)?$', price_str):
            # Заменяем запятую на точку и конвертируем в число
            price_num = float(price_str.replace(',', '.'))
            # Если целое число (например 1500.0), приводим к int
            if abs(price_num - int(price_num)) < 1e-9:
                price_num = int(price_num)
            return price_num
        else:
            # Если цена указана с текстом (например "1 500" с пробелом или "—"), вернем как есть строкой
            return price_str
    return None

# Функция для генерации ответа GPT-4 на основе запроса пользователя и найденной цены
def generate_response(user_message: str, price: str or int or float):
    """
    Вызывает OpenAI GPT-4 API для генерации дружелюбного ответа, включая указанную цену.
    """
    # Формируем системное сообщение с инструкциями и информацией о цене
    system_content = (
        "You are a friendly customer support assistant at a printing company. "
        "The conversation is in Russian. "
        "The user will provide a printing request, and you have the price from the price list. "
    )
    if price is not None:
        # Встраиваем информацию о цене в системное сообщение
        # Округляем/форматируем цену в строку с валютой
        if isinstance(price, (int, float)):
            price_value = int(price) if isinstance(price, float) and price.is_integer() else price
            price_text = f"{price_value} рублей"
        else:
            # Если цена уже строка (возможно с форматированием), добавляем валюту, если не указано
            price_text = price
            if not any(curr in price_text for curr in ["руб", "р.", "₽"]):
                price_text += " рублей"
        system_content += f"Provide the price {price_text} in your answer and address the user's request helpfully and in a human-like manner."
    else:
        # Если цена не найдена, просим извиниться и уточнить
        system_content += "Unfortunately, you could not find the price for the request. Apologize to the customer and ask for clarification if needed."
    # Собираем сообщения для чата
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message}
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.5
        )
        answer = response['choices'][0]['message']['content'].strip()
        return answer
    except Exception as e:
        print(f"Ошибка при обращении к OpenAI API: {e}")
        # В случае ошибки API возвращаем шаблонный ответ
        if price is not None:
            return f"Здравствуйте! По вашему запросу ориентировочная стоимость составляет {price} рублей. Если у вас возникли дополнительные вопросы, я буду рад ответить."
        else:
            return "Извините, я сейчас не могу уточнить цену. Пожалуйста, уточните детали вашего запроса, и я помогу вам с расчетом."

# Фоновая задача для обработки входящего сообщения
def handle_incoming_message(message: dict):
    """
    Обрабатывает входящее сообщение: определяет ответ с ценой и отсылает его через Wazzup API.
    """
    text = message.get("text", "")
    if not text:
        return  # Если нет текста сообщения, нечего обрабатывать

    # Проверяем, не является ли сообщение эхом/нашим собственным, чтобы избежать бесконечных циклов
    # Вебхук Wazzup передает isEcho = False для входящих от клиента. Если есть isEcho = True, игнорируем.
    if message.get("isEcho") is True:
        return

    # Получаем цену из прайса
    price = None
    try:
        price = find_price_in_sheet(text)
    except Exception as e:
        print(f"Ошибка при поиске цены: {e}")

    # Генерируем ответ с помощью GPT-4
    reply_text = generate_response(text, price)

    # Формируем и отправляем ответное сообщение через Wazzup API
    reply_payload = {
        "channelId": message.get("channelId"),
        "chatType": message.get("chatType"),
        "chatId": message.get("chatId"),
        "text": reply_text
    }
    # Добавляем crmMessageId для идемпотентности (уникальный), например на основе messageId
    if message.get("messageId"):
        reply_payload["crmMessageId"] = f"reply_{message['messageId']}"
    try:
        res = requests.post(
            "https://api.wazzup24.com/v3/message",
            json=reply_payload,
            headers={"Authorization": f"Bearer {WAZZUP_API_KEY}", "Content-Type": "application/json"}
        )
        if res.status_code >= 400:
            print(f"Ошибка отправки сообщения через Wazzup API: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"Ошибка при вызове Wazzup API: {e}")

# Эндпоинт для вебхуков от Wazzup
@app.post("/webhook")
async def wazzup_webhook(request_data: dict, background_tasks: BackgroundTasks):
    """
    Эндпоинт, принимающий вебхуки от Wazzup (новые сообщения и статусы).
    Обрабатывает новые входящие сообщения от клиентов в фоновом задании.
    """
    # Wazzup может отправить тестовый запрос { "test": true } при подключении вебхука
    if request_data.get("test"):
        return JSONResponse(content={"ok": True}, status_code=200)

    # Извлекаем новые сообщения, если они есть
    messages = request_data.get("messages")
    if messages:
        # Обрабатываем все новые входящие сообщения
        for msg in messages:
            # Проверяем статус сообщения: 'inbound' означает входящее сообщение от клиента
            status = msg.get("status")
            # Если есть статус и он не 'inbound', пропускаем обработку (например, статусы доставки)
            if status and status != "inbound":
                continue
            # Добавляем фонового таска для обработки (чтобы сразу ответить 200 OK на вебхук)
            background_tasks.add_task(handle_incoming_message, msg)

    # Всегда возвращаем 200 OK, чтобы Wazzup не повторял вебхук
    return JSONResponse(content={"ok": True}, status_code=200)

# Запуск приложения (для локального запуска; Render автоматически запускает с uvicorn/gunicorn)
if __name__ == "__main__":
    import uvicorn
    # На Render используется порт из переменной окружения PORT, иначе 8000 по умолчанию
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
