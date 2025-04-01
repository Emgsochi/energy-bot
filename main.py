from fastapi import FastAPI, Request
from pydantic import BaseModel
import logging
import json

app = FastAPI()
logging.basicConfig(level=logging.INFO)

class WazzupMessage(BaseModel):
    text: str
    chat_id: str
    name: str
    channel: str

@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    # Логируем заголовки
    headers = dict(request.headers)
    logging.info(f"📬 Headers: {headers}")

    # Получаем и логируем RAW тело
    raw_body = await request.body()
    body_str = raw_body.decode("utf-8")
    logging.info(f"📥 RAW BODY: {body_str}")

    try:
        data = json.loads(body_str)
        logging.info(f"📩 PARSED JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")

        # Проверяем наличие необходимых полей
        required_fields = ["text", "chat_id", "name", "channel"]
        if not all(field in data for field in required_fields):
            logging.warning("⚠️ Недостаточно данных: text, chat_id, name, channel")
            return {"message": "Недостаточно данных"}

        message = WazzupMessage(**data)

        # Здесь логика обработки сообщения
        logging.info(f"✅ Получено сообщение от {message.name} в {message.channel}: {message.text}")

        return {"message": f"Принято сообщение: {message.text}"}

    except json.JSONDecodeError:
        logging.error("❌ Ошибка декодирования JSON")
        return {"message": "Некорректный JSON"}

    except Exception as e:
        logging.error(f"❌ Общая ошибка: {str(e)}")
        return {"message": "Внутренняя ошибка сервера"}
