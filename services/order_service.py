from db import async_session
from database.models import Order, User, Plan
from sqlalchemy import select
from models.order_status import OrderStatus


async def create_order(
    telegram_id: int,
    plan_id: int
):
    async with async_session() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None or user.is_blocked:
            return None


        plan_result = await session.execute(
            select(Plan).where(
                Plan.id == plan_id,
                Plan.is_active.is_(True),
                Plan.is_deleted.is_(False),
            )
        )

        plan = plan_result.scalar_one_or_none()

        if plan is None:
            return None


        order = Order(
            user_id=user.id,
            plan_id=plan.id,
            price=plan.price,
            status=OrderStatus.PENDING_PAYMENT.value
        )

        session.add(order)

        await session.commit()

        await session.refresh(order, attribute_names=["plan"])

        return order
