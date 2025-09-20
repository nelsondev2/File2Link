import os
from datetime import datetime, timedelta
from flask import Flask, request
from pyrogram import Client, filters
from config import Config

# --- Inicializar bot ---
app_bot = Client(
    "File2Link",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    in_memory=True
)

# --- Almacenamiento temporal de enlaces ---
temp_links = {}

def generate_tg_link(message):
    if message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.audio:
        file_id = message.audio.file_id
    else:
        return None
    return f"https://t.me/{app_bot.me.username}?start={file_id}"

# --- Comandos del bot ---
@app_bot.on_message(filters.command("start"))
def start(client, message):
    message.reply_text(
        "👋 Bienvenido a File2Link.\n"
        "Envíame un archivo y te daré un enlace temporal de descarga (4h)."
    )

@app_bot.on_message(filters.private & (filters.document | filters.video | filters.audio))
def file_handler(client, message):
    msg = message.reply_text("📥 Procesando archivo...")
    link = generate_tg_link(message)
    expire_time = datetime.utcnow() + timedelta(hours=Config.EXPIRATION_HOURS)
    temp_links[link] = expire_time

    # Log en canal privado
    app_bot.send_message(
        Config.LOG_CHANNEL,
        f"📂 Archivo recibido de {message.from_user.id}\n"
        f"Link: {link}\n"
        f"Expira: {expire_time} UTC"
    )

    msg.edit_text(f"✅ Tu enlace (expira en {Config.EXPIRATION_HOURS}h):\n{link}")

@app_bot.on_message(filters.command("stats") & filters.user(Config.ADMINS))
def stats(client, message):
    total_links = len(temp_links)
    active_links = sum(1 for exp in temp_links.values() if exp > datetime.utcnow())
    message.reply_text(f"📊 Total generados: {total_links}\n🔹 Activos: {active_links}")

@app_bot.on_message(filters.command("clean") & filters.user(Config.ADMINS))
def clean_links(client, message):
    now = datetime.utcnow()
    expired = [link for link, exp in temp_links.items() if exp <= now]
    for link in expired:
        del temp_links[link]
    message.reply_text(f"🧹 Eliminados {len(expired)} enlaces expirados.")

# --- Servidor Flask ---
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "✅ File2Link Webhook activo."

@app_web.route(f"/{Config.BOT_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json()
    if update:
        app_bot.process_update(update)
    return "OK"

if __name__ == "__main__":
    # Iniciar bot y configurar webhook
    app_bot.start()
    app_bot.set_webhook(url=f"{Config.WEBHOOK_URL}/{Config.BOT_TOKEN}")

    port = int(os.environ.get("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)
