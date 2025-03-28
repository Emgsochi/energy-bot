from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)


@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        logging.info(f"📨 Получены данные: {data}")

        if not isinstance(data, list) or len(data) == 0:
            return JSONResponse(content={"message": "No data"}, status_code=200)

        message_data = data[0]
        text = message_data.get("text") or message_data.get("message") or ""
        username = message_data.get("username") or message_data.get("Имя пользователя (только для Telegram)", "")
        messenger = message_data.get("messenger", "")

        logging.info(f"👤 Пользователь: {username}, 📩 Текст: {text}, 📱 Мессенджер: {messenger}")

        # Здесь можно вставить обработку через GPT и т.п.
        # Например:
        answer = f"{username}, вы написали: '{text}'. Спасибо за сообщение!"

        return JSONResponse(content={"reply": answer}, status_code=200)

    except Exception as e:
        logging.exception("❌ Ошибка при обработке запроса")
        return JSONResponse(content={"error": str(e)}, status_code=500)
