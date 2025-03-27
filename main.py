import logging
from fastapi import FastAPI, Request
import openpyxl
import re

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Загружаем Excel-файл один раз при запуске
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

@app.post("/wazzup/webhook")
async def receive_message(request: Request):
    data = await request.json()
    text = data.get("text") or data.get("message") or ""
    qty, size, sides = parse_message(text)

    if qty and size and sides:
        price = find_price(qty, size, sides)
        if price:
            logging.info(f"✅ Цена найдена: {qty} визиток {size} {sides} = {price}₽")
        else:
            logging.warning(f"❌ Не найдено в прайсе: {qty} {size} {sides}")
    else:
        logging.warning(f"⚠️ Не удалось распознать параметры в сообщении: {text}")

    return {"status": "ok"}
