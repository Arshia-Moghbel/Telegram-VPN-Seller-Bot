from aiogram.fsm.state import State, StatesGroup


class PlanState(StatesGroup):
    creating_name = State()
    creating_price = State()
    creating_duration = State()
    creating_traffic = State()
    creating_description = State()
    editing_field = State()
