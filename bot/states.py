from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    name = State()
    city = State()
    city_other = State()
    niche = State()
    niche_other = State()
    instagram = State()
    goal = State()


class Introduce(StatesGroup):
    text = State()


class SearchPartners(StatesGroup):
    query = State()


class SuggestTopic(StatesGroup):
    text = State()


class CreateMeeting(StatesGroup):
    date = State()
    time = State()
    topic = State()
    seats = State()
    confirm = State()
