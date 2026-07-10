from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🛒 خرید VPN"),
            KeyboardButton(text="💎 تعرفه‌ها")
        ],
        [
            KeyboardButton(text="🌍 سرورها"),
            KeyboardButton(text="📖 آموزش اتصال")
        ],
        [
            KeyboardButton(text="📞 پشتیبانی")
        ]
    ],
    resize_keyboard=True
)