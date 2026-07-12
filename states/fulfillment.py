from aiogram.fsm.state import State, StatesGroup


class FulfillmentState(StatesGroup):
    waiting_for_config = State()
