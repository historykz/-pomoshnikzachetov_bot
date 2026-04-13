import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers_admin import router as admin_router
from handlers_student import router as student_router
from handlers_poll import router as poll_router
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

async def main():
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

```
dp.include_router(admin_router)
dp.include_router(student_router)
dp.include_router(poll_router)

await init_db()

scheduler = setup_scheduler(bot)
scheduler.start()

logger.info("Bot started")
try:
    await dp.start_polling(bot, drop_pending_updates=True)
finally:
    scheduler.shutdown()
    await bot.session.close()
```
if __name__ == "__main__":
    asyncio.run(main())
