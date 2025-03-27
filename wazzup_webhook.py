from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/wazzup-webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("Получено сообщение:", data)
    # Здесь будет вызов обработки: GPT, прайс, Trello и т.д.
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
