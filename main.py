from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import os
from openai import OpenAI
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
client = OpenAI()

@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"📩 Получен запрос: {data}")

        # Исправленное извлечение данных
        message_text = data.get("text = {{message", {}).get("text}}", "").strip()
        chat_id = data.get("chat_id = {{chat", {}).get("id}}", "")
        channel_id = data.get("channel = {{messenger}}", "")

        if not (message_text and chat_id and channel_id):
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

        headers = {
            "Authorization": f"Bearer {os.getenv('WAZZUP_TOKEN')}",
            "Content-Type": "application/json"
        }

        json_body = {
            "chatId": chat_id,
            "channelId": channel_id,
            "text": gpt_response
        }

        async with httpx.AsyncClient() as http_client:
            result = await http_client.post("https://api.wazzup24.com/v3/message", headers=headers, json=json_body)
            logger.info(f"📤 Ответ отправлен в Wazzup: {result.status_code}, {result.text}")

        return {"status": "ok", "reply": gpt_response}

    except Exception as e:
        logger.exception("❌ Ошибка обработки запроса")
        return JSONResponse({"error": str(e)}, status_code=500)
