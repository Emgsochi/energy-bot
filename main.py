import logging
import openai
import os
from fastapi import FastAPI, Request
import openpyxl
import re

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Загружаем Excel-файл
wb = openpyxl.load_workbook("bot_energy.xlsx", data_only=True)
sheet = wb["визитки цифра"]

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

def generate_answer(text, price_info=None):
    prompt_base = """
Ты — менеджер рекламного агентства "Энерджи" из Сочи. Отвечай как человек: живо, понятно и дружелюбно. Предлагай помощь, уточняй детали и веди диалог, как если бы ты писал клиенту сам. Отвечай на русском.
"""
    if price_info:
        prompt = prompt_base + f"\nКлиент спросил: '{text}'\nНайдено в прайсе: {price_info}\nОтветь клиенту, как менеджер."
    else:
        prompt = prompt_base + f"\nКлиент написал: '{text}'\nОтветь, задавая уточняющие вопросы, если нужно."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{ "role": "user", "content": prompt }]
    )
    return response['choices'][0]['message']['content']

@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    data = await request.json()
    text = data.get("text") or data.get("message") or ""

    qty, size, sides = parse_message(text)
    if qty and size and sides:
        price = find_price(qty, size, sides)
        price_info = f"{qty} визиток {size} {sides} — {price}₽" if price else None
    else:
        price_info = None

    reply = generate_answer(text, price_info)

    logging.info(f"📨 Клиент: {text}")
    logging.info(f"🤖 Ответ: {reply}")

    return {"reply": reply}
