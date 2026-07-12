from enum import Enum


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment"
    WAITING_REVIEW = "waiting_review"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELED = "canceled"
    EXPIRED = "expired"
