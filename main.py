from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from extract_parameters import extract_parameters
import logging

app = FastAPI()

@app.post("/wazzup/webhook")
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Если список - берём первый элемент
    if isinstance(payload, list):
        data = payload[0] if payload else {}
    elif isinstance(payload, dict):
        data = payload
    else:
        raise HTTPException(status_code=400, detail="Payload must be JSON object or array")

    # Безопасно получаем текст и имя
    text = data.get("text", "")
    contact_name = data.get("contact_name", "")

    print(f"📨 Получено сообщение: '{text}', отправитель: {contact_name}")

    # Вызов своей функции для извлечения параметров
    extracted = extract_parameters(text)
    print("📦 Извлечено:", extracted)

    # Здесь можно будет вызвать прайс и GPT обработку...

    return JSONResponse(content={
        "status": "ok",
        "contact": contact_name,
        "query": text,
        "params": extracted
    })
