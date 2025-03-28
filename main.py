import os
import logging
import openpyxl
import re
import requests
from fastapi import FastAPI, Request
from openai import OpenAI

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Загружаем Excel-файл один раз
wb = openpyxl.load_workbook("bot_energy.xlsx", data_only=True)
sheet = wb["визитки цифра"]

# GPT-ключ из переменных окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Основной промт
BASE_PROMPT = """
Ты — профессиональный менеджер рекламного агентства "Энерджи" в Сочи. Общайся вежливо, дружелюбно и по делу.
Отвечай на вопросы клиентов, помогай подобрать услугу, стоимость, дизайн, сроки. Не используй шаблоны.
"""

def parse_message(text):
    match = re.search(r"(\d+)\s+визитк[иа]\s+(\d+)[xхXХ](\d+)\s+(двух|одно)сторонн", text, re.IGNORECASE)
    if match:
        qty = int(match.group(1))
        width = match.group(2)
        height = match.group(3)
        side = match.group(4).lower()
        format_str = f"{width}x{height}"
        side_str = "4+4" if side == "двух" else "4+0"
        return qty, format_str, side_str
    return None, None, None

def find_price(qty, format_str, side_str):
    for row in sheet.iter_rows(min_row=2, values_only=True):
        row_qty, row_format, row_side, price = row[:4]
        if (int(row_qty) == qty and row_format == format_str and row_side == side_str):
            return price
    return None

def ask_gpt(message):
    full_prompt = BASE_PROMPT + f"\nКлиент: {message}\nМенеджер:"
    response = client.chat.completions.create(
        model="gpt-4",  # или gpt-3.5-turbo
        messages=[{"role": "user", "content": full_prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    data = await request.json()
    text = data.get("text") or data.get("message") or ""

    qty, size, sides = parse_message(text)
    if qty and size and sides:
        price = find_price(qty, size, sides)
        if price:
            reply = f"{qty} визиток {size} {sides} — это {price}₽. Хотите оформить заказ?"
        else:
            reply = f"Не нашёл точную цену на {qty} визиток {size} {sides}, но могу уточнить!"
    else:
        reply = ask_gpt(text)

    logging.info(f"Ответ клиенту: {reply}")
    return {"response": reply}
