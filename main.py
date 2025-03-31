from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

@app.post("/wazzup/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"📩 Получен запрос: {data}")

        # Обработка пустого списка
        if isinstance(data, list):
            if not data:
                return JSONResponse({"message": "Нет данных"}, status_code=200)
            data = data[0]

        # Проверка ключей
        if not isinstance(data, dict) or not data.get("text"):
            return JSONResponse({"message": "Нет текста"}, status_code=200)

        name = data.get("name", "Клиент")
        text = data.get("text")
        chat_id = data.get("chat_id")
        channel = data.get("channel")

        reply = f"{name}, ваш запрос «{text}» получен. Ожидайте расчёт 😉"

        return JSONResponse({"reply": reply})
    
    except Exception as e:
        logging.exception("Ошибка при обработке запроса")
        return JSONResponse({"error": "Внутренняя ошибка сервера"}, status_code=500)
