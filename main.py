from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import json

app = FastAPI()

# Настройка логов
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.post("/wazzup/webhook")
async def webhook(request: Request):
    try:
        # Получаем тело запроса
        raw_body = await request.body()
        logging.info(f"📩 RAW body: {raw_body.decode('utf-8')}")

        data = await request.json()
        logging.info(f"✅ Parsed JSON: {json.dumps(data, ensure_ascii=False)}")

        # Если приходит список — берём первый элемент
        if isinstance(data, list):
            if not data:
                logging.warning("⚠️ Получен пустой список")
                return JSONResponse({"message": "Нет данных"}, status_code=200)
            data = data[0]

        if not isinstance(data, dict):
            logging.error("❌ Неверный формат данных (не dict)")
            return JSONResponse({"error": "Неверный формат данных"}, status_code=400)

        # Проверка обязательных полей
        required_fields = ["text", "chat_id", "channel"]
        missing = [field for field in required_fields if not data.get(field)]

        if missing:
            logging.warning(f"⚠️ Отсутствуют обязательные поля: {missing}")
            return JSONResponse({"error": f"Недостаточно данных: {', '.join(missing)}"}, status_code=400)

        # Извлекаем данные
        text = data.get("text")
        chat_id = data.get("chat_id")
        channel = data.get("channel")
        name = data.get("name", "Гость")

        # Ответ пользователю
        reply = f"{name}, ваш запрос «{text}» получен! Мы уже начали расчёт 🧮"

        logging.info(f"📤 Ответ клиенту: {reply}")
        return JSONResponse({"reply": reply})

    except Exception as e:
        logging.exception("❌ Ошибка при обработке запроса")
        return JSONResponse({"error": "Внутренняя ошибка сервера"}, status_code=500)
