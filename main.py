from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

app = FastAPI()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        logger.info(f"📨 Получены данные: {data}")

        # Проверяем формат данных (ожидаем словарь)
        if not isinstance(data, dict) or not data:
            logger.warning("⚠️ Пустой запрос или неверный формат")
            return JSONResponse(content={"message": "No data"}, status_code=200)

        # Безопасно извлекаем данные из словаря
        text = data.get("text", "").strip()
        username = data.get("fromName", "Пользователь").strip()
        messenger = data.get("messenger", "неизвестный мессенджер").strip()

        logger.info(f"👤 Пользователь: {username}, 📩 Текст: {text}, 📱 Мессенджер: {messenger}")

        # Формируем и возвращаем ответ
        answer = f"{username}, ваш запрос «{text}» принят! Скоро свяжемся с вами."

        return JSONResponse(content={"reply": answer}, status_code=200)

    except Exception as e:
        logger.exception("❌ Ошибка при обработке запроса")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Точка входа (для локального запуска)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
