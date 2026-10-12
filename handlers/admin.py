from aiogram.dispatcher.event.bases import SkipHandler
from html import escape
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from config import settings
from database.models import Order, Plan
from db import async_session
from keyboards.admin import (
    admin_panel_keyboard,
    back_to_admin_keyboard,
    button_settings_keyboard,
    cancel_admin_keyboard,
    content_settings_keyboard,
    coupons_keyboard,
    confirm_plan_deletion_keyboard,
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
    get_active_fulfillment_order_id,
    get_order,
    get_payment_settings,
    get_recent_orders,
    get_user,
    get_user_orders,
    get_users,
    get_ui_labels,
    save_payment_setting,
    set_active_fulfillment_order_id,
    set_user_blocked,
)
from services.plan_duration import format_duration, parse_duration
from services.coupon_service import create_coupon, get_coupons, normalize_coupon_code, toggle_coupon
from filters.admin import AdminFilter
from states.admin import AdminState
from states.coupon import CouponState
from states.fulfillment import FulfillmentState
from states.plan import PlanState

router = Router()
logger = logging.getLogger(__name__)

PAYMENT_SETTING_LABELS = {
    "payment_card": "شماره کارت",
    "card_owner": "نام صاحب حساب",
    "payment_bank": "بانک",
    "payment_reference": "شناسه پرداخت",
    "support_username": "پشتیبانی",
    "content_servers": "متن سرورها",
    "content_guide_android": "آموزش اندروید",
    "content_guide_ios": "آموزش iPhone/iPad",
    "content_guide_windows": "آموزش ویندوز",
    "content_guide_macos": "آموزش مک",
    "ui_public_buy": "دکمهٔ خرید",
    "ui_public_servers": "دکمهٔ سرورها",
    "ui_public_guides": "دکمهٔ آموزش اتصال",
    "ui_public_support": "دکمهٔ پشتیبانی",
    "ui_admin_plans": "دکمهٔ مدیریت پلن‌ها",
    "ui_admin_payment": "دکمهٔ تنظیمات پرداخت",
    "ui_admin_content": "دکمهٔ متن‌های ربات",
    "ui_admin_orders": "دکمهٔ سفارش‌ها",
    "ui_admin_users": "دکمهٔ کاربران",
    "ui_admin_stats": "دکمهٔ آمار",
    "ui_admin_broadcast": "دکمهٔ ارسال همگانی",
    "ui_admin_coupons": "دکمهٔ کدهای تخفیف",
    "ui_admin_buttons": "دکمهٔ تنظیم دکمه‌ها",
}


def is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id


def plan_text(plan: Plan) -> str:
    status = "فعال" if plan.is_active else "غیرفعال"
    return (
        f"📦 {plan.name}\n\n"
        f"💰 قیمت: {plan.price:,} تومان\n"
        f"📅 مدت: {format_duration(plan.duration, plan.duration_unit)}\n"
        f"📶 حجم: {plan.traffic}\n"
        f"📝 توضیحات: {plan.description or '—'}\n"
        f"⚙️ وضعیت: {status}"
    )


@router.message(AdminFilter(), StateFilter("*"), F.text.casefold() == "cancel")
async def cancel_admin_flow(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ عملیات لغو شد.", reply_markup=back_to_admin_keyboard())


@router.callback_query(F.data == "admin_cancel_flow")
async def cancel_admin_flow_button(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "🛠 پنل مدیریت", reply_markup=admin_panel_keyboard(await get_ui_labels())
    )
    await callback.answer("عملیات لغو شد.")


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ شما دسترسی به این بخش را ندارید.")
        return

    await message.answer(
        "🛠 پنل مدیریت",
        reply_markup=admin_panel_keyboard(await get_ui_labels()),
    )


@router.callback_query(F.data == "admin_home")
async def show_admin_home(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    await callback.message.edit_text(
        "🛠 پنل مدیریت", reply_markup=admin_panel_keyboard(await get_ui_labels())
    )
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


@router.callback_query(F.data == "admin_payment")
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


@router.callback_query(F.data == "admin_buttons")
async def show_button_settings(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    labels = await get_ui_labels()
    await callback.message.edit_text(
        "🔘 تنظیم دکمه‌ها\n\nهر دکمه را انتخاب کنید و متن جدید شامل ایموجی را بفرستید. "
        "کاربران با /start منوی جدید را دریافت می‌کنند.",
        reply_markup=button_settings_keyboard(labels),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_coupons")
async def show_coupons(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    coupons = await get_coupons()
    await callback.message.edit_text(
        "🎟 کدهای تخفیف\n\nبرای غیرفعال/فعال‌کردن یک کد، روی آن بزنید.",
        reply_markup=coupons_keyboard(coupons),
    )
    await callback.answer()


@router.callback_query(F.data == "coupon_add")
async def add_coupon(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    await state.set_state(CouponState.creating_code)
    await callback.message.answer("کد تخفیف را وارد کنید (مثلاً WELCOME10)، یا «cancel» برای انصراف.")
    await callback.answer()


@router.message(CouponState.creating_code, F.text)
async def coupon_code(message: Message, state: FSMContext):
    code = normalize_coupon_code(message.text)
    if not code or len(code) > 50 or not code.replace("_", "").isalnum():
        await message.answer("کد فقط می‌تواند شامل حروف، عدد و _ باشد.")
        return
    await state.update_data(coupon_code=code)
    await state.set_state(CouponState.creating_type)
    await message.answer("نوع تخفیف را وارد کنید: «درصد» یا «تومان».")


@router.message(CouponState.creating_type, F.text)
async def coupon_type(message: Message, state: FSMContext):
    value = message.text.strip().casefold()
    if value in {"درصد", "percent", "%"}:
        discount_type = "percent"
    elif value in {"تومان", "fixed"}:
        discount_type = "fixed"
    else:
        await message.answer("فقط «درصد» یا «تومان» وارد کنید.")
        return
    await state.update_data(coupon_type=discount_type)
    await state.set_state(CouponState.creating_value)
    await message.answer("مقدار تخفیف را وارد کنید:")


@router.message(CouponState.creating_value, F.text)
async def coupon_value(message: Message, state: FSMContext):
    try:
        value = int(message.text.replace(",", "").strip())
        coupon_type = (await state.get_data())["coupon_type"]
        if value <= 0 or (coupon_type == "percent" and value > 100):
            raise ValueError
    except ValueError:
        await message.answer("مقدار نامعتبر است؛ درصد باید بین ۱ تا ۱۰۰ باشد.")
        return
    await state.update_data(coupon_value=value)
    await state.set_state(CouponState.creating_limit)
    await message.answer("حداکثر دفعات استفاده را وارد کنید، یا «نامحدود» بنویسید:")


@router.message(CouponState.creating_limit, F.text)
async def coupon_limit(message: Message, state: FSMContext):
    raw_value = message.text.strip().casefold()
    try:
        limit = None if raw_value in {"نامحدود", "unlimited", "-"} else int(raw_value)
        if limit is not None and limit <= 0:
            raise ValueError
    except ValueError:
        await message.answer("یک عدد مثبت یا «نامحدود» وارد کنید.")
        return
    data = await state.get_data()
    try:
        coupon = await create_coupon(data["coupon_code"], data["coupon_type"], data["coupon_value"], limit)
    except Exception:
        logger.exception("Could not create coupon")
        await message.answer("این کد قبلاً وجود دارد یا ذخیره‌سازی ناموفق بود.")
        return
    await state.clear()
    await message.answer(f"✅ کد تخفیف «{coupon.code}» ساخته شد.", reply_markup=back_to_admin_keyboard())


@router.callback_query(F.data.regexp(r"^coupon_toggle_\d+$"))
async def change_coupon_status(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    coupon = await toggle_coupon(int(callback.data.rsplit("_", 1)[1]))
    if coupon is None:
        await callback.answer("کد پیدا نشد.", show_alert=True)
        return
    coupons = await get_coupons()
    await callback.message.edit_text("🎟 کدهای تخفیف", reply_markup=coupons_keyboard(coupons))
    await callback.answer("وضعیت کد تغییر کرد.")


@router.callback_query(F.data == "admin_content")
async def show_content_settings(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return
    await callback.message.edit_text(
        "📝 متن‌های ربات\n\nمتن سرورها یا راهنمای هر دستگاه را انتخاب و ویرایش کنید. "
        "تغییرات در دیتابیس ذخیره می‌شوند و پس از ری‌استارت باقی می‌مانند.",
        reply_markup=content_settings_keyboard(),
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
    await callback.message.answer(
        f"مقدار جدید «{label}» را ارسال کنید (حداکثر ۵۰۰ کاراکتر):",
        reply_markup=cancel_admin_keyboard(),
    )
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
    if len(value) > 500:
        await message.answer("متن نباید بیشتر از ۵۰۰ کاراکتر باشد.")
        return

    if not await save_payment_setting(key, value):
        await message.answer("تنظیمات نامعتبر است.")
        await state.clear()
        return
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
async def show_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    users = await get_users()
    if not users:
        await callback.message.edit_text(
            "👥 هنوز کاربری ثبت نشده است.",
            reply_markup=back_to_admin_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "👥 کاربران اخیر:\n\nبرای مشاهدهٔ جزئیات، یک کاربر را انتخاب کنید.",
        reply_markup=users_keyboard(users),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users_search")
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


@router.callback_query(F.data.regexp(r"^admin_user_(block|unblock)_\d+$"))
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


@router.callback_query(F.data.regexp(r"^admin_user_\d+$"))
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
            logger.warning("Broadcast delivery failed for Telegram user %s", recipient_id)
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
        plans = (
            await session.execute(
                select(Plan).where(Plan.is_deleted.is_(False)).order_by(Plan.id)
            )
        ).scalars().all()

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
    await message.answer(
        "مدت اشتراک را وارد کنید؛ مثلاً «1 ماه»، «0.01 ماه» یا «24 ساعت».\n"
        "اگر فقط عدد بفرستید، واحد آن ماه در نظر گرفته می‌شود."
    )


@router.message(PlanState.creating_duration, F.text)
async def create_plan_duration(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        duration, duration_unit = parse_duration(message.text)
    except ValueError:
        await message.answer("مدت نامعتبر است. نمونهٔ درست: «0.01 ماه» یا «24 ساعت».")
        return
    await state.update_data(duration=duration, duration_unit=duration_unit)
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
        "duration": "مدت",
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
        if field == "price":
            value = int(value.replace(",", ""))
            if value <= 0:
                raise ValueError
        elif field == "duration":
            value, duration_unit = parse_duration(value)
    except ValueError:
        await message.answer("یک مقدار مثبت وارد کنید. برای مدت: «0.01 ماه» یا «24 ساعت».")
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
        if field == "duration":
            plan.duration_unit = duration_unit
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


@router.callback_query(F.data.regexp(r"^plan_delete_\d+$"))
async def request_plan_deletion(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    plan_id = int(callback.data.removeprefix("plan_delete_"))
    async with async_session() as session:
        plan = await session.get(Plan, plan_id)
        if plan is None or plan.is_deleted:
            await callback.answer("پلن پیدا نشد.", show_alert=True)
            return
        has_orders = (
            await session.execute(select(Order.id).where(Order.plan_id == plan_id).limit(1))
        ).scalar_one_or_none()

    history_note = (
        "این پلن سفارش‌های قبلی دارد. پس از حذف، جزئیات سفارش‌ها و تاریخچه حفظ می‌شوند."
        if has_orders is not None
        else "این پلن هنوز سفارشی ندارد."
    )
    await callback.message.edit_text(
        f"🗑 حذف پلن\n\n{plan_text(plan)}\n\n{history_note}\n\n"
        "پس از تأیید، پلن دیگر برای خرید یا مدیریت نمایش داده نمی‌شود.",
        reply_markup=confirm_plan_deletion_keyboard(plan.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("plan_delete_confirm_"))
async def confirm_plan_deletion(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("دسترسی ندارید.", show_alert=True)
        return

    plan_id = int(callback.data.removeprefix("plan_delete_confirm_"))
    async with async_session() as session:
        plan = await session.get(Plan, plan_id)
        if plan is None or plan.is_deleted:
            await callback.answer("پلن پیدا نشد یا قبلاً حذف شده است.", show_alert=True)
            return
        plan.is_active = False
        plan.is_deleted = True
        await session.commit()

    await callback.message.edit_text(
        "✅ پلن حذف شد و دیگر برای خرید نمایش داده نمی‌شود.\n\n"
        "اطلاعات آن در سفارش‌ها و تاریخچهٔ قبلی محفوظ است.",
        reply_markup=plans_management_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r"^approve_order_\d+$"))
async def approve_order(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])
    active_order_id = await get_active_fulfillment_order_id()
    if active_order_id is not None:
        active_order = await get_order(active_order_id)
        if active_order is not None and active_order.status == OrderStatus.PAID.value:
            await callback.answer(
                f"ابتدا کانفیگ سفارش #{active_order_id} را ارسال کنید.", show_alert=True
            )
            return
        await set_active_fulfillment_order_id(None)

    async with async_session() as session:
        order = (await session.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
        if order is None:
            await callback.answer("Order not found.", show_alert=True)
            return
        if order.status != OrderStatus.WAITING_REVIEW.value:
            await callback.answer("این سفارش قبلاً بررسی شده است.", show_alert=True)
            return
        order.status = OrderStatus.PAID.value
        await session.commit()

    await set_active_fulfillment_order_id(order.id)
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n✅ پرداخت تایید شد.",
        reply_markup=None,
    )
    await state.set_state(FulfillmentState.waiting_for_config)
    await state.update_data(order_id=order.id)
    await callback.message.answer(
        f"پرداخت سفارش #{order.id} تایید شد.\n\n"
        "حالا کانفیگ VPN این کاربر را به‌صورت متن ارسال کنید تا برای او فرستاده شود."
    )
    await callback.answer("حالا کانفیگ را ارسال کنید.")


async def deliver_config(message: Message, bot: Bot, order_id: int) -> bool:
    """Send first, then mark complete, so a failed Telegram call is retryable."""
    if order_id is None:
        return False

    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None:
            await message.answer("سفارش پیدا نشد.")
            return False
        if order.status != OrderStatus.PAID.value:
            await message.answer("این سفارش در وضعیت آمادهٔ ارسال کانفیگ نیست.")
            return False
        await session.refresh(order, attribute_names=["user"])
        user_id = order.user.telegram_id

    try:
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
    except TelegramAPIError:
        await message.answer("❌ ارسال کانفیگ ناموفق بود؛ لطفاً دوباره تلاش کنید.")
        return False

    async with async_session() as session:
        order = await session.get(Order, order_id)
        if order is None or order.status != OrderStatus.PAID.value:
            await message.answer("وضعیت سفارش هنگام ثبت نهایی تغییر کرد. آن را بررسی کنید.")
            return False
        order.status = OrderStatus.COMPLETED.value
        await session.commit()
    await set_active_fulfillment_order_id(None)
    await message.answer(f"✅ کانفیگ برای کاربر سفارش #{order_id} ارسال شد.")
    return True


@router.message(FulfillmentState.waiting_for_config, F.text)
async def send_config_to_user(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    order_id = (await state.get_data()).get("order_id")
    if order_id is None:
        order_id = await get_active_fulfillment_order_id()
    if order_id is None:
        await state.clear()
        await message.answer("سفارش آمادهٔ ارسال کانفیگ پیدا نشد.")
        return
    if await deliver_config(message, bot, order_id):
        await state.clear()


@router.message(FulfillmentState.waiting_for_config)
async def invalid_config(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("کانفیگ را به‌صورت پیام متنی ارسال کنید.")


@router.message(F.text, ~F.text.startswith("/"))
async def resume_config_delivery(message: Message, bot: Bot):
    """Resume config delivery after a restart, without blocking public handlers."""
    if not is_admin(message.from_user.id):
        raise SkipHandler

    order_id = await get_active_fulfillment_order_id()

    if order_id is None:
        raise SkipHandler

    await deliver_config(message, bot, order_id)


@router.callback_query(F.data.regexp(r"^reject_order_\d+$"))
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
        if order.status != OrderStatus.WAITING_REVIEW.value:
            await callback.answer("این سفارش قبلاً بررسی شده است.", show_alert=True)
            return
        await session.refresh(order, attribute_names=["user"])
        order.status = OrderStatus.CANCELED.value
        await session.commit()

    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n❌ پرداخت رد شد.",
        reply_markup=None,
    )
    await bot.send_message(order.user.telegram_id, "❌ پرداخت تایید نشد. لطفاً با پشتیبانی تماس بگیرید.")
    await callback.answer("سفارش رد شد.")
