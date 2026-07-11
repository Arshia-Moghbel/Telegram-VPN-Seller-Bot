from aiogram.fsm.state import State, StatesGroup


class OrderState(StatesGroup):
    waiting_for_receipt = State()