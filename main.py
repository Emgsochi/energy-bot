from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Optional
import os
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)

class MessagePayload(BaseModel):
    chatId: str = Field(..., alias="chatId")
    channelId: str = Field(..., alias="channelId")
    chatType: str = Field(..., alias="chatType")
    text: str = Field(..., alias="text")
    name: Optional[str] = Field(None, alias="name")

@app.post("/wazzup/webhook")
async def wazzup_webhook(payload: MessagePayload):
    logging.info(f"Получен запрос: {payload}")
    
    # Пример простой логики ответа (в будущем можно вызвать GPT, Excel и т.д.)
    reply = f"Принято сообщение от {payload.name or 'Клиент'}: {payload.text}"

    return {"status": "ok", "message": reply}

@app.get("/")
async def root():
    return {"message": "Energy bot is live"}
