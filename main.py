from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import logging
import os

app = FastAPI()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Модель запроса от Wazzup
class WazzupWebhookPayload(BaseModel):
    chatId: str
    channelId: str
    chatType: str
    text: str

@app.get("/")
def root():
    return {"message": "OK"}

@app.post("/wazzup/webhook")
async def wazzup_webhook(payload: WazzupWebhookPayload):
    logger.info(f"📩 Получено сообщение от Wazzup:\n{payload}")

    # Простейшая заглушка-ответ
    response_text = f"Вы написали: {payload.text}"

    # Здесь можно добавить логику отправки ответа клиенту через Wazzup API

    return {"status": "ok", "echo": response_text}
