from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import os
from openai import OpenAI
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
client = OpenAI()  # Берёт ключ из переменной окружения OPENAI_API_KEY

@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"📩 Получен запрос: {data}")

        # Извлекаем данные
        chat_id = data.get("chatId")
        message_text = data.get("text")
        channel_id = data.get("channelId")

        if not message_text or not chat_id or not channel_id:
            logger.error("Отсутствуют обязательные поля в запросе")
            return JSONResponse({"error": "Отсутствуют обязательные поля"}, status_code=400)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — дружелюбный помощник типографии, отвечай кратко и по делу."},
                {"role": "user", "content": message_text}
            ]
        )

        gpt_response = response.choices[0].message.content.strip()
        logger.info(f"🤖 Ответ GPT: {gpt_response}")

        async with httpx.AsyncClient() as http_client:
            wazzup_response = await http_client.post(
                url="https://api.wazzup24.com/v3/message",
                headers={
                    "Authorization": f"Bearer {os.getenv('WAZZUP_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "chatId": chat_id,
                    "channelId": channel_id,
                    "text": gpt_response
                },
                timeout=30
            )

        logger.info(f"📤 Ответ отправлен в Wazzup: {wazzup_response.status_code}, {wazzup_response.text}")

        return {"status": "ok", "reply": gpt_response}

    except Exception as e:
        logger.exception("❌ Ошибка обработки запроса")
        return JSONResponse({"error": str(e)}, status_code=500)
