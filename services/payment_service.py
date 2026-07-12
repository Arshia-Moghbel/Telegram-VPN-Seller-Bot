from database.models import Receipt, Order
from db import async_session
from sqlalchemy import select
from models.order_status import OrderStatus


async def save_receipt(
    order_id: int,
    telegram_file_id: str
):
    async with async_session() as session:

        result = await session.execute(
            select(Order).where(
                Order.id == order_id
            )
        )

        order = result.scalar_one_or_none()

        if order is None:
            return None

        receipt = Receipt(
            order_id=order.id,
            telegram_file_id=telegram_file_id
        )

        order.status = OrderStatus.WAITING_REVIEW.value

        session.add(receipt)

        await session.commit()

        await session.refresh(receipt)

        return receipt