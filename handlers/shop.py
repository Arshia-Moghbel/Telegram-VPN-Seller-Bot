from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from db import async_session
from database.models import Plan
from keyboards.shop import create_plans_keyboard
from services.order_service import create_order

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

    order = await create_order(
        telegram_id=callback.from_user.id,
        plan_id=plan_id
    )

    if order is None:
        await callback.message.answer(
            "❌ خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید."
        )
        return

    await callback.message.answer(
        f"✅ سفارش شما ثبت شد.\n\n"
        f"🆔 شماره سفارش: #{order.id}\n\n"
        f"💳 وضعیت: در انتظار پرداخت\n\n"
        f"لطفاً پرداخت را انجام دهید و رسید را ارسال کنید."
    )
