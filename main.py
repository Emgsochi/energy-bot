from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
import logging

app = FastAPI()

# В openai==1.9.0 всё работает корректно без api_key и proxies
client = OpenAI()

logging.basicConfig(level=logging.INFO)

@app.post("/wazzup/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logging.info(f"📩 Получен запрос: {data}")

        if isinstance(data, list):
            if not data:
                return JSONResponse({"message": "Пустой список"}, status_code=200)
            data = data[0]

        text = data.get("text", "")
        name = data.get("fromName", "Клиент")

        if not text:
            return JSONResponse({"message": "Пустой текст"}, status_code=200)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты — дружелюбный помощник."},
                {"role": "user", "content": text}
            ]
        )

        reply = response.choices[0].message.content.strip()
        return JSONResponse({"reply": f"{name}, ответ: {reply}"})

    except Exception as e:
        logging.exception("❌ Ошибка обработки запроса")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
