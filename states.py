from aiogram.fsm.state import State, StatesGroup

class AdminCreateDay(StatesGroup):
waiting_date = State()
waiting_start_time = State()
waiting_end_time = State()
waiting_interval = State()

class AdminSlotSettings(StatesGroup):
waiting_subject = State()
waiting_topic = State()
waiting_description = State()
waiting_meet_link = State()
waiting_file = State()
waiting_capacity = State()
waiting_max_score = State()

class AdminJournal(StatesGroup):
waiting_score = State()
waiting_comment = State()

class AdminPoll(StatesGroup):
waiting_question = State()
waiting_options = State()
waiting_multiple = State()

class StudentBook(StatesGroup):
waiting_day = State()
waiting_slot = State()
