import aiosqlite
from config import DB_PATH

async def init_db():
async with aiosqlite.connect(DB_PATH) as db:
await db.executescript(”””
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
telegram_id INTEGER UNIQUE NOT NULL,
username TEXT,
full_name TEXT,
role TEXT DEFAULT ‘student’
);

```
    CREATE TABLE IF NOT EXISTS exam_days (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        weekday TEXT,
        enabled INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS exam_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_day_id INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        capacity INTEGER DEFAULT 1,
        subject TEXT,
        topic TEXT,
        description TEXT,
        meet_link TEXT,
        file_id TEXT,
        max_score INTEGER DEFAULT 10,
        FOREIGN KEY (exam_day_id) REFERENCES exam_days(id)
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        booked_at TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (slot_id) REFERENCES exam_slots(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS exam_journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL UNIQUE,
        attendance_status TEXT DEFAULT 'pending',
        score INTEGER,
        max_score INTEGER DEFAULT 10,
        teacher_comment TEXT,
        marked_at TEXT,
        FOREIGN KEY (booking_id) REFERENCES bookings(id)
    );

    CREATE TABLE IF NOT EXISTS polls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        is_multiple INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        expires_at TEXT,
        status TEXT DEFAULT 'active'
    );

    CREATE TABLE IF NOT EXISTS poll_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER NOT NULL,
        option_text TEXT NOT NULL,
        FOREIGN KEY (poll_id) REFERENCES polls(id)
    );

    CREATE TABLE IF NOT EXISTS poll_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        poll_id INTEGER NOT NULL,
        option_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        voted_at TEXT NOT NULL,
        FOREIGN KEY (poll_id) REFERENCES polls(id),
        FOREIGN KEY (option_id) REFERENCES poll_options(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    await db.commit()
```

async def get_or_create_user(telegram_id: int, username: str, full_name: str) -> dict:
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“SELECT * FROM users WHERE telegram_id=?”, (telegram_id,)
) as cur:
row = await cur.fetchone()
if row:
await db.execute(
“UPDATE users SET username=?, full_name=? WHERE telegram_id=?”,
(username, full_name, telegram_id)
)
await db.commit()
async with db.execute(
“SELECT * FROM users WHERE telegram_id=?”, (telegram_id,)
) as cur:
row = await cur.fetchone()
return dict(row)
await db.execute(
“INSERT INTO users (telegram_id, username, full_name) VALUES (?,?,?)”,
(telegram_id, username, full_name)
)
await db.commit()
async with db.execute(
“SELECT * FROM users WHERE telegram_id=?”, (telegram_id,)
) as cur:
row = await cur.fetchone()
return dict(row)

async def get_user_by_telegram_id(telegram_id: int):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“SELECT * FROM users WHERE telegram_id=?”, (telegram_id,)
) as cur:
row = await cur.fetchone()
return dict(row) if row else None

async def get_all_students():
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“SELECT * FROM users WHERE role=‘student’”
) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]

# ── Exam days ────────────────────────────────────────────────────────────────

async def create_exam_day(date: str, weekday: str) -> int:
async with aiosqlite.connect(DB_PATH) as db:
cur = await db.execute(
“INSERT INTO exam_days (date, weekday) VALUES (?,?)”, (date, weekday)
)
await db.commit()
return cur.lastrowid

async def get_exam_days(only_enabled=True):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
q = “SELECT * FROM exam_days”
if only_enabled:
q += “ WHERE enabled=1”
q += “ ORDER BY date”
async with db.execute(q) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]

async def toggle_exam_day(day_id: int, enabled: int):
async with aiosqlite.connect(DB_PATH) as db:
await db.execute(
“UPDATE exam_days SET enabled=? WHERE id=?”, (enabled, day_id)
)
await db.commit()

# ── Exam slots ────────────────────────────────────────────────────────────────

async def create_exam_slot(
exam_day_id: int, start_time: str, end_time: str,
subject: str = None, topic: str = None, description: str = None,
meet_link: str = None, file_id: str = None,
capacity: int = 1, max_score: int = 10
) -> int:
async with aiosqlite.connect(DB_PATH) as db:
cur = await db.execute(
“”“INSERT INTO exam_slots
(exam_day_id, start_time, end_time, subject, topic,
description, meet_link, file_id, capacity, max_score)
VALUES (?,?,?,?,?,?,?,?,?,?)”””,
(exam_day_id, start_time, end_time, subject, topic,
description, meet_link, file_id, capacity, max_score)
)
await db.commit()
return cur.lastrowid

async def get_slots_for_day(exam_day_id: int, only_active=True):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
q = “SELECT * FROM exam_slots WHERE exam_day_id=?”
if only_active:
q += “ AND is_active=1”
q += “ ORDER BY start_time”
async with db.execute(q, (exam_day_id,)) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]

async def get_slot(slot_id: int):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“SELECT * FROM exam_slots WHERE id=?”, (slot_id,)
) as cur:
row = await cur.fetchone()
return dict(row) if row else None

async def update_slot(slot_id: int, **kwargs):
allowed = {“subject”, “topic”, “description”, “meet_link”, “file_id”,
“capacity”, “max_score”, “is_active”}
fields = {k: v for k, v in kwargs.items() if k in allowed}
if not fields:
return
set_clause = “, “.join(f”{k}=?” for k in fields)
values = list(fields.values()) + [slot_id]
async with aiosqlite.connect(DB_PATH) as db:
await db.execute(
f”UPDATE exam_slots SET {set_clause} WHERE id=?”, values
)
await db.commit()

async def count_bookings_for_slot(slot_id: int) -> int:
async with aiosqlite.connect(DB_PATH) as db:
async with db.execute(
“SELECT COUNT(*) FROM bookings WHERE slot_id=? AND status=‘active’”,
(slot_id,)
) as cur:
row = await cur.fetchone()
return row[0]

# ── Bookings ────────────────────────────────────────────────────────────────

async def create_booking(slot_id: int, user_id: int, booked_at: str) -> int:
async with aiosqlite.connect(DB_PATH) as db:
cur = await db.execute(
“INSERT INTO bookings (slot_id, user_id, booked_at) VALUES (?,?,?)”,
(slot_id, user_id, booked_at)
)
await db.commit()
return cur.lastrowid

async def get_active_booking_for_user(user_id: int):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“”“SELECT b.*, s.start_time, s.end_time, s.subject, s.topic,
s.meet_link, s.file_id, s.exam_day_id,
d.date, d.weekday
FROM bookings b
JOIN exam_slots s ON b.slot_id=s.id
JOIN exam_days d ON s.exam_day_id=d.id
WHERE b.user_id=? AND b.status=‘active’
ORDER BY d.date, s.start_time
LIMIT 1”””,
(user_id,)
) as cur:
row = await cur.fetchone()
return dict(row) if row else None

async def cancel_booking(booking_id: int):
async with aiosqlite.connect(DB_PATH) as db:
await db.execute(
“UPDATE bookings SET status=‘cancelled’ WHERE id=?”, (booking_id,)
)
await db.commit()

async def get_all_bookings(date_filter=None, status_filter=“active”):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
params = []
q = “”“SELECT b.*, u.username, u.full_name, u.telegram_id,
s.start_time, s.end_time, s.subject, s.topic,
d.date, d.weekday
FROM bookings b
JOIN users u ON b.user_id=u.id
JOIN exam_slots s ON b.slot_id=s.id
JOIN exam_days d ON s.exam_day_id=d.id
WHERE 1=1”””
if status_filter:
q += “ AND b.status=?”
params.append(status_filter)
if date_filter:
q += “ AND d.date=?”
params.append(date_filter)
q += “ ORDER BY d.date, s.start_time”
async with db.execute(q, params) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]

async def get_bookings_for_slot(slot_id: int):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“”“SELECT b.*, u.username, u.full_name, u.telegram_id
FROM bookings b
JOIN users u ON b.user_id=u.id
WHERE b.slot_id=? AND b.status=‘active’”””,
(slot_id,)
) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]

# ── Journal ────────────────────────────────────────────────────────────────

async def upsert_journal(booking_id: int, attendance_status: str,
score: int = None, max_score: int = 10,
teacher_comment: str = None, marked_at: str = None):
async with aiosqlite.connect(DB_PATH) as db:
await db.execute(
“”“INSERT INTO exam_journal
(booking_id, attendance_status, score, max_score, teacher_comment, marked_at)
VALUES (?,?,?,?,?,?)
ON CONFLICT(booking_id) DO UPDATE SET
attendance_status=excluded.attendance_status,
score=excluded.score,
max_score=excluded.max_score,
teacher_comment=excluded.teacher_comment,
marked_at=excluded.marked_at”””,
(booking_id, attendance_status, score, max_score, teacher_comment, marked_at)
)
await db.commit()

async def get_journal_entries(
date_filter=None, status_filter=None,
subject_filter=None, user_filter=None
):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
params = []
q = “”“SELECT j.*, b.slot_id, b.user_id,
u.username, u.full_name, u.telegram_id,
s.start_time, s.end_time, s.subject, s.topic,
d.date, d.weekday
FROM exam_journal j
JOIN bookings b ON j.booking_id=b.id
JOIN users u ON b.user_id=u.id
JOIN exam_slots s ON b.slot_id=s.id
JOIN exam_days d ON s.exam_day_id=d.id
WHERE 1=1”””
if date_filter:
q += “ AND d.date=?”
params.append(date_filter)
if status_filter:
q += “ AND j.attendance_status=?”
params.append(status_filter)
if subject_filter:
q += “ AND s.subject LIKE ?”
params.append(f”%{subject_filter}%”)
if user_filter:
q += “ AND (u.username LIKE ? OR u.full_name LIKE ?)”
params.extend([f”%{user_filter}%”, f”%{user_filter}%”])
q += “ ORDER BY d.date, s.start_time”
async with db.execute(q, params) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]

# ── Polls ────────────────────────────────────────────────────────────────────

async def create_poll(question: str, is_multiple: int, created_at: str,
expires_at: str = None) -> int:
async with aiosqlite.connect(DB_PATH) as db:
cur = await db.execute(
“INSERT INTO polls (question, is_multiple, created_at, expires_at) VALUES (?,?,?,?)”,
(question, is_multiple, created_at, expires_at)
)
await db.commit()
return cur.lastrowid

async def add_poll_option(poll_id: int, option_text: str) -> int:
async with aiosqlite.connect(DB_PATH) as db:
cur = await db.execute(
“INSERT INTO poll_options (poll_id, option_text) VALUES (?,?)”,
(poll_id, option_text)
)
await db.commit()
return cur.lastrowid

async def get_poll(poll_id: int):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(“SELECT * FROM polls WHERE id=?”, (poll_id,)) as cur:
row = await cur.fetchone()
return dict(row) if row else None

async def get_poll_options(poll_id: int):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“SELECT * FROM poll_options WHERE poll_id=?”, (poll_id,)
) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]

async def get_active_polls():
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“SELECT * FROM polls WHERE status=‘active’ ORDER BY created_at DESC”
) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]

async def record_vote(poll_id: int, option_id: int, user_id: int, voted_at: str):
async with aiosqlite.connect(DB_PATH) as db:
# Prevent duplicate single-choice votes on same option
async with db.execute(
“SELECT id FROM poll_votes WHERE poll_id=? AND option_id=? AND user_id=?”,
(poll_id, option_id, user_id)
) as cur:
existing = await cur.fetchone()
if existing:
return False
await db.execute(
“INSERT INTO poll_votes (poll_id, option_id, user_id, voted_at) VALUES (?,?,?,?)”,
(poll_id, option_id, user_id, voted_at)
)
await db.commit()
return True

async def get_user_votes_in_poll(poll_id: int, user_id: int):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“SELECT option_id FROM poll_votes WHERE poll_id=? AND user_id=?”,
(poll_id, user_id)
) as cur:
rows = await cur.fetchall()
return [r[“option_id”] for r in rows]

async def get_poll_results(poll_id: int):
“”“Returns {option_id: {“text”: …, “count”: …, “voters”: […]}}”””
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“SELECT * FROM poll_options WHERE poll_id=?”, (poll_id,)
) as cur:
options = [dict(r) for r in await cur.fetchall()]

```
    results = {}
    for opt in options:
        async with db.execute(
            """SELECT pv.option_id, u.username, u.full_name
               FROM poll_votes pv
               JOIN users u ON pv.user_id=u.id
               WHERE pv.poll_id=? AND pv.option_id=?""",
            (poll_id, opt["id"])
        ) as cur:
            voters = [dict(r) for r in await cur.fetchall()]
        results[opt["id"]] = {
            "text": opt["option_text"],
            "count": len(voters),
            "voters": voters
        }
    return results
```

async def close_poll(poll_id: int):
async with aiosqlite.connect(DB_PATH) as db:
await db.execute(
“UPDATE polls SET status=‘closed’ WHERE id=?”, (poll_id,)
)
await db.commit()

async def get_non_voters(poll_id: int):
async with aiosqlite.connect(DB_PATH) as db:
db.row_factory = aiosqlite.Row
async with db.execute(
“”“SELECT * FROM users WHERE role=‘student’
AND id NOT IN (
SELECT DISTINCT user_id FROM poll_votes WHERE poll_id=?
)”””,
(poll_id,)
) as cur:
rows = await cur.fetchall()
return [dict(r) for r in rows]
