from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(labels: dict[str, str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=labels["ui_public_buy"])],
            [
                KeyboardButton(text=labels["ui_public_servers"]),
                KeyboardButton(text=labels["ui_public_guides"]),
            ],
            [KeyboardButton(text=labels["ui_public_support"])],
        ],
        resize_keyboard=True,
    )
