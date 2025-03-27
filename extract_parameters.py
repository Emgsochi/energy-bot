import re

SYNONYMS = {
    "двухсторонние": "4+4",
    "двухсторонних": "4+4",
    "двусторонние": "4+4",
    "двусторонних": "4+4",
    "односторонние": "4+0",
    "односторонних": "4+0",
    "визитка": "визитки",
    "визитки": "визитки",
    "визиток": "визитки",
    "90х50": "90x50",
}

def extract_parameters(query: str) -> dict:
    query = query.lower()

    # Синонимы
    for word, replacement in SYNONYMS.items():
        query = query.replace(word, replacement)

    # Кол-во
    quantity_match = re.search(r"\d+", query)
    quantity = int(quantity_match.group()) if quantity_match else None

    # Размер
    size_match = re.search(r"\d{2,4}[xхХ×*]\d{2,4}", query)
    size = size_match.group().replace("х", "x").replace("×", "x") if size_match else None

    # Формат
    format_match = re.search(r"4\+4|4\+0", query)
    format_value = format_match.group() if format_match else None

    # Продукт
    if re.search(r"визитк", query):
        product = "визитки"
    else:
        product = None

    return {
        "product": product,
        "format": format_value,
        "size": size,
        "quantity": quantity
    }
