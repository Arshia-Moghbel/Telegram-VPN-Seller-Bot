from aiogram.fsm.state import State, StatesGroup


class AdminState(StatesGroup):
    waiting_for_setting_value = State()
    waiting_for_user_query = State()
    waiting_for_broadcast = State()
