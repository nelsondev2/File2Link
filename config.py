import os

class Config:
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL"))  # ID canal privado para logs
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "").split()]  # IDs admins
    EXPIRATION_HOURS = int(os.environ.get("EXPIRATION_HOURS", 4))
