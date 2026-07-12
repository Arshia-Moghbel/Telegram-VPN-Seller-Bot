from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from config import settings
from database.models import Order, Plan
from db import async_session
from keyboards.admin import (
    admin_panel_keyboard,
    back_to_admin_keyboard,
    orders_keyboard,
    plan_details_keyboard,
    plan_list_keyboard,
    plans_management_keyboard,
    payment_settings_keyboard,
    receipt_review_keyboard,
    user_details_keyboard,
    users_keyboard,
)
from models.order_status import OrderStatus
from services.admin_service import (
    find_users,
    get_broadcast_recipient_ids,
    get_dashboard_stats,
    get_order,
    get_payment_settings,
    get_recent_orders,
    get_user,
    get_user_orders,
    save_payment_setting,
    set_user_blocked,
)
from states.admin import AdminState
from states.fulfillment import FulfillmentState
from states.plan import PlanState

router = Router()

PAYMENT_SETTING_LABELS = {
    "payment_card": "شماره کارت",
    "card_owner": "نام صاحب حساب",
    "payment_bank": "بانک",
    "payment_reference": "شناسه پرداخت",
    "support_username": "پشتیبانی",
}


def is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id


def plan_text(plan: Plan) -> str:
    status = "فعال" if plan.is_active else "غیرفعال"
    return (
        f"📦 {plan.name}\n\n"
        f"💰 قیمت: {plan.price:,} تومان\n"
        f"📅 مدت: {plan.duration} ماه\n"
        f"📶 حجم: {plan.traffic}\n"
        f"📝 توضیحات: {plan.description or '—'}\n"
        f"⚙️ وضعیت: {status}"
    )


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی به این بخش را ندارید.")
        return

    await message.answer(
        "🛠 پنل مدیریت",
        reply_markup=admin_panel_keyboard(),
    )


@router.callback_query(F.data == "admin_home")
async def show_admin_home(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    await callback.message.edit_text("🛠 پنل مدیریت", reply_markup=admin_panel_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_plans")
async def open_plans_management(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    await callback.message.edit_text(
        "📦 مدیریت پلن‌ها",
        reply_markup=plans_management_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.in_({"admin_payment", "admin_settings"}))
async def show_payment_settings(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    payment_settings = await get_payment_settings()
    await callback.message.edit_text(
        "💳 تنظیمات پرداخت\n\n"
        f"شماره کارت: {payment_settings['payment_card'] or '—'}\n"
        f"نام صاحب حساب: {payment_settings['card_owner'] or '—'}\n"
        f"بانک: {payment_settings['payment_bank'] or '—'}\n"
        f"شناسه پرداخت: {payment_settings['payment_reference'] or '—'}\n"
        f"پشتیبانی: {payment_settings['support_username'] or '—'}",
        reply_markup=payment_settings_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_setting_"))
async def edit_payment_setting(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    key = callback.data.removeprefix("admin_setting_")
    label = PAYMENT_SETTING_LABELS.get(key)
    if label is None:
        await callback.answer("تنظیمات نامعتبر است.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_setting_value)
    await state.update_data(setting_key=key)
    await callback.message.answer(f"مقدار جدید «{label}» را ارسال کنید:")
    await callback.answer()


@router.message(AdminState.waiting_for_setting_value, F.text)
async def save_payment_setting_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    key = data.get("setting_key")
    value = message.text.strip()
    if not key or not value:
        await message.answer("مقدار نامعتبر است. دوباره تلاش کنید.")
        return

    await save_payment_setting(key, value)
    await state.clear()
    await message.answer("✅ تنظیمات ذخیره شد.", reply_markup=back_to_admin_keyboard())


@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    stats = await get_dashboard_stats()
    await callback.message.edit_text(
        "📊 آمار\n\n"
        f"👥 تعداد کاربران: {stats['total_users']:,}\n"
        f"📑 سفارش‌های امروز: {stats['today_orders']:,}\n"
        f"💰 فروش امروز: {stats['today_sales']:,} تومان\n"
        f"💵 کل فروش: {stats['total_sales']:,} تومان\n"
        f"⏳ پرداخت‌های معلق: {stats['pending_payments']:,}",
        reply_markup=back_to_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
async def show_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    orders = await get_recent_orders()
    if not orders:
        await callback.message.edit_text("📑 هنوز سفارشی ثبت نشده است.", reply_markup=back_to_admin_keyboard())
    else:
        await callback.message.edit_text("📑 آخرین سفارش‌ها:", reply_markup=orders_keyboard(orders))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_"))
async def show_order_details(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    order_id = int(callback.data.removeprefix("admin_order_"))
    order = await get_order(order_id)
    if order is None:
        await callback.answer("سفارش پیدا نشد.", show_alert=True)
        return

    username = f"@{order.user.username}" if order.user.username else "—"
    await callback.message.edit_text(
        f"📑 سفارش #{order.id}\n\n"
        f"👤 کاربر: {order.user.telegram_id} ({username})\n"
        f"📦 پلن: {order.plan.name}\n"
        f"💰 مبلغ: {order.price:,} تومان\n"
        f"⚙️ وضعیت: {order.status}\n"
        f"📅 زمان: {order.created_at:%Y-%m-%d %H:%M}",
        reply_markup=back_to_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def request_user_search(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_user_query)
    await callback.message.answer("شناسه تلگرام یا نام کاربری کاربر را ارسال کنید:")
    await callback.answer()


@router.message(AdminState.waiting_for_user_query, F.text)
async def search_users(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    users = await find_users(message.text)
    await state.clear()
    if not users:
        await message.answer("کاربری پیدا نشد.", reply_markup=back_to_admin_keyboard())
        return
    await message.answer("👥 نتیجهٔ جستجو:", reply_markup=users_keyboard(users))


@router.callback_query(F.data.startswith("admin_user_orders_"))
async def show_user_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    user_id = int(callback.data.removeprefix("admin_user_orders_"))
    orders = await get_user_orders(user_id)
    if not orders:
        await callback.message.edit_text("🧾 این کاربر هنوز سفارشی ندارد.", reply_markup=back_to_admin_keyboard())
    else:
        await callback.message.edit_text("🧾 سوابق خرید کاربر:", reply_markup=orders_keyboard(orders))
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_user_(block|unblock)_\\d+$"))
async def change_user_block_status(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    _, _, action, user_id = callback.data.split("_", maxsplit=3)
    user = await set_user_blocked(int(user_id), action == "block")
    if user is None:
        await callback.answer("کاربر پیدا نشد.", show_alert=True)
        return
    await callback.message.edit_text(
        f"✅ وضعیت کاربر {user.telegram_id} به‌روزرسانی شد.",
        reply_markup=user_details_keyboard(user.id, user.is_blocked),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^admin_user_\\d+$"))
async def show_user_details(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    user_id = int(callback.data.removeprefix("admin_user_"))
    user = await get_user(user_id)
    if user is None:
        await callback.answer("کاربر پیدا نشد.", show_alert=True)
        return

    username = f"@{user.username}" if user.username else "—"
    status = "مسدود" if user.is_blocked else "فعال"
    await callback.message.edit_text(
        f"👤 کاربر\n\n"
        f"شناسه تلگرام: {user.telegram_id}\n"
        f"نام کاربری: {username}\n"
        f"وضعیت: {status}\n"
        f"عضویت: {user.created_at:%Y-%m-%d %H:%M}",
        reply_markup=user_details_keyboard(user.id, user.is_blocked),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def request_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    await state.set_state(AdminState.waiting_for_broadcast)
    await callback.message.answer("متن پیام همگانی را ارسال کنید:")
    await callback.answer()


@router.message(AdminState.waiting_for_broadcast, F.text)
async def send_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    recipient_ids = await get_broadcast_recipient_ids()
    sent_count = 0
    for recipient_id in recipient_ids:
        try:
            await bot.send_message(recipient_id, message.text)
            sent_count += 1
        except TelegramAPIError:
            continue

    await state.clear()
    await message.answer(
        f"✅ پیام همگانی برای {sent_count:,} کاربر ارسال شد.",
        reply_markup=back_to_admin_keyboard(),
    )


@router.callback_query(F.data == "plan_list")
async def list_plans(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    async with async_session() as session:
        plans = (await session.execute(select(Plan).order_by(Plan.id))).scalars().all()

    await callback.message.edit_text(
        "📋 یکی از پلن‌ها را انتخاب کنید:",
        reply_markup=plan_list_keyboard(plans),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("plan_open_"))
async def open_plan(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    plan_id = int(callback.data.removeprefix("plan_open_"))
    async with async_session() as session:
        plan = await session.get(Plan, plan_id)

    if plan is None:
        await callback.answer("پلن پیدا نشد.", show_alert=True)
        return

    await callback.message.edit_text(
        plan_text(plan), reply_markup=plan_details_keyboard(plan.id, plan.is_active)
    )
    await callback.answer()


@router.callback_query(F.data == "plan_add")
async def add_plan(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    await state.clear()
    await state.set_state(PlanState.creating_name)
    await callback.message.answer("نام پلن جدید را بفرستید:")
    await callback.answer()


@router.message(PlanState.creating_name, F.text)
async def create_plan_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(PlanState.creating_price)
    await message.answer("قیمت پلن را فقط به تومان و با رقم وارد کنید (مثلاً 150000):")


@router.message(PlanState.creating_price, F.text)
async def create_plan_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        price = int(message.text.replace(",", "").strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("قیمت باید یک عدد مثبت باشد.")
        return
    await state.update_data(price=price)
    await state.set_state(PlanState.creating_duration)
    await message.answer("مدت اشتراک را به ماه وارد کنید:")


@router.message(PlanState.creating_duration, F.text)
async def create_plan_duration(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer("مدت باید یک عدد مثبت باشد.")
        return
    await state.update_data(duration=duration)
    await state.set_state(PlanState.creating_traffic)
    await message.answer("حجم را وارد کنید (مثلاً 100GB یا نامحدود):")


@router.message(PlanState.creating_traffic, F.text)
async def create_plan_traffic(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(traffic=message.text.strip())
    await state.set_state(PlanState.creating_description)
    await message.answer("توضیح کوتاه پلن را بفرستید، یا «-» برای نداشتن توضیح:")


@router.message(PlanState.creating_description, F.text)
async def create_plan_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    description = message.text.strip()
    async with async_session() as session:
        plan = Plan(**data, description=None if description == "-" else description)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
    await state.clear()
    await message.answer(
        f"✅ پلن جدید اضافه شد.\n\n{plan_text(plan)}",
        reply_markup=plan_details_keyboard(plan.id, plan.is_active),
    )


@router.callback_query(F.data.startswith("plan_edit_"))
async def edit_plan(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    _, _, plan_id, field = callback.data.split("_", maxsplit=3)
    await state.set_state(PlanState.editing_field)
    await state.update_data(plan_id=int(plan_id), field=field)
    labels = {
        "name": "نام",
        "price": "قیمت",
        "duration": "مدت به ماه",
        "traffic": "حجم",
        "description": "توضیحات",
    }
    await callback.message.answer(f"مقدار جدید «{labels[field]}» را بفرستید:")
    await callback.answer()


@router.message(PlanState.editing_field, F.text)
async def save_plan_edit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    field = data["field"]
    value = message.text.strip()
    try:
        if field in {"price", "duration"}:
            value = int(value.replace(",", ""))
            if value <= 0:
                raise ValueError
    except ValueError:
        await message.answer("یک عدد مثبت وارد کنید.")
        return

    if field == "description" and value == "-":
        value = None
    async with async_session() as session:
        plan = await session.get(Plan, data["plan_id"])
        if plan is None:
            await message.answer("پلن پیدا نشد.")
            await state.clear()
            return
        setattr(plan, field, value)
        await session.commit()
        await session.refresh(plan)
    await state.clear()
    await message.answer(
        f"✅ پلن ویرایش شد.\n\n{plan_text(plan)}",
        reply_markup=plan_details_keyboard(plan.id, plan.is_active),
    )


@router.callback_query(F.data.startswith("plan_toggle_"))
async def toggle_plan(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    plan_id = int(callback.data.removeprefix("plan_toggle_"))
    async with async_session() as session:
        plan = await session.get(Plan, plan_id)
        if plan is None:
            await callback.answer("پلن پیدا نشد.", show_alert=True)
            return
        plan.is_active = not plan.is_active
        await session.commit()
        await session.refresh(plan)
    await callback.message.edit_text(
        plan_text(plan), reply_markup=plan_details_keyboard(plan.id, plan.is_active)
    )
    await callback.answer("وضعیت پلن تغییر کرد.")


@router.callback_query(F.data.startswith("plan_delete_"))
async def delete_plan(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    plan_id = int(callback.data.removeprefix("plan_delete_"))
    async with async_session() as session:
        plan = await session.get(Plan, plan_id)
        if plan is None:
            await callback.answer("پلن پیدا نشد.", show_alert=True)
            return
        has_orders = (
            await session.execute(select(Order.id).where(Order.plan_id == plan_id).limit(1))
        ).scalar_one_or_none()
        if has_orders is not None:
            plan.is_active = False
            await session.commit()
            await callback.message.edit_text(
                "این پلن سفارش دارد؛ برای حفظ تاریخچه، به‌جای حذف غیرفعال شد.",
                reply_markup=plans_management_keyboard(),
            )
            await callback.answer()
            return
        await session.delete(plan)
        await session.commit()
    await callback.message.edit_text("✅ پلن حذف شد.", reply_markup=plans_management_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("approve_order_"))
async def approve_order(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        order = (await session.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
        if order is None:
            await callback.answer("Order not found.", show_alert=True)
            return
        order.status = OrderStatus.PAID.value
        await session.commit()

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ پرداخت تایید شد.")
    await state.set_state(FulfillmentState.waiting_for_config)
    await state.update_data(order_id=order.id)
    await callback.message.answer(
        f"پرداخت سفارش #{order.id} تایید شد.\n\n"
        "حالا کانفیگ VPN این کاربر را به‌صورت متن ارسال کنید تا برای او فرستاده شود."
    )
    await callback.answer("حالا کانفیگ را ارسال کنید.")


@router.message(FulfillmentState.waiting_for_config, F.text)
async def send_config_to_user(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    if order_id is None:
        await state.clear()
        await message.answer("سفارش پیدا نشد. دوباره تلاش کنید.")
        return

    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await state.clear()
            await message.answer("سفارش پیدا نشد.")
            return
        await session.refresh(order, attribute_names=["user"])
        order.status = OrderStatus.COMPLETED.value
        await session.commit()
        user_id = order.user.telegram_id

    await bot.send_message(
        chat_id=user_id,
        text=(
            "✅ پرداخت شما تایید شد.\n\n"
            "🔐 کانفیگ VPN شما:\n"
            f"<code>{escape(message.text)}</code>\n\n"
            "برای راهنمای اتصال، با پشتیبانی در تماس باشید."
        ),
        parse_mode="HTML",
    )
    await state.clear()
    await message.answer(f"✅ کانفیگ برای کاربر سفارش #{order_id} ارسال شد.")


@router.message(FulfillmentState.waiting_for_config)
async def invalid_config(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("کانفیگ را به‌صورت پیام متنی ارسال کنید.")


@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])
    async with async_session() as session:
        order = (await session.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
        if order is None:
            await callback.answer("Order not found.", show_alert=True)
            return
        await session.refresh(order, attribute_names=["user"])
        order.status = OrderStatus.CANCELED.value
        await session.commit()

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ پرداخت رد شد.")
    await bot.send_message(order.user.telegram_id, "❌ پرداخت تایید نشد. لطفاً با پشتیبانی تماس بگیرید.")
    await callback.answer("سفارش رد شد.")
