from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import os
from openai import OpenAI
import httpx

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация FastAPI и OpenAI-клиента
app = FastAPI()
client = OpenAI()  # SDK сам подтянет OPENAI_API_KEY из окружения

@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    try:
        # Получаем JSON из запроса
        data = await request.json()
        logger.info(f"📩 Получен запрос: {data}")

        # Извлекаем текст сообщения
        message_text = data.get("text", "").strip()

        if not message_text:
            return JSONResponse({"error": "Сообщение пустое"}, status_code=400)

        # Формируем запрос к GPT
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — дружелюбный помощник типографии, отвечай кратко и по делу."},
                {"role": "user", "content": message_text}
            ]
        )
        gpt_response = response.choices[0].message.content.strip()
        logger.info(f"🤖 Ответ GPT: {gpt_response}")

        # Получаем идентификаторы
        chat_id = data.get("chatId") or os.getenv("DEFAULT_CHAT_ID")
        channel_id = data.get("channelId") or os.getenv("DEFAULT_CHANNEL_ID")

        if not chat_id or not channel_id:
            logger.warning("❗ Не удалось извлечь chat_id или channel_id")
            return JSONResponse({"error": "Нет chat_id или channel_id"}, status_code=400)

        # Отправляем ответ в Wazzup
        async with httpx.AsyncClient() as http_client:
            result = await http_client.post(
                url="https://api.wazzup24.com/v3/message",
                headers={
                    "Authorization": f"Bearer {os.getenv('WAZZUP_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "chatId": chat_id,
                    "channelId": channel_id,
                    "text": gpt_response
                }
            )
            logger.info(f"📤 Ответ отправлен в Wazzup: {result.status_code}, {result.text}")

        return {"status": "ok", "reply": gpt_response}

    except Exception as e:
        logger.exception("❌ Ошибка обработки запроса")
        return JSONResponse({"error": str(e)}, status_code=500)
