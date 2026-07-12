from sqlalchemy import select

from db import async_session
from database.models import Plan


async def create_default_plans():
    async with async_session() as session:

        result = await session.execute(
            select(Plan)
        )

        plans = result.scalars().all()

        legacy_names = {
            "اقتصادی": "پلن ۱",
            "استاندارد": "پلن ۲",
            "حرفه‌ای": "پلن ۳",
        }

        renamed_plans = False
        for plan in plans:
            if plan.name in legacy_names:
                plan.name = legacy_names[plan.name]
                renamed_plans = True

        if renamed_plans:
            await session.commit()

        if plans:
            return

        default_plans = [
            Plan(
                name="پلن ۱",
                price=100000,
                duration=1,
                traffic="100GB",
                description="مناسب استفاده روزمره و شبکه‌های اجتماعی",
            ),
            Plan(
                name="پلن ۲",
                price=270000,
                duration=3,
                traffic="300GB",
                description="انتخاب متعادل برای استفاده شخصی و کاری",
            ),
            Plan(
                name="پلن ۳",
                price=500000,
                duration=6,
                traffic="700GB",
                description="مناسب کاربران حرفه‌ای و مصرف بالا",
            ),
        ]

        session.add_all(default_plans)
        await session.commit()
