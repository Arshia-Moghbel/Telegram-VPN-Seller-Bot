from aiogram.fsm.state import State, StatesGroup


class CouponState(StatesGroup):
    creating_code = State()
    creating_type = State()
    creating_value = State()
    creating_limit = State()
    waiting_for_code = State()
