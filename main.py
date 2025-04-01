import os
import json
import logging
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Инициализация OpenAI клиента
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Переменные окружения
WAZZUP_API_KEY = os.getenv("WAZZUP_API_KEY")
WAZZUP_SEND_URL = "https://api.wazzup24.com/v3/message"  # эндпоинт отправки сообщения


# Функция отправки ответа клиенту через Wazzup
def send_wazzup_message(chat_id: str, text: str):
    headers = {
        "Authorization": f"Bearer {WAZZUP_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "chatId": chat_id,
        "text": text,
        "type": "text"
    }
    response = requests.post(WAZZUP_SEND_URL, headers=headers, json=data)
    logging.info(f"📤 Ответ отправлен через Wazzup: {response.status_code} {response.text}")
    return response


# Обработка вебхука от Albato
@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    body = await request.json()
    logging.info(f"📥 RAW BODY: {body}")

    # Проверка и извлечение данных
    chat_id = body.get("chat_id")
    text = body.get("text")
    name = body.get("name", "Гость")
    channel = body.get("channel")

    if not all([chat_id, text, name, channel]):
        logging.warning("⚠️ Недостаточно данных: text, chat_id, name, channel")
        return {"status": "missing_data"}

    # GPT: генерация ответа
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Ты оператор печати. Отвечай вежливо, ясно, кратко, как человек."},
            {"role": "user", "content": text}
        ]
    )
    gpt_reply = response.choices[0].message.content
    logging.info(f"🤖 GPT ответ: {gpt_reply}")

    # Отправка ответа в Wazzup
    send_wazzup_message(chat_id, gpt_reply)

    return {"status": "ok"}
