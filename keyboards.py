from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ── Admin main menu ───────────────────────────────────────────────────────────

def admin_main_menu() -> InlineKeyboardMarkup:
return InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=“📅 Создать день зачёта”, callback_data=“admin:create_day”)],
[InlineKeyboardButton(text=“📋 Дни зачётов”, callback_data=“admin:list_days”)],
[InlineKeyboardButton(text=“👥 Все записи”, callback_data=“admin:all_bookings”)],
[InlineKeyboardButton(text=“📘 Журнал зачётов”, callback_data=“admin:journal”)],
[InlineKeyboardButton(text=“📤 Экспорт журнала”, callback_data=“admin:export_journal”)],
[InlineKeyboardButton(text=“📊 Опросы”, callback_data=“admin:polls_menu”)],
])

# ── Student main menu ─────────────────────────────────────────────────────────

def student_main_menu() -> InlineKeyboardMarkup:
return InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=“📅 Записаться на зачёт”, callback_data=“student:book”)],
[InlineKeyboardButton(text=“📖 Мои зачёты”, callback_data=“student:my_exams”)],
[InlineKeyboardButton(text=“❌ Отменить зачёт”, callback_data=“student:cancel”)],
[InlineKeyboardButton(text=“📊 Опросы”, callback_data=“student:polls”)],
])

# ── Generic ───────────────────────────────────────────────────────────────────

def back_button(callback: str = “start”) -> InlineKeyboardMarkup:
return InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=“◀️ Назад”, callback_data=callback)]
])

def confirm_cancel_kb(confirm_cb: str, cancel_cb: str) -> InlineKeyboardMarkup:
return InlineKeyboardMarkup(inline_keyboard=[
[
InlineKeyboardButton(text=“✅ Подтвердить”, callback_data=confirm_cb),
InlineKeyboardButton(text=“❌ Отмена”, callback_data=cancel_cb),
]
])

# ── Day selection ─────────────────────────────────────────────────────────────

def days_keyboard(days: list, prefix: str = “book_day”) -> InlineKeyboardMarkup:
buttons = []
for day in days:
label = f”📅 {day[‘weekday’]} {day[‘date’]}”
buttons.append([InlineKeyboardButton(text=label, callback_data=f”{prefix}:{day[‘id’]}”)])
buttons.append([InlineKeyboardButton(text=“◀️ Назад”, callback_data=“start”)])
return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── Slot selection ────────────────────────────────────────────────────────────

def slots_keyboard(slots: list, day_id: int, booked_ids: set) -> InlineKeyboardMarkup:
buttons = []
for s in slots:
if s[“id”] in booked_ids:
label = f”🔒 {s[‘start_time’]}–{s[‘end_time’]}”
cb = “noop”
else:
label = f”🕐 {s[‘start_time’]}–{s[‘end_time’]}”
cb = f”book_slot:{s[‘id’]}”
buttons.append([InlineKeyboardButton(text=label, callback_data=cb)])
buttons.append([InlineKeyboardButton(text=“◀️ Назад”, callback_data=“student:book”)])
return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── Journal status ────────────────────────────────────────────────────────────

def journal_status_kb(booking_id: int) -> InlineKeyboardMarkup:
statuses = [
(“✅ Провёл”, “done”),
(“⏰ Опоздал”, “late”),
(“❌ Не присутствовал”, “absent”),
(“🔄 Перенесён”, “rescheduled”),
]
buttons = [
[InlineKeyboardButton(text=label, callback_data=f”jstatus:{booking_id}:{code}”)]
for label, code in statuses
]
return InlineKeyboardMarkup(inline_keyboard=buttons)

def score_keyboard(booking_id: int, max_score: int = 10) -> InlineKeyboardMarkup:
row = []
buttons = []
for i in range(max_score + 1):
row.append(InlineKeyboardButton(text=str(i), callback_data=f”jscore:{booking_id}:{i}”))
if len(row) == 5:
buttons.append(row)
row = []
if row:
buttons.append(row)
return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── Poll voting ───────────────────────────────────────────────────────────────

def poll_options_kb(poll_id: int, options: list, voted_ids: list, is_multiple: bool) -> InlineKeyboardMarkup:
buttons = []
for opt in options:
check = “✅ “ if opt[“id”] in voted_ids else “”
buttons.append([
InlineKeyboardButton(
text=f”{check}{opt[‘option_text’]}”,
callback_data=f”vote:{poll_id}:{opt[‘id’]}”
)
])
if is_multiple:
buttons.append([
InlineKeyboardButton(text=“💾 Готово”, callback_data=f”vote_done:{poll_id}”)
])
return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── Admin poll management ─────────────────────────────────────────────────────

def admin_poll_kb(poll_id: int) -> InlineKeyboardMarkup:
return InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=“📊 Результаты”, callback_data=f”poll_results:{poll_id}”)],
[InlineKeyboardButton(text=“🔇 Закрыть опрос”, callback_data=f”poll_close:{poll_id}”)],
[InlineKeyboardButton(text=“🔔 Напомнить не проголосовавшим”, callback_data=f”poll_remind:{poll_id}”)],
[InlineKeyboardButton(text=“◀️ Назад”, callback_data=“admin:polls_menu”)],
])
