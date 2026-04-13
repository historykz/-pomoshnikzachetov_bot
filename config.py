import os

BOT_TOKEN = os.getenv(“8409766223:AAFYEunOGMFojqhajrM5P9EdUzaUAeP8ojQ”, “YOUR_BOT_TOKEN_HERE”)

# Comma-separated admin Telegram IDs, e.g. “8368153725”

ADMIN_IDS_RAW = os.getenv(“ADMIN_IDS”, “123456789”)
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(”,”) if x.strip()]

DB_PATH = os.getenv(“DB_PATH”, “exam_bot.db”)
