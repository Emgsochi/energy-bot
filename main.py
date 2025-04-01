from fastapi import FastAPI, Request
import os
import requests
import logging
from openai import OpenAI
from pydantic import BaseModel

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenAI client (использует переменную окружения OPENAI_API_KEY)
client = OpenAI()

# Инициализация FastAPI
app = FastAPI()

# Ключ для отправки через Wazzup
WAZZUP_API_KEY = os.getenv("WAZZUP_API_KEY")

# Модель запроса (на случай, если ты решишь использовать строгую валидацию)
class IncomingMessage(BaseModel):
    chat_id: str
    text: str
    name: str = "Гость"
    channel: str = "telegram"


@app.post("/wazzup/webhook")
async def handle_message(request: Request):
    try:
        data = await request.json()

        chat_id = data.get("chat_id")
        text = data.get("text")
        name = data.get("name", "Гость")
        channel = data.get("channel", "telegram")

        if not all([chat_id, text]):
            logger.warning("Missing data in request.")
            return {"status": "missing_data"}

        logger.info(f"Входящее сообщение от {name}: {text}")

        # Обращение к OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты вежливый и профессиональный менеджер по продажам. Отвечай кратко, но понятно."},
                {"role": "user", "content": text}
            ]
        )

        reply_text = response.choices[0].message.content.strip()
        logger.info(f"Ответ GPT: {reply_text}")

        # Отправка ответа клиенту через Wazzup
        send_url = "https://api.wazzup24.com/v3/message"
        headers = {
            "Authorization": f"Bearer {WAZZUP_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "channelId": chat_id,
            "text": reply_text,
            "type": "text"
        }

        send_response = requests.post(send_url, json=payload, headers=headers)
        logger.info(f"Ответ Wazzup API: {send_response.status_code} - {send_response.text}")

        return {"status": "ok", "gpt_reply": reply_text}

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {str(e)}")
        return {"status": "error", "message": str(e)}
