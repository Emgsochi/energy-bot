from fastapi import FastAPI, Request
import os
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

app = FastAPI()

# Загружаем ключи из переменных окружения
WAZZUP_API_KEY = os.getenv("WAZZUP_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

openai.api_key = OPENAI_API_KEY

# Авторизация Google Sheets
def get_worksheet():
    import json
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID)
    return sheet.sheet1

# Поиск строки с нужным товаром
def find_price_in_sheet(text):
    worksheet = get_worksheet()
    rows = worksheet.get_all_records()
    for row in rows:
        name = str(row.get("Название", "")).lower()
        quantity = str(row.get("Тираж", "")).lower()
        format_ = str(row.get("Формат", "")).lower()

        if "визиток" in text and "двухсторонн" in text:
            if "90x50" in text and "300" in text:
                if "4+4" in format_ and "300" in quantity:
                    return f"{row['Цена']} ₽ — {row['Название']} {row['Формат']} {row['Тираж']} шт"
    return "Не удалось найти цену в прайсе 😔"

# Отправка ответа через Wazzup
def send_wazzup_reply(channel_id, contact_id, message):
    url = "https://api.wazzup24.com/v3/message"
    headers = {
        "Authorization": f"Bearer {WAZZUP_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "channelId": channel_id,
        "chatId": contact_id,
        "text": message
    }
    response = requests.post(url, json=data, headers=headers)
    return response.status_code, response.text

# Главная логика обработки webhook
@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    data = await request.json()

    try:
        message_text = data.get("text", "")
        channel_id = data.get("channelId")
        contact_id = data.get("chatId")

        # Поиск в прайсе
        price = find_price_in_sheet(message_text)

        # Запрос к ChatGPT
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты менеджер рекламного агентства, дружелюбный и точный."},
                {"role": "user", "content": f"Клиент спрашивает: {message_text}\nНайденная цена: {price}"}
            ]
        )
        answer = response.choices[0].message.content.strip()

        # Отправка ответа
        status, reply = send_wazzup_reply(channel_id, contact_id, answer)
        return {"status": status, "reply": reply}

    except Exception as e:
        return {"error": str(e)}
