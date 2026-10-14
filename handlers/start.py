from db import async_session
from database.models import User
from services.admin_service import get_ui_labels
from services.admin_service import get_content_settings
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
            content = await get_content_settings()
            await message.answer(content["content_blocked"])
            return

    content = await get_content_settings()
    await message.answer(
        content["content_welcome"],
        reply_markup=main_menu(await get_ui_labels()),
    )
