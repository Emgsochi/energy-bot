import os
import logging
import openai
from fastapi import FastAPI, Request

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
logging.basicConfig(level=logging.INFO)

PROMPT_TEMPLATE = """
Ты — профессиональный менеджер рекламного агентства «Энерджи» в Сочи.
Твоя задача — общаться с клиентами вежливо, дружелюбно и профессионально.
Отвечай как человек, предлагай решения, задавай уточняющие вопросы.
Если клиент написал что-то непонятное — задай уточнение.

Сообщение клиента: "{user_message}"
"""

@app.get("/")
def read_root():
    return {"message": "Energy Bot работает!"}

@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    data = await request.json()
    user_message = data.get("text") or data.get("message") or ""

    logging.info(f"📩 Получено сообщение: {user_message}")

    prompt = PROMPT_TEMPLATE.format(user_message=user_message)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # можно заменить на gpt-4 при необходимости
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        reply = response["choices"][0]["message"]["content"]
        logging.info(f"🤖 Ответ нейросети: {reply}")
    except Exception as e:
        logging.error(f"❌ Ошибка OpenAI: {e}")
        reply = "Прошу прощения, сейчас не могу ответить. Напишите позже."

    return {"response": reply}
