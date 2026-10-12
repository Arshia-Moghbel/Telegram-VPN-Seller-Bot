from aiogram.filters import BaseFilter
from aiogram.types import Message

from services.admin_service import get_ui_labels


class ButtonTextFilter(BaseFilter):
    def __init__(self, key: str):
        self.key = key

    async def __call__(self, message: Message) -> bool:
        if not message.text:
            return False
        return message.text == (await get_ui_labels())[self.key]
