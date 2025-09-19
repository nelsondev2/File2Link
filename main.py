import os
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from config import Config

app = Client(
    "File2Link",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Diccionario para almacenar enlaces temporales
temp_links = {}

def generate_tg_link(message):
    # Usamos la CDN de Telegram para acceso directo
    file_id = message.document.file_id if message.document else message.video.file_id if message.video else message.audio.file_id
    return f"https://telegram.me/{app.me.username}?start={file_id}"

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("👋 Bienvenido a File2Link.\nEnvíame un archivo y te daré un enlace temporal de descarga (4h).")

@app.on_message(filters.private & (filters.document | filters.video | filters.audio))
def file_handler(client, message):
    msg = message.reply_text("📥 Procesando archivo...")
    link = generate_tg_link(message)
    expire_time = datetime.utcnow() + timedelta(hours=Config.EXPIRATION_HOURS)
    temp_links[link] = expire_time

    # Log
    app.send_message(Config.LOG_CHANNEL, f"📂 Archivo recibido de {message.from_user.id}\nLink: {link}\nExpira: {expire_time} UTC")

    msg.edit_text(f"✅ Tu enlace (expira en {Config.EXPIRATION_HOURS}h):\n{link}")

@app.on_message(filters.command("stats") & filters.user(Config.ADMINS))
def stats(client, message):
    total_links = len(temp_links)
    active_links = sum(1 for exp in temp_links.values() if exp > datetime.utcnow())
    message.reply_text(f"📊 Total generados: {total_links}\n🔹 Activos: {active_links}")

# Limpieza automática cada hora
@app.on_message(filters.command("clean") & filters.user(Config.ADMINS))
def clean_links(client, message):
    now = datetime.utcnow()
    expired = [link for link, exp in temp_links.items() if exp <= now]
    for link in expired:
        del temp_links[link]
    message.reply_text(f"🧹 Eliminados {len(expired)} enlaces expirados.")

app.run()
