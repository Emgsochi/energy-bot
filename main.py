from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
import logging

app = FastAPI()

# Стандартная инициализация OpenAI клиента
# SDK сам подтянет OPENAI_API_KEY из переменных окружения
client = OpenAI()

# Логирование
logging.basicConfig(level=logging.INFO)

@app.post("/wazzup/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"📩 Пришёл запрос: {data}")

        # Если data — список
        if isinstance(data, list):
            if not data:
                return JSONResponse({"message": "Пустой список"}, status_code=200)
            data = data[0]

        text = data.get("text", "")
        name = data.get("fromName", "Клиент")

        if not text:
            return JSONResponse({"message": "Пустой текст"}, status_code=200)

        # Простой вызов OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — дружелюбный помощник."},
                {"role": "user", "content": text}
            ]
        )

        answer = response.choices[0].message.content.strip()
        return JSONResponse({"reply": f"{name}, ответ: {answer}"})

    except Exception as e:
        logging.exception("❌ Ошибка обработки запроса")
        return JSONResponse({"error": str(e)}, status_code=500)

# Для локального запуска
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
