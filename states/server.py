from aiogram.fsm.state import State, StatesGroup


class ServerState(StatesGroup):
    waiting_for_server = State()
