from aiogram.fsm.state import State, StatesGroup


class ProfileForm(StatesGroup):
    waiting_name_choice = State()
    waiting_name_input = State()
    waiting_photo = State()
    waiting_sphere = State()
    waiting_activity = State()
    waiting_instagram = State()
    waiting_hobby = State()
