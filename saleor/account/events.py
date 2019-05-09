from typing import Optional

from django.contrib.auth.base_user import AbstractBaseUser

from ..order.models import Order
from . import CustomerEvents
from .models import CustomerEvent

UserType = AbstractBaseUser


def _new_customer_event(**data) -> CustomerEvent:
    return CustomerEvent.objects.create(**data)


def customer_placed_order_event(
    *, user: UserType, order: Order
) -> Optional[CustomerEvent]:
    if user.is_anonymous:
        return None

    return _new_customer_event(user=user, order=order, type=CustomerEvents.PLACED_ORDER)
