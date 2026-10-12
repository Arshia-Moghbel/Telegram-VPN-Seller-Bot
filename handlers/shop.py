from html import escape

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from db import async_session
from database.models import Plan, User
from filters.button_text import ButtonTextFilter
from keyboards.shop import create_plans_keyboard
from services.order_service import create_order
from services.plan_duration import format_duration
from services.admin_service import get_payment_settings
from services.coupon_service import get_coupon, normalize_coupon_code
from states.coupon import CouponState
from states.payment import PaymentState

router = Router()


def plans_summary(plans: list[Plan]) -> str:
    details = []
    for plan in plans:
        description = f"\n   📝 {plan.description}" if plan.description else ""
        details.append(
            f"📦 {plan.name}\n"
            f"   💰 {plan.price:,} تومان | 📅 {format_duration(plan.duration, plan.duration_unit)} | 📶 {plan.traffic}"
            f"{description}"
        )
    return "\n\n".join(details)


async def show_available_plans(message: Message, state: FSMContext | None = None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if user is not None and user.is_blocked:
            await message.answer("⛔ حساب شما مسدود شده است. برای پیگیری با پشتیبانی تماس بگیرید.")
            return

        result = await session.execute(
            select(Plan).where(Plan.is_active.is_(True), Plan.is_deleted.is_(False))
        )

        plans = result.scalars().all()

    if not plans:
        await message.answer(
            "در حال حاضر هیچ پلنی فعال نیست."
        )
        return

    coupon_code = (await state.get_data()).get("coupon_code") if state else None
    coupon_note = ""
    if coupon_code:
        coupon = await get_coupon(coupon_code)
        if coupon is not None:
            coupon_note = f"\n\n🎟 کد تخفیف فعال: {coupon.code}"
        else:
            coupon_note = "\n\n⚠️ کد تخفیف دیگر معتبر نیست."
            if state:
                await state.update_data(coupon_code=None)
    keyboard = await create_plans_keyboard(plans)

    await message.answer(
        f"🛒 پلن موردنظر خود را انتخاب کنید:\n\n{plans_summary(plans)}{coupon_note}",
        reply_markup=keyboard
    )


@router.message(ButtonTextFilter("ui_public_buy"))
async def buy_vpn(message: Message, state: FSMContext):
    await state.clear()
    await show_available_plans(message, state)


@router.callback_query(F.data == "coupon_enter")
async def request_coupon(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CouponState.waiting_for_code)
    await callback.message.answer("کد تخفیف را بفرستید، یا «cancel» برای انصراف.")
    await callback.answer()


@router.message(CouponState.waiting_for_code, F.text.casefold() == "cancel")
async def cancel_coupon(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ واردکردن کد تخفیف لغو شد.")


@router.message(CouponState.waiting_for_code, F.text)
async def apply_coupon(message: Message, state: FSMContext):
    code = normalize_coupon_code(message.text)
    coupon = await get_coupon(code)
    if coupon is None:
        await message.answer("❌ کد تخفیف معتبر نیست یا ظرفیت آن تمام شده است.")
        return
    await state.update_data(coupon_code=code)
    await state.set_state(None)
    await message.answer(f"✅ کد «{code}» اعمال شد.")
    await show_available_plans(message, state)


@router.callback_query(F.data.regexp(r"^plan_\d+$"))
async def select_plan(callback: CallbackQuery, state: FSMContext):

    await callback.answer()

    plan_id = int(callback.data.split("_")[1])

    payment_settings = await get_payment_settings()
    if not payment_settings["payment_card"].strip():
        await callback.message.answer(
            "⚠️ پرداخت آنلاین فعلاً آماده نیست. لطفاً بعداً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
        return

    order = await create_order(
        telegram_id=callback.from_user.id,
        plan_id=plan_id,
        coupon_code=(await state.get_data()).get("coupon_code"),
    )

    if order is None:
        await callback.message.answer(
            "❌ خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید."
        )
        return
    await state.update_data(order_id=order.id, coupon_code=None)
    await state.set_state(PaymentState.waiting_for_receipt)

    card_details = ""
    if payment_settings["payment_card"]:
        bank = f"🏦 بانک: {payment_settings['payment_bank']}\n" if payment_settings["payment_bank"] else ""
        reference = (
            f"🔖 شناسه پرداخت: {payment_settings['payment_reference']}\n"
            if payment_settings["payment_reference"]
            else ""
        )
        card_details = (
            f"💳 شماره کارت: <code>{escape(payment_settings['payment_card'])}</code>\n"
            f"👤 به نام: {escape(payment_settings['card_owner']) or '—'}\n"
            f"{bank}{reference}\n"
        )
    else:
        card_details = "⚠️ اطلاعات کارت پرداخت هنوز تنظیم نشده است.\n\n"

    await callback.message.answer(
        f"✅ سفارش شما ثبت شد.\n\n"
        f"🆔 شماره سفارش: #{order.id}\n"
        f"📦 پلن: {order.plan.name}\n"
        f"💰 مبلغ قابل پرداخت: {order.price:,} تومان\n"
        f"🎟 تخفیف: {order.discount_amount:,} تومان\n\n"
        f"{card_details}"
        f"پس از پرداخت، تصویر رسید را ارسال کنید.",
        parse_mode="HTML"
    )
