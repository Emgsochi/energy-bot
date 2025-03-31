from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/webhook")
async def receive_webhook(request: Request):
    # Пытаемся получить JSON из запроса
    try:
        payload = await request.json()
    except Exception:
        # Если JSON некорректен или отсутствует
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Обработка разных форматов тела запроса
    if payload is None or payload == []:
        # Случай, когда тело пустое или пустой массив
        data = {}
    elif isinstance(payload, list):
        # Если прислали список объектов, возьмём первый элемент (или обработаем все по очереди)
        if len(payload) > 0:
            data = payload[0]  # берём первый объект из списка
        else:
            data = {}
    elif isinstance(payload, dict):
        # Если пришёл JSON-объект (словарь)
        data = payload
    else:
        # Неподдерживаемый формат данных
        raise HTTPException(status_code=400, detail="Payload must be JSON object or array")

    # Безопасно извлекаем нужные поля с значениями по умолчанию
    text = data.get("text", "")  # текст сообщения (по умолчанию пустая строка)
    contact_name = data.get("contact_name", "")  # имя контакта (по умолчанию пустая строка)
    # ... извлечение других потенциальных полей ...
    # Например:
    # timestamp = data.get("timestamp", "")
    # messenger = data.get("messenger", "")

    # Логируем полученную информацию (для отладки)
    print(f"Получено сообщение: '{text}', отправитель: '{contact_name}'")
    # Здесь можно добавить любую необходимую обработку полученных данных,
    # например, сохранить их в базе, отправить в другой сервис и т.д.

    # Возвращаем подтверждение успешного приема
    return JSONResponse(content={"status": "ok"})
