from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    activity = State()
    goal = State()
    target_weight = State()


class MealInput(StatesGroup):
    waiting_type = State()
    waiting_description = State()


class WeightInput(StatesGroup):
    waiting_weight = State()


class ChatState(StatesGroup):
    waiting_question = State()
