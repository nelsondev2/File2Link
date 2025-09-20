import os
import asyncio
import httpx
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse
from pyrogram import Client, filters
import uvicorn

# === Variables de entorno ===
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = os.getenv("BASE_URL")  # Ej: https://tu-app.onrender.com
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
PORT = int(os.getenv("PORT", 10000))

# === Configuración FastAPI ===
app = FastAPI()
UPLOAD_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === Configuración Bot de Telegram ===
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# === Rutas de la API ===
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"url": f"{BASE_URL}/static/{file.filename}"}

@app.get("/static/{filename}")
def serve_file(filename: str):
    return FileResponse(os.path.join(UPLOAD_DIR, filename))

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    update = await request.json()
    await bot.process_update(update)
    return {"status": "ok"}

# === Handler del bot ===
@bot.on_message(filters.document)
async def handle_file(client, message):
    file = await message.download()
    async with httpx.AsyncClient() as client_http:
        with open(file, "rb") as f:
            resp = await client_http.post(f"{BASE_URL}/upload", files={"file": f})
    url = resp.json().get("url")
    await message.reply(f"Archivo subido: [Descargar]({url})", disable_web_page_preview=True)

# === Lifespan para iniciar y detener el bot ===
@app.on_event("startup")
async def startup():
    await bot.start()
    async with httpx.AsyncClient() as client_http:
        await client_http.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            params={"url": f"{BASE_URL}{WEBHOOK_PATH}"}
        )

@app.on_event("shutdown")
async def shutdown():
    await bot.stop()

# === Ejecutar servidor ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
