from fastapi import FastAPI, Request
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from extract_parameters import extract_parameters

app = FastAPI()

# Настройка OpenAI
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_credentials = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_credentials, scope)
client_gs = gspread.authorize(creds)

sheet_id = os.environ.get("GOOGLE_SHEET_ID")
sheet = client_gs.open_by_key(sheet_id).sheet1

# Получение всех строк прайса
sheet_data = sheet.get_all_records()


def find_price(params):
    for row in sheet_data:
        if (
            str(row["Формат"]).replace(" ", "") == params["format"].replace(" ", "") and
            str(row["Цветность"]).replace(" ", "") == params["color"].replace(" ", "") and
            int(row["Тираж"]) == int(params["quantity"])
        ):
            return row["Цена"]
    return None


def generate_answer(user_text):
    try:
        params = extract_parameters(user_text)
        price = find_price(params)
        if price:
            return f"Стоимость {params['quantity']} визиток {params['format']} {params['color']} — {price} ₽."
        else:
            return "Не нашёл цену для заданных параметров. Уточните формат, цветность и тираж."
    except Exception as e:
        return f"Произошла ошибка при обработке запроса: {str(e)}"


@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    try:
        data = await request.json()
        
        # Проверка: если список — берём первый элемент
        if isinstance(data, list):
            data = data[0]

        message_text = data.get("text", "")
        if not message_text:
            return {"error": "Пустое сообщение"}

        answer = generate_answer(message_text)

        print("Получено сообщение:", message_text)
        print("Ответ:", answer)

        return {"reply": answer}
    except Exception as e:
        print("Ошибка обработки:", e)
        return {"error": str(e)}
