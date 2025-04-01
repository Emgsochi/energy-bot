from fastapi import FastAPI, Request
import logging
import os
import openai
import gspread
import requests
import json
from oauth2client.service_account import ServiceAccountCredentials

# 🔧 Настройка логов
logging.basicConfig(level=logging.INFO)

# ✅ Получаем переменные из Render
openai.api_key = os.getenv("OPENAI_API_KEY")
wazzup_token = os.getenv("WAZZUP_API_KEY")
sheet_id = os.getenv("GOOGLE_SHEET_ID")

# 📌 JSON-ключ как строка
google_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")

# 🧠 Авторизация Google Sheets напрямую из строки
creds_dict = json.loads(google_json_str)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(sheet_id).sheet1


# 🔍 Поиск товара
def find_product_info(text: str) -> str:
    rows = sheet.get_all_records()
    for row in rows:
        name = row.get("Название", "").lower()
        qty = str(row.get("Кол-во", "")).lower()
        format_ = row.get("Формат", "").lower()
        if all(k in text.lower() for k in [name, qty, format_]):
            return f"{row['Название']} {row['Кол-во']} {row['Формат']} — {row['Цена']}₽"
    return "Не удалось найти позицию, уточните, пожалуйста."


# 📬 Отправка ответа через Wazzup API
def send_reply(chat_id: str, message: str) -> str:
    url = "https://api.wazzup24.com/v3/message"
    headers = {
        "Authorization": f"Bearer {wazzup_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "chatId": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload, headers=headers)
    logging.info(f"📤 Отправка в Wazzup: {response.status_code} | {response.text}")
    return "sent" if response.status_code == 200 else f"error: {response.status_code}"


# 🚀 FastAPI
app = FastAPI()


@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"📩 Получено: {data}")

        text = data.get("text")
        chat_id = data.get("chat_id")
        name = data.get("name", "Гость")

        if not all([text, chat_id]):
            logging.warning("⚠️ Недостаточно данных")
            return {"status": "missing_data"}

        # Поиск и генерация ответа
        match = find_product_info(text)
        prompt = f"Клиент спрашивает: {text}\nНайдено в прайсе: {match}\nОтветь понятно и дружелюбно."

        reply = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты менеджер рекламного агентства, отвечай понятно, коротко и дружелюбно."},
                {"role": "user", "content": prompt}
            ]
        ).choices[0].message.content.strip()

        logging.info(f"🤖 GPT ответ: {reply}")
        status = send_reply(chat_id, reply)

        return {"status": "ok", "sent": status, "reply": reply}

    except Exception as e:
        logging.error(f"🔥 Ошибка: {e}")
        return {"status": "error", "detail": str(e)}
