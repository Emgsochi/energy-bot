import logging
from fastapi import FastAPI, Request
import openai
import os

app = FastAPI()
logging.basicConfig(level=logging.INFO)

openai.api_key = os.getenv("OPENAI_API_KEY")

PROMPT_TEMPLATE = """
Ты — профессиональный менеджер рекламного агентства «Энерджи Сочи». Агентство работает в Сочи, специализируется на digital-рекламе и креативных решениях.

Твой стиль: уверенный, клиентоориентированный, дружелюбный. Не шаблонный. Используй конкретику, метафоры, примеры. Всегда предлагай решение и зови к действию. Отвечай так, как будто ты живой менеджер агентства.

Вот сообщение от клиента:
"{message}"

Ответь как человек, в стиле агентства Energy.
"""

@app.post("/wazzup/webhook")
async def handle_message(request: Request):
    data = await request.json()
    message = data.get("text") or data.get("message") or ""
    
    if not message:
        logging.warning("Пустое сообщение.")
        return {"status": "no message"}

    prompt = PROMPT_TEMPLATE.format(message=message)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message.content.strip()
        logging.info(f"💬 Ответ: {reply}")
    except Exception as e:
        logging.error(f"Ошибка GPT: {e}")
        reply = "Прошу прощения, сейчас не могу ответить. Вернусь с ответом чуть позже!"

    return {"reply": reply}
