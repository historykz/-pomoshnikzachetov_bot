import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip()]

DB_PATH = os.getenv("DB_PATH", "exam_bot.db")
