from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from db import async_session
from database.models import Plan
from config import settings
from keyboards.shop import create_plans_keyboard
from services.order_service import create_order
from states.payment import PaymentState

router = Router()


def plans_summary(plans: list[Plan]) -> str:
    details = []
    for plan in plans:
        description = f"\n   📝 {plan.description}" if plan.description else ""
        details.append(
            f"📦 {plan.name}\n"
            f"   💰 {plan.price:,} تومان | 📅 {plan.duration} ماه | 📶 {plan.traffic}"
            f"{description}"
        )
    return "\n\n".join(details)


@router.message(F.text == "🛒 خرید VPN")
async def buy_vpn(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Plan).where(Plan.is_active.is_(True))
        )

        plans = result.scalars().all()

    if not plans:
        await message.answer(
            "در حال حاضر هیچ پلنی فعال نیست."
        )
        return

    keyboard = await create_plans_keyboard(plans)

    await message.answer(
        f"🛒 پلن موردنظر خود را انتخاب کنید:\n\n{plans_summary(plans)}",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("plan_"))
async def select_plan(callback: CallbackQuery, state: FSMContext):

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
    await state.update_data(order_id=order.id)
    await state.set_state(PaymentState.waiting_for_receipt)

    card_details = ""
    if settings.payment_card:
        card_details = (
            f"💳 شماره کارت: <code>{settings.payment_card}</code>\n"
            f"👤 به نام: {settings.card_owner or '—'}\n\n"
        )
    else:
        card_details = "⚠️ اطلاعات کارت پرداخت هنوز تنظیم نشده است.\n\n"

    await callback.message.answer(
        f"✅ سفارش شما ثبت شد.\n\n"
        f"🆔 شماره سفارش: #{order.id}\n"
        f"📦 پلن: {order.plan.name}\n"
        f"💰 مبلغ قابل پرداخت: {order.price:,} تومان\n\n"
        f"{card_details}"
        f"پس از پرداخت، تصویر رسید را ارسال کنید.",
        parse_mode="HTML"
    )
