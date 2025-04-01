import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

# Инициализация логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI()

# Инициализация клиента OpenAI (берёт ключ из переменной окружения)
client = AsyncOpenAI()  # Никаких proxies и api_key не передаём вручную

@app.post("/wazzup/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"📩 Получены данные: {data}")

        # Обработка формата списка от Albato
        if isinstance(data, list):
            if not data:
                return JSONResponse({"message": "Пустой запрос"}, status_code=200)
            data = data[0]

        text = data.get("text", "")
        chat_id = data.get("chatId", "")
        messenger = data.get("messenger", "")
        from_name = data.get("fromName", "Клиент")

        if not text:
            return JSONResponse({"message": "Пустое сообщение"}, status_code=200)

        # Запрос к OpenAI
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты вежливый ассистент рекламного агентства Энерджи."},
                {"role": "user", "content": text}
            ]
        )

        ai_reply = response.choices[0].message.content.strip()
        logger.info(f"🤖 Ответ GPT: {ai_reply}")

        return JSONResponse({"reply": ai_reply}, status_code=200)

    except Exception as e:
        logger.exception("❌ Ошибка обработки запроса")
        return JSONResponse({"error": str(e)}, status_code=500)


# Для локального запуска (не используется на Render)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
