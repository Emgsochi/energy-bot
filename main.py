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

        if not isinstance(data, dict) or not data:
            logger.warning("⚠️ Пустой запрос или неверный формат")
            return JSONResponse(content={"message": "No data"}, status_code=200)

        text = data.get("text", "").strip()
        username = data.get("fromName", "Гость").strip()
        messenger = data.get("messenger", "unknown").lower()

        logger.info(
            f"👤 Пользователь: {username} | 📩 Текст: {text[:50]}... | 📱 Мессенджер: {messenger}"
        )

        answer = f"{username}, ваш запрос «{text}» принят! Скоро свяжемся с вами."

        return JSONResponse(content={"reply": answer}, status_code=200)

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {str(e)}")
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
