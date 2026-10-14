from services.seed import create_default_plans
from handlers.shop import router as shop_router
from handlers.payment import router as payment_router
from handlers.start import router
from handlers.admin import router as admin_router
from handlers.info import router as info_router
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent
from config import settings, validate_settings
from db import (
    acquire_instance_lock,
    create_db,
    engine,
    release_instance_lock,
)


logger = logging.getLogger(__name__)


async def log_unhandled_update(event: ErrorEvent) -> bool:
    exception = event.exception
    logger.error(
        "Unhandled Telegram update",
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    return True


async def main():
    validate_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    acquire_instance_lock()
    bot = Bot(settings.bot_token)
    try:
        await create_db()
        await create_default_plans()

        dp = Dispatcher()
        dp.include_router(admin_router)
        dp.include_router(router)
        dp.include_router(shop_router)
        dp.include_router(info_router)
        dp.include_router(payment_router)
        dp.errors.register(log_unhandled_update)

        # Polling and a webhook cannot consume updates at the same time. This
        # preserves queued messages while switching a deployment to polling.
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Starting Telegram bot polling")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await engine.dispose()
        release_instance_lock()


if __name__ == "__main__":
    asyncio.run(main())
