import asyncio
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{directory}/test.db"
        os.environ["BOT_TOKEN"] = "123456:ABCDEF_test_token"
        os.environ["ADMIN_ID"] = "1"

        from database.models import Plan, User
        from db import async_session, create_db, engine
        from models.order_status import OrderStatus
        from services.admin_service import get_content_settings, save_payment_setting
        from services.coupon_service import create_coupon
        from services.order_service import create_order

        await create_db()
        assert await save_payment_setting("content_servers", "سرور آزمایشی")
        assert (await get_content_settings())["content_servers"] == "سرور آزمایشی"

        async with async_session() as session:
            user = User(telegram_id=10, username="buyer")
            plan = Plan(name="Test", price=100_000, duration=24, duration_unit="hour", traffic="10GB")
            session.add_all((user, plan))
            await session.commit()
            await session.refresh(plan)
            plan_id = plan.id

        await create_coupon("SAVE10", "percent", 10, 1)
        order = await create_order(10, plan_id, "save10")
        assert order is not None
        assert order.price == 90_000
        assert order.discount_amount == 10_000
        assert order.status == OrderStatus.PENDING_PAYMENT.value
        assert await create_order(10, plan_id, "save10") is None
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
    print("smoke tests: OK")
