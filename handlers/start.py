from db import async_session
from database.models import User
from sqlalchemy import select
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start(message: Message):

    from keyboards.user import main_menu

    async with async_session() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            new_user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username
            )

            session.add(new_user)
            await session.commit()

        elif user.is_blocked:
            await message.answer("⛔ حساب شما مسدود شده است. برای پیگیری با پشتیبانی تماس بگیرید.")
            return

    await message.answer(
        "سلام 👋\n\n"
        "به VPNifi خوش آمدی.\n\n"
        "از منوی زیر یک گزینه را انتخاب کن:",
        reply_markup=main_menu
    )
