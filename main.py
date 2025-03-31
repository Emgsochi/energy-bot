from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import openai
import os
from extract_parameters import extract_parameters

app = FastAPI()

# Устанавливаем API-ключ OpenAI из переменной окружения
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/wazzup/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Универсальная обработка формата
    if payload is None or payload == "":
        data = {}
    elif isinstance(payload, list):
        data = payload[0] if len(payload) > 0 else {}
    elif isinstance(payload, dict):
        data = payload
    else:
        raise HTTPException(status_code=400, detail="Payload must be JSON object or array")

    # Извлекаем данные из запроса
    text = data.get("text", "")
    contact_name = data.get("contact_name", "")
    contact_id = data.get("contact_id", "")

    print(f"📩 Получено сообщение от {contact_name}: {text}")

    # Обработка параметров (кол-во, формат, размер, продукт)
    extracted = extract_parameters(text)
    print("🧠 Извлечённые параметры:", extracted)

    # Генерируем системную инструкцию и запрос для GPT
    system_prompt = (
        "Ты — дружелюбный помощник рекламного агентства Энерджи в Сочи. "
        "Ты помогаешь клиентам посчитать стоимость продукции и объясняешь, если что-то непонятно."
    )

    # Формируем пользовательский запрос с параметрами
    user_prompt = (
        f"Клиент спрашивает: {text}\n\n"
        f"В сообщении я нашёл такие параметры:\n"
        f"- Количество: {extracted.get('quantity') or 'не указано'}\n"
        f"- Размер: {extracted.get('size') or 'не указано'}\n"
        f"- Формат: {extracted.get('format') or 'не указан'}\n"
        f"- Продукт: {extracted.get('product') or 'не указан'}\n\n"
        "Ответь так, как если бы ты был менеджером агентства: дружелюбно, без лишней воды, и если нужно — уточни."
    )

    # Запрос к GPT
    gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    reply = gpt_response.choices[0].message.content.strip()
    print("🤖 Ответ GPT:", reply)

    # Ответ для Albato (чтобы переслать его обратно в Telegram через webhook)
    return JSONResponse(content={
        "text": reply,
        "contact_id": contact_id,
        "contact_name": contact_name
    })
