
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import openai

app = FastAPI()

# Конфигурация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Настройка Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON")),
    scope
)
client = gspread.authorize(creds)
sheet = client.open_by_key(os.getenv("GOOGLE_SHEET_ID")).sheet1

# Настройка OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/wazzup/webhook")
async def webhook(request: Request):
    try:
        # 1. Получаем данные
        data = await request.json()
        logging.info(f"📩 Получен запрос: {data}")

        if isinstance(data, list):
            if not data:
                return JSONResponse({"message": "Нет данных"}, 200)
            message = data[0]
        else:
            message = data

        # 2. Извлекаем параметры через GPT
        user_text = message.get("text", "")
        if not user_text:
            return await ask_for_clarification(message, "Не удалось распознать текст запроса")

        gpt_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник типографии. Извлеки из сообщения: тираж, формат (например 90x50), цветность (4+4, 4+0), бумагу, постобработку. Ответь только JSON."
                },
                {"role": "user", "content": user_text}
            ]
        )

        params = json.loads(gpt_response.choices[0].message.content)
        logging.info(f"🔍 Распознанные параметры: {params}")

        # 3. Поиск в прайсе
        price_info = find_in_price(params)
        if not price_info:
            return await offer_alternatives(params, message)

        # 4. Формируем ответ
        response_text = (
            f"✅ {params.get('тираж', '')} визиток {params.get('формат', '')} "
            f"{params.get('цветность', '')} — {price_info['price']} ₽.\n"
            "Всё верно? Напишите «да» для оформления или уточните детали."
        )

        return JSONResponse({"reply": response_text})

    except Exception as e:
        logging.error(f"❌ Ошибка: {str(e)}", exc_info=True)
        return JSONResponse({"error": "Произошла ошибка. Попробуйте позже"}, 500)

async def ask_for_clarification(message: dict, reason: str):
    username = message.get("fromName") or message.get("name") or "Клиент"
    response = (
        f"🤔 {username}, {reason}.\n"
        "Уточните:\n"
        "- Тираж (например: 300 шт)\n"
        "- Формат (например: 90x50 мм)\n"
        "- Цветность (4+4 или 4+0)"
    )
    return JSONResponse({"reply": response})

def find_in_price(params: dict) -> dict:
    try:
        records = sheet.get_all_records()
        for row in records:
            if (str(row.get('тираж')) == str(params.get('тираж')) and
                row.get('формат') == params.get('формат') and
                row.get('цветность') == params.get('цветность')):
                return {"price": row['цена'], "params": row}
        return {}
    except Exception as e:
        logging.error(f"Ошибка поиска в прайсе: {e}")
        return {}

async def offer_alternatives(params: dict, message: dict):
    alternatives = find_close_matches(params)
    if alternatives:
        options = "\n".join([f"- {alt['тираж']} шт, {alt['формат']}, {alt['цветность']} — {alt['цена']} ₽" 
                              for alt in alternatives])
        response = (
            f"💡 Мы не нашли точное совпадение, но есть похожие варианты:\n{options}\n"
            "Выберите подходящий или уточните параметры."
        )
    else:
        response = "К сожалению, мы не можем выполнить такой заказ. Попробуйте изменить параметры."

    return JSONResponse({"reply": response})

def find_close_matches(params: dict) -> list:
    return []  # Здесь можно добавить fuzzy-поиск

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
