from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/wazzup/webhook")  # ← исправили маршрут, теперь он правильный
async def receive_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if payload is None or payload == "":
        data = {}
    elif isinstance(payload, list):
        data = payload[0] if len(payload) > 0 else {}
    elif isinstance(payload, dict):
        data = payload
    else:
        raise HTTPException(status_code=400, detail="Payload must be JSON object or array")

    # Безопасно извлекаем поля из JSON
    text = data.get("text", "")
    contact_name = data.get("contact_name", "")
    contact_id = data.get("contact_id", "")
    messenger = data.get("messenger", "")
    timestamp = data.get("timestamp", "")

    print(f"📨 Получено сообщение: '{text}', отправитель: {contact_name}")

    # Тут можно вызывать GPT, обработку прайса, Trello и т.п.

    return JSONResponse(content={"status": "ok"})
