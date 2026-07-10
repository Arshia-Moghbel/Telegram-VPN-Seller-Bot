from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from db import async_session
from database.models import Plan
from keyboards.shop import create_plans_keyboard

router = Router()


@router.message(F.text == "🛒 خرید VPN")
async def buy_vpn(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Plan).where(Plan.is_active == True)
        )

        plans = result.scalars().all()

    if not plans:
        await message.answer(
            "در حال حاضر هیچ پلنی فعال نیست."
        )
        return

    keyboard = await create_plans_keyboard(plans)

    await message.answer(
        "🛒 پلن موردنظر خود را انتخاب کنید:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("plan_"))
async def select_plan(callback: CallbackQuery):

    await callback.answer()

    plan_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        result = await session.execute(
            select(Plan).where(Plan.id == plan_id)
        )

        plan = result.scalar_one_or_none()

    if plan is None:
        await callback.answer(
            "این پلن وجود ندارد.",
            show_alert=True
        )
        return

    await callback.message.answer(
        f"✅ پلن انتخاب شد:\n\n"
        f"📦 اشتراک: {plan.name}\n"
        f"⏳ مدت: {plan.duration} ماه\n"
        f"📊 حجم: {plan.traffic}\n"
        f"💰 مبلغ: {plan.price:,} تومان\n\n"
        f"لطفاً پرداخت را انجام دهید و رسید را ارسال کنید."
    )
