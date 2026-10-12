from db import async_session
from database.models import Coupon, CouponRedemption, Order, User, Plan
from sqlalchemy import select
from models.order_status import OrderStatus
from services.coupon_service import discount_for_price, normalize_coupon_code


async def create_order(
    telegram_id: int,
    plan_id: int,
    coupon_code: str | None = None,
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

        open_orders = list(
            (
                await session.execute(
                    select(Order).where(
                        Order.user_id == user.id,
                        Order.status.in_(
                            (
                                OrderStatus.PENDING_PAYMENT.value,
                                OrderStatus.WAITING_REVIEW.value,
                                OrderStatus.PAID.value,
                            )
                        ),
                    )
                )
            ).scalars()
        )
        # A payment already being reviewed/fulfilled must not be replaced by a
        # new checkout. Unpaid abandoned checkouts are safely expired below.
        if any(order.status != OrderStatus.PENDING_PAYMENT.value for order in open_orders):
            return None
        for open_order in open_orders:
            open_order.status = OrderStatus.EXPIRED.value


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


        discount_amount = 0
        normalized_code = None
        coupon = None
        if coupon_code:
            normalized_code = normalize_coupon_code(coupon_code)
            coupon = await session.scalar(select(Coupon).where(Coupon.code == normalized_code))
            if coupon is None or not coupon.is_active:
                return None
            if coupon.max_uses is not None and coupon.uses_count >= coupon.max_uses:
                return None
            redemption = await session.scalar(
                select(CouponRedemption).where(
                    CouponRedemption.coupon_id == coupon.id,
                    CouponRedemption.user_id == user.id,
                )
            )
            if redemption is not None:
                return None
            discount_amount = discount_for_price(coupon, plan.price)

        order = Order(
            user_id=user.id,
            plan_id=plan.id,
            price=plan.price - discount_amount,
            discount_amount=discount_amount,
            coupon_code=normalized_code,
            status=OrderStatus.PENDING_PAYMENT.value
        )

        session.add(order)

        if coupon is not None:
            coupon.uses_count += 1
            await session.flush()
            session.add(CouponRedemption(coupon_id=coupon.id, user_id=user.id, order_id=order.id))

        await session.commit()

        await session.refresh(order, attribute_names=["plan"])

        return order
