from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database as db
from config import ADMIN_IDS
from keyboards import journal_status_kb

def setup_scheduler(bot) -> AsyncIOScheduler:
scheduler = AsyncIOScheduler()

```
# Check every minute for upcoming exams (30min and 5min reminders)
scheduler.add_job(send_reminders, "interval", minutes=1, args=[bot])

# Check every minute for exams that just ended → prompt admin for journal
scheduler.add_job(prompt_journal, "interval", minutes=1, args=[bot])

return scheduler
```

async def send_reminders(bot):
now = datetime.now()
bookings = await db.get_all_bookings(status_filter=“active”)
for b in bookings:
try:
exam_dt = datetime.strptime(f”{b[‘date’]} {b[‘start_time’]}”, “%Y-%m-%d %H:%M”)
except Exception:
continue

```
    diff_minutes = (exam_dt - now).total_seconds() / 60

    # 30-minute reminder
    if 29 <= diff_minutes <= 31:
        await _send_reminder(bot, b, "⏰ До вашего зачёта <b>30 минут!</b>")
    # 5-minute reminder
    elif 4 <= diff_minutes <= 6:
        await _send_reminder(bot, b, "🔔 До вашего зачёта <b>5 минут!</b>")
```

async def _send_reminder(bot, booking: dict, headline: str):
text = (
f”{headline}\n\n”
f”📅 {booking.get(‘weekday’, ‘’)} {booking.get(‘date’, ‘’)}\n”
f”🕐 {booking.get(‘start_time’, ‘’)}–{booking.get(‘end_time’, ‘’)}\n”
)
if booking.get(“subject”):
text += f”📚 {booking[‘subject’]}\n”
if booking.get(“topic”):
text += f”📝 {booking[‘topic’]}\n”
if booking.get(“meet_link”):
text += f”🔗 {booking[‘meet_link’]}\n”

```
try:
    await bot.send_message(booking["telegram_id"], text, parse_mode="HTML")
    if booking.get("file_id"):
        await bot.send_document(booking["telegram_id"], booking["file_id"])
except Exception:
    pass

# Also notify admins
admin_text = (
    f"🔔 <b>Напоминание!</b> Скоро зачёт:\n"
    f"👤 {booking.get('full_name', '')} "
    f"(@{booking.get('username', '')})\n"
    f"📅 {booking.get('date', '')} {booking.get('start_time', '')}–{booking.get('end_time', '')}"
)
for admin_id in ADMIN_IDS:
    try:
        await bot.send_message(admin_id, admin_text, parse_mode="HTML")
    except Exception:
        pass
```

async def prompt_journal(bot):
“”“After a slot ends, ask admin to fill in the journal.”””
now = datetime.now()
bookings = await db.get_all_bookings(status_filter=“active”)
for b in bookings:
try:
exam_end_dt = datetime.strptime(f”{b[‘date’]} {b[‘end_time’]}”, “%Y-%m-%d %H:%M”)
except Exception:
continue

```
    # Within 1 minute of ending
    diff = (now - exam_end_dt).total_seconds() / 60
    if 0 <= diff <= 1:
        # Check if already journaled
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(DB_PATH) as dbc:
            async with dbc.execute(
                "SELECT id FROM exam_journal WHERE booking_id=?", (b["id"],)
            ) as cur:
                existing = await cur.fetchone()

        if existing:
            continue

        text = (
            f"📋 <b>Зачёт завершён!</b>\n\n"
            f"👤 {b.get('full_name', '')} (@{b.get('username', '')})\n"
            f"📅 {b.get('weekday', '')} {b.get('date', '')} "
            f"{b.get('start_time', '')}–{b.get('end_time', '')}\n"
            f"📚 {b.get('subject', '—')} / {b.get('topic', '—')}\n\n"
            f"Отметьте результат:"
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id, text,
                    parse_mode="HTML",
                    reply_markup=journal_status_kb(b["id"])
                )
            except Exception:
                pass
```
