import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI

load_dotenv()  # Загружаем переменные из .env (если используешь локально)

# Явно передаём API ключ — это обязательно
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()


class Message(BaseModel):
    message: str


@app.post("/wazzup/webhook")
async def handle_wazzup(request: Request):
    try:
        data = await request.json()
        print("Получено сообщение:", data)

        user_text = extract_text(data)
        if not user_text:
            return {"status": "ignored", "reason": "no_text"}

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты — дружелюбный ассистент."},
                {"role": "user", "content": user_text},
            ],
        )

        reply = response.choices[0].message.content
        print("Ответ GPT:", reply)
        return {"status": "ok", "reply": reply}

    except Exception as e:
        print("Ошибка:", e)
        return {"status": "error", "detail": str(e)}


def extract_text(data):
    # Обработка формата Wazzup (может быть dict или list)
    if isinstance(data, dict) and "messages" in data:
        for message in data["messages"]:
            if "text" in message:
                return message["text"]
    elif isinstance(data, list):
        for item in data:
            if "text" in item:
                return item["text"]
    return None
