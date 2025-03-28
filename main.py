from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        logger.info(f"📨 Получен запрос: {data}")

        # ✅ Правильная проверка формата (список)
        if not isinstance(data, list) or not data:
            logger.warning("⚠️ Пустой запрос или неверный формат")
            return JSONResponse(content={"message": "No data"}, status_code=200)

        # ✅ Извлечение первого элемента списка
        message_data = data[0]

        text = message_data.get("text", "").strip()
        username = message_data.get("fromName", "Гость").strip()
        messenger = message_data.get("messenger", "unknown").lower()

        logger.info(
            f"👤 Пользователь: {username} | 📩 Текст: {text[:50]}... | 📱 Мессенджер: {messenger}"
        )

        answer = f"{username}, ваш запрос «{text}» принят! Скоро свяжемся с вами."

        return JSONResponse(content={"reply": answer}, status_code=200)

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {str(e)}")
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)

# Для локального запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
