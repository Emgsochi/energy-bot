import os
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
from httpx import Client

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Создаем FastAPI приложение
app = FastAPI()

# Явно создаем http-клиент без прокси
http_client = Client(proxies=None)

# Инициализируем OpenAI клиент, используя переменную окружения и http_client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=http_client
)

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"📩 Получен запрос: {data}")

        # Пример обработки текста (если есть)
        text = data.get("text", "Привет! Расскажи, чем могу помочь?")

        # Вызов OpenAI (GPT-3.5 или GPT-4)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — помощник типографии."},
                {"role": "user", "content": text}
            ]
        )

        reply = response.choices[0].message.content.strip()
        logging.info(f"💬 Ответ: {reply}")
        return {"reply": reply}

    except Exception as e:
        logging.exception("❌ Ошибка при обработке запроса")
        return JSONResponse(content={"error": str(e)}, status_code=500)
