from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import json

app = FastAPI()
logging.basicConfig(level=logging.INFO)

@app.post("/wazzup/webhook")
async def webhook(request: Request):
    try:
        # Логируем тело запроса
        raw_body = await request.body()
        logging.info(f"📥 RAW BODY: {raw_body.decode('utf-8')}")

        data = await request.json()
        logging.info(f"📩 PARSED JSON: {json.dumps(data, ensure_ascii=False, indent=2)}")

        # Если данные в виде списка — берем первый элемент
        if isinstance(data, list):
            if not data:
                return JSONResponse({"message": "Нет данных"}, status_code=200)
            data = data[0]

        # Проверка, что это словарь
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Формат запроса должен быть JSON-объектом")

        # Проверка обязательных полей
        required_fields = ["text", "chat_id", "channel"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            error_msg = f"Недостаточно данных: {', '.join(missing)}"
            logging.warning(f"⚠️ {error_msg}")
            return JSONResponse({"error": error_msg}, status_code=400)

        # Извлечение данных
        text = data["text"]
        chat_id = data["chat_id"]
        channel = data["channel"]
        name = data.get("name", "Гость")

        # Ответ
        reply = f"{name}, ваш запрос «{text}» получен! Мы уже начали расчёт 🎯"
        logging.info(f"✅ Ответ: {reply}")

        return JSONResponse({"reply": reply})

    except Exception as e:
        logging.exception("❌ Ошибка при обработке запроса")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
