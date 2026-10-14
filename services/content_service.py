import re

from database.models import Plan
from db import async_session
from sqlalchemy import select
from services.plan_duration import format_duration


CONTENT_DEFAULTS = {
    "content_welcome": (
        "سلام 👋\n\n"
        "به VPNifi خوش آمدی.\n\n"
        "از منوی زیر یک گزینه را انتخاب کن:"
    ),
    "content_blocked": "⛔ حساب شما مسدود شده است. برای پیگیری با پشتیبانی تماس بگیرید.",
    "content_servers": (
        "🌍 سرورها\n\n"
        "🇩🇪 آلمان — اتصال پایدار برای استفاده روزمره\n"
        "🇫🇮 فنلاند — مناسب وب‌گردی و پیام‌رسان‌ها\n"
        "🇹🇷 ترکیه — گزینه‌ای نزدیک‌تر برای تأخیر کمتر\n\n"
        "انتخاب سرور پس از دریافت کانفیگ امکان‌پذیر است. "
        "برای وضعیت لحظه‌ای یا پیشنهاد مناسب، با پشتیبانی تماس بگیرید."
    ),
    "content_guide_android": (
        "🤖 آموزش اتصال در اندروید\n\n"
        "1. اپلیکیشن پیشنهادی سرویس را از فروشگاه معتبر نصب کنید.\n"
        "2. کانفیگ یا لینک اشتراک دریافتی را کپی کنید.\n"
        "3. در برنامه گزینه Import/Add را بزنید و لینک را وارد کنید.\n"
        "4. سرور را انتخاب کنید و روی Connect بزنید.\n\n"
        "در صورت خطا، تصویر خطا را برای پشتیبانی ارسال کنید."
    ),
    "content_guide_ios": (
        "🍎 آموزش اتصال در آیفون و آیپد\n\n"
        "1. اپلیکیشن سازگار با کانفیگ دریافتی را از App Store نصب کنید.\n"
        "2. لینک اشتراک یا کانفیگ را کپی کنید.\n"
        "3. در برنامه، Add/Import from clipboard را انتخاب کنید.\n"
        "4. اجازه افزودن VPN را تأیید و سپس Connect را لمس کنید.\n\n"
        "اگر اجازه VPN نمایش داده نشد، تنظیمات دستگاه را بررسی کنید."
    ),
    "content_guide_windows": (
        "🪟 آموزش اتصال در ویندوز\n\n"
        "1. نرم‌افزار سازگار با کانفیگ دریافتی را نصب کنید.\n"
        "2. لینک یا فایل کانفیگ را در برنامه Import کنید.\n"
        "3. یک سرور انتخاب کنید و Connect را بزنید.\n"
        "4. پس از اتصال، با باز کردن یک وب‌سایت اتصال را بررسی کنید.\n\n"
        "اگر آنتی‌ویروس برنامه را مسدود کرد، از پشتیبانی راهنمایی بگیرید."
    ),
    "content_guide_macos": (
        "💻 آموزش اتصال در مک\n\n"
        "1. برنامه سازگار با کانفیگ را نصب کنید.\n"
        "2. لینک اشتراک یا کانفیگ را Import کنید.\n"
        "3. در صورت درخواست macOS، مجوز VPN را تأیید کنید.\n"
        "4. سرور را انتخاب و Connect را بزنید.\n\n"
        "برای خطاهای مجوز، بخش VPN در تنظیمات macOS را بررسی کنید."
    ),
    "content_guides_menu": "📖 آموزش اتصال\n\nدستگاه خود را انتخاب کنید:",
    "content_support": (
        "📞 پشتیبانی\n\n"
        "برای پیگیری سفارش، مشکل اتصال یا پرسش‌های پیش از خرید، پیام بدهید."
    ),
    "content_support_unavailable": "اطلاعات پشتیبانی هنوز تنظیم نشده است. لطفاً بعداً دوباره تلاش کنید.",
    "content_no_plans": "در حال حاضر هیچ پلنی فعال نیست.",
    "content_choose_plan": "🛒 پلن موردنظر خود را انتخاب کنید:\n\n{plans}{coupon_note}",
    "content_coupon_prompt": "کد تخفیف را بفرستید، یا «cancel» برای انصراف.",
    "content_coupon_cancelled": "✅ واردکردن کد تخفیف لغو شد.",
    "content_coupon_invalid": "❌ کد تخفیف معتبر نیست یا ظرفیت آن تمام شده است.",
    "content_coupon_applied": "✅ کد «{code}» اعمال شد.",
    "content_coupon_active": "\n\n🎟 کد تخفیف فعال: {code}",
    "content_coupon_expired": "\n\n⚠️ کد تخفیف دیگر معتبر نیست.",
    "content_payment_unavailable": (
        "⚠️ پرداخت آنلاین فعلاً آماده نیست. لطفاً بعداً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
    ),
    "content_order_failed": "❌ خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.",
    "content_payment_details_missing": "⚠️ اطلاعات کارت پرداخت هنوز تنظیم نشده است.\n\n",
    "content_order_created": (
        "✅ سفارش شما ثبت شد.\n\n"
        "🆔 شماره سفارش: #{order_id}\n"
        "📦 پلن: {plan_name}\n"
        "💰 مبلغ قابل پرداخت: {price} تومان\n"
        "🎟 تخفیف: {discount} تومان\n\n"
        "{payment_details}"
        "پس از پرداخت، تصویر رسید را ارسال کنید."
    ),
    "content_receipt_cancelled": "✅ ارسال رسید لغو شد. می‌توانید دوباره از بخش خرید اقدام کنید.",
    "content_receipt_unavailable": "❌ این سفارش دیگر آمادهٔ دریافت رسید نیست. لطفاً وضعیت سفارش را بررسی کنید.",
    "content_receipt_forward_failed": "❌ ارسال رسید برای پشتیبانی ناموفق بود. لطفاً چند لحظه دیگر دوباره تلاش کنید.",
    "content_receipt_received": "✅ رسید شما دریافت شد.\n\nدر حال بررسی توسط پشتیبانی است.",
    "content_order_not_found": "❌ سفارش پیدا نشد. لطفاً دوباره از بخش خرید اقدام کنید.",
    "content_receipt_image_only": "❌ لطفاً فقط تصویر رسید پرداخت را ارسال کنید.",
}

GUIDE_CONTENT_KEYS = {
    "android": "content_guide_android",
    "ios": "content_guide_ios",
    "windows": "content_guide_windows",
    "macos": "content_guide_macos",
}


def render_content(template: str, **values: object) -> str:
    """Replace known placeholders without breaking text that contains braces."""
    return re.sub(
        r"\{([a-z_]+)\}",
        lambda match: str(values.get(match.group(1), match.group(0))),
        template,
    )


async def get_active_plans() -> list[Plan]:
    async with async_session() as session:
        return list(
            (
                await session.execute(
                    select(Plan)
                    .where(Plan.is_active.is_(True), Plan.is_deleted.is_(False))
                    .order_by(Plan.price)
                )
            ).scalars()
        )


def format_tariffs(plans: list[Plan]) -> str:
    details = []
    for plan in plans:
        description = f"\n📝 {plan.description}" if plan.description else ""
        details.append(
            f"📦 {plan.name}\n"
            f"💰 {plan.price:,} تومان | 📅 {format_duration(plan.duration, plan.duration_unit)} | 📶 {plan.traffic}"
            f"{description}"
        )
    return "💎 تعرفه‌ها\n\n" + "\n\n".join(details)
