import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Важно! Импорт из httpx
import httpx  
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
app = FastAPI()

# Правильно создаем httpx-клиент
http_client = httpx.Client()  # proxies по умолчанию не передаются

# Инициализируем OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), http_client=http_client)

@app.get("/")
def root():
    return {"message": "OK"}

@app.post("/wazzup/webhook")
async def wazzup_webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"📩 Получен запрос: {data}")

        prompt = data.get("text", "Расскажи, чем могу помочь?")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты помощник типографии"},
                {"role": "user", "content": prompt}
            ]
        )

        reply = response.choices[0].message.content.strip()
        return {"reply": reply}

    except Exception as e:
        logging.exception("❌ Ошибка при обработке запроса")
        return JSONResponse(content={"error": str(e)}, status_code=500)
