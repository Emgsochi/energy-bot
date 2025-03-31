import os
from fastapi import FastAPI, Request
from openai import OpenAI
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from extract_parameters import extract_parameters
from wazzup_webhook import send_message

app = FastAPI()

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Настройка OpenAI (новый синтаксис)
client = OpenAI(api_key=OPENAI_API_KEY)

# Подключение к Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE = "credentials.json"  # ⚠️ Убедись, что этот файл есть в репозитории

creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client_gsheets = gspread.authorize(creds)
sheet = client_gsheets.open("bot_energy").sheet1


@app.post("/wazzup/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    try:
        # Извлечение сообщения
        message_text = data.get("message", {}).get("text", "")
        chat_id = data.get("chat", {}).get("id")

        print(f"📩 Получено сообщение от {chat_id}: {message_text}")

        # Параметры из текста
        params = extract_parameters(message_text)
        print("🧠 Извлечённые параметры:", params)

        # Генерация ответа от ChatGPT
        prompt = f"""Ты — вежливый менеджер рекламного агентства ENERGY в Сочи. 
Клиент спрашивает: "{message_text}"

Используй дружелюбный стиль и краткий ответ. Если знаешь цену, скажи её. 
Если не можешь — задай уточняющий вопрос.

Извлечённые параметры: {params}"""

        gpt_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Ты менеджер ENERGY"},
                      {"role": "user", "content": prompt}],
            temperature=0.7
        )

        final_text = gpt_response.choices[0].message.content.strip()
        print("🤖 Ответ GPT:", final_text)

        # Отправка ответа обратно клиенту
        send_message(chat_id=chat_id, text=final_text, bot_token=BOT_TOKEN)

        return {"status": "ok"}

    except Exception as e:
        print("❌ Ошибка:", e)
        return {"status": "error", "details": str(e)}
