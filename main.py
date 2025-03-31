from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAI
import os
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Инициализация FastAPI
app = FastAPI()

# Инициализация OpenAI клиента
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Авторизация в Google Sheets
CREDENTIALS_FILE = 'H:/RoboJulia/credentials.json'
SPREADSHEET_NAME = 'EnergyBD'
SHEET_NAME = 'прайс'

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
sheet_client = gspread.authorize(creds)
sheet = sheet_client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
data = sheet.get_all_values()


# Синонимы
SYNONYMS = {
    "двусторонние": "4+4",
    "двусторонняя": "4+4",
    "двухсторонние": "4+4",
    "односторонние": "4+0",
    "односторонняя": "4+0",
    "визитки": "визитки",
    "визитка": "визитки",
    "90х50": "90x50",
    "90x50": "90x50"
}


def extract_parameters(query: str) -> dict:
    query = query.lower()
    for word, replacement in SYNONYMS.items():
        query = query.replace(word, replacement)

    # Кол-во
    quantity_match = re.search(r"\d+", query)
    quantity = int(quantity_match.group()) if quantity_match else None

    # Размер
    size_match = re.search(r"\d{2,4}[xх*]\d{2,4}", query)
    size = size_match.group().replace("х", "x").replace("*", "x") if size_match else None

    # Формат
    format_match = re.search(r"\d\+\d|\d{1,2}\+\d{1,2}", query)
    format_value = format_match.group() if format_match else None

    # Продукт
    product = "визитки" if "визитки" in query else None

    return {
        "product": product,
        "format": format_value,
        "size": size,
        "quantity": quantity
    }


def find_price_row(params):
    for row in data[1:]:  # пропускаем заголовок
        if (
            params["product"] and params["product"] in row[0].lower()
            and params["format"] and params["format"] in row[1]
            and params["size"] and params["size"] in row[2]
            and params["quantity"] and str(params["quantity"]) in row[3]
        ):
            return row
    return None


@app.post("/wazzup/webhook")
async def receive_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    elif isinstance(data, dict):
        pass
    else:
        raise HTTPException(status_code=400, detail="Payload must be JSON object or array")

    text = data.get("text", "")
    contact_name = data.get("contact_name", "")
    print(f"📩 Получено сообщение от {contact_name}: {text}")

    # Извлекаем параметры
    params = extract_parameters(text)
    print(f"🧠 Извлечённые параметры: {params}")

    # Пытаемся найти цену
    price_row = find_price_row(params)
    if price_row:
        response_text = (
            f"Стоимость {params['quantity']} визиток {params['size']} {params['format']} — {price_row[4]} ₽"
        )
    else:
        response_text = (
            "К сожалению, не удалось найти цену по вашему запросу. Уточните, пожалуйста, параметры (формат, размер, количество)."
        )

    # Запрос к ChatGPT для более человеческого ответа
    gpt_response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ты — дружелюбный менеджер рекламного агентства."},
            {"role": "user", "content": f"Запрос клиента: {text}. Ответ от базы: {response_text}"}
        ],
        temperature=0.7
    )

    final_reply = gpt_response.choices[0].message.content
    print("🤖 Ответ GPT:", final_reply)

    return JSONResponse(content={"status": "ok", "reply": final_reply})
