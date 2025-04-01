from fastapi import FastAPI, Request
import logging
import os
import openai
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
wazzup_api_key = os.getenv("WAZZUP_API_KEY")

app = FastAPI()

logging.basicConfig(level=logging.INFO)

@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"📩 Получен JSON: {data}")

        text = data.get("text")
        chat_id = data.get("chat_id")
        name = data.get("name", "Гость")
        channel = data.get("channel", "unknown")

        if not all([text, chat_id, name, channel]):
            logging.warning("⚠️ Недостаточно данных")
            return {"status": "error", "message": "Недостаточно данных"}

        logging.info(f"🔍 Обработка сообщения от {name} ({channel}) - {text}")

        # Генерация ответа от GPT
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты вежливый менеджер полиграфической компании и помогаешь клиентам с расчётом стоимости продукции."},
                {"role": "user", "content": text}
            ]
        )
        reply = response.choices[0].message.content.strip()
        logging.info(f"🤖 Ответ: {reply}")

        # Отправка ответа через Wazzup API
        send_status = send_reply_to_client(chat_id, reply)
        return {"status": "ok", "reply": reply, "wazzup_status": send_status}

    except Exception as e:
        logging.error(f"🔥 Ошибка при обработке запроса: {e}")
        return {"status": "error", "message": str(e)}


def send_reply_to_client(chat_id: str, message: str) -> str:
    try:
        url = "https://api.wazzup24.com/v3/message"
        headers = {
            "Authorization": f"Bearer {wazzup_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "chatId": chat_id,
            "text": message
        }

        res = requests.post(url, json=payload, headers=headers)
        logging.info(f"📤 Отправка в Wazzup: {res.status_code} | {res.text}")

        if res.status_code == 200:
            return "sent"
        else:
            return f"failed: {res.status_code}"

    except Exception as e:
        logging.error(f"🚫 Ошибка при отправке в Wazzup: {e}")
        return f"error: {e}"
