from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import database as db
from config import ADMIN_IDS
from keyboards import student_main_menu, days_keyboard, slots_keyboard, back_button

router = Router()

WEEKDAY_RU = {
“Monday”: “Пн”, “Tuesday”: “Вт”, “Wednesday”: “Ср”,
“Thursday”: “Чт”, “Friday”: “Пт”, “Saturday”: “Сб”, “Sunday”: “Вс”
}

async def ensure_user(message: Message):
username = message.from_user.username or “”
full_name = message.from_user.full_name or “”
return await db.get_or_create_user(message.from_user.id, username, full_name)

@router.message(CommandStart())
async def cmd_start(message: Message):
user = await ensure_user(message)
if message.from_user.id in ADMIN_IDS:
from keyboards import admin_main_menu
await message.answer(
“👋 Добро пожаловать, <b>Администратор</b>!”,
reply_markup=admin_main_menu(),
parse_mode=“HTML”
)
else:
await message.answer(
f”👋 Привет, <b>{message.from_user.first_name}</b>!\n\n”
“Выбери действие:”,
reply_markup=student_main_menu(),
parse_mode=“HTML”
)

@router.callback_query(F.data == “start”)
async def back_to_start(call: CallbackQuery):
if call.from_user.id in ADMIN_IDS:
from keyboards import admin_main_menu
await call.message.edit_text(“🏠 Главное меню (Админ):”, reply_markup=admin_main_menu())
else:
await call.message.edit_text(“🏠 Главное меню:”, reply_markup=student_main_menu())

# ── Booking flow ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == “student:book”)
async def student_book(call: CallbackQuery):
days = await db.get_exam_days(only_enabled=True)
if not days:
await call.message.edit_text(
“😔 Нет доступных дней для записи.”,
reply_markup=back_button(“start”)
)
return
# Filter out days that have no active slots
available = []
for day in days:
slots = await db.get_slots_for_day(day[“id”], only_active=True)
if slots:
available.append(day)
if not available:
await call.message.edit_text(
“😔 Нет доступных слотов.”,
reply_markup=back_button(“start”)
)
return
await call.message.edit_text(
“📅 Выберите день зачёта:”,
reply_markup=days_keyboard(available, prefix=“book_day”)
)

@router.callback_query(F.data.startswith(“book_day:”))
async def pick_slot(call: CallbackQuery):
day_id = int(call.data.split(”:”)[1])
slots = await db.get_slots_for_day(day_id, only_active=True)
if not slots:
await call.answer(“Нет активных слотов в этот день.”, show_alert=True)
return

```
# Check which slots are full
booked_ids = set()
for s in slots:
    count = await db.count_bookings_for_slot(s["id"])
    if count >= s["capacity"]:
        booked_ids.add(s["id"])

await call.message.edit_text(
    "🕐 Выберите время:",
    reply_markup=slots_keyboard(slots, day_id, booked_ids)
)
```

@router.callback_query(F.data == “noop”)
async def noop(call: CallbackQuery):
await call.answer(“Этот слот занят.”, show_alert=True)

@router.callback_query(F.data.startswith(“book_slot:”))
async def confirm_booking(call: CallbackQuery):
slot_id = int(call.data.split(”:”)[1])
user = await db.get_user_by_telegram_id(call.from_user.id)
if not user:
await call.answer(“Пожалуйста, отправьте /start сначала.”, show_alert=True)
return

```
# Check existing active booking
existing = await db.get_active_booking_for_user(user["id"])
if existing:
    await call.answer(
        "У вас уже есть активная запись! Сначала отмените её.",
        show_alert=True
    )
    return

slot = await db.get_slot(slot_id)
if not slot:
    await call.answer("Слот не найден.", show_alert=True)
    return

count = await db.count_bookings_for_slot(slot_id)
if count >= slot["capacity"]:
    await call.answer("Этот слот уже занят.", show_alert=True)
    return

now = datetime.now().isoformat()
booking_id = await db.create_booking(slot_id, user["id"], now)

# Get day info
async with __import__("aiosqlite").connect(__import__("config").DB_PATH) as dbc:
    dbc.row_factory = __import__("aiosqlite").Row
    async with dbc.execute(
        "SELECT * FROM exam_days WHERE id=?", (slot["exam_day_id"],)
    ) as cur:
        day = dict(await cur.fetchone())

text = (
    f"✅ <b>Вы записаны на зачёт!</b>\n\n"
    f"📅 Дата: <b>{day['weekday']} {day['date']}</b>\n"
    f"🕐 Время: <b>{slot['start_time']}–{slot['end_time']}</b>\n"
)
if slot.get("subject"):
    text += f"📚 Предмет: <b>{slot['subject']}</b>\n"
if slot.get("topic"):
    text += f"📝 Тема: <b>{slot['topic']}</b>\n"
if slot.get("meet_link"):
    text += f"🔗 Google Meet: {slot['meet_link']}\n"
if slot.get("description"):
    text += f"\n💬 {slot['description']}"

await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("start"))

# Notify file
if slot.get("file_id"):
    await call.message.answer_document(slot["file_id"], caption="📎 Вопросы к зачёту")

# Notify admins
admin_text = (
    f"📢 <b>Новая запись!</b>\n"
    f"👤 {user['full_name']} (@{user.get('username', '—')})\n"
    f"📅 {day['weekday']} {day['date']} • {slot['start_time']}–{slot['end_time']}\n"
    f"📚 {slot.get('subject', '—')} / {slot.get('topic', '—')}"
)
bot = call.bot
for admin_id in ADMIN_IDS:
    try:
        await bot.send_message(admin_id, admin_text, parse_mode="HTML")
    except Exception:
        pass
```

# ── My exams ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == “student:my_exams”)
async def my_exams(call: CallbackQuery):
user = await db.get_user_by_telegram_id(call.from_user.id)
if not user:
await call.answer(“Сначала /start”, show_alert=True)
return
booking = await db.get_active_booking_for_user(user[“id”])
if not booking:
await call.message.edit_text(
“📭 У вас нет активных записей.”,
reply_markup=back_button(“start”)
)
return

```
text = (
    f"📖 <b>Ваш ближайший зачёт:</b>\n\n"
    f"📅 {booking['weekday']} {booking['date']}\n"
    f"🕐 {booking['start_time']}–{booking['end_time']}\n"
)
if booking.get("subject"):
    text += f"📚 {booking['subject']}\n"
if booking.get("topic"):
    text += f"📝 {booking['topic']}\n"
if booking.get("meet_link"):
    text += f"🔗 {booking['meet_link']}\n"
text += f"\n🟢 Статус: Активна"

await call.message.edit_text(text, parse_mode="HTML", reply_markup=back_button("start"))
```

# ── Cancel booking ────────────────────────────────────────────────────────────

@router.callback_query(F.data == “student:cancel”)
async def cancel_booking_init(call: CallbackQuery):
user = await db.get_user_by_telegram_id(call.from_user.id)
if not user:
await call.answer(“Сначала /start”, show_alert=True)
return
booking = await db.get_active_booking_for_user(user[“id”])
if not booking:
await call.message.edit_text(
“📭 Нет активной записи для отмены.”,
reply_markup=back_button(“start”)
)
return
from keyboards import confirm_cancel_kb
await call.message.edit_text(
f”❓ Отменить запись на <b>{booking[‘weekday’]} {booking[‘date’]}</b> “
f”в <b>{booking[‘start_time’]}</b>?”,
parse_mode=“HTML”,
reply_markup=confirm_cancel_kb(
f”confirm_cancel:{booking[‘id’]}”,
“start”
)
)

@router.callback_query(F.data.startswith(“confirm_cancel:”))
async def do_cancel(call: CallbackQuery):
booking_id = int(call.data.split(”:”)[1])
await db.cancel_booking(booking_id)

```
user = await db.get_user_by_telegram_id(call.from_user.id)
admin_text = (
    f"⚠️ <b>Отмена записи!</b>\n"
    f"👤 {user['full_name']} (@{user.get('username', '—')})\n"
    f"Запись #{booking_id} отменена."
)
for admin_id in ADMIN_IDS:
    try:
        await call.bot.send_message(admin_id, admin_text, parse_mode="HTML")
    except Exception:
        pass

await call.message.edit_text(
    "✅ Запись отменена. Слот освобождён.",
    reply_markup=back_button("start")
)
```
