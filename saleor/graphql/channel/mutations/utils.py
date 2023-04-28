from datetime import timedelta
from typing import Optional

from django.core.exceptions import ValidationError

from saleor.graphql.core.enums import ChannelErrorCode

DELETE_EXPIRED_ORDERS_MAX_DAYS = 120


def clean_expire_orders_after(expire_orders_after: int) -> Optional[int]:
    if expire_orders_after is None or expire_orders_after == 0:
        return None
    if expire_orders_after < 0:
        raise ValidationError(
            {
                "expire_orders_after": ValidationError(
                    "Expiration time for orders cannot be lower than 0.",
                    code=ChannelErrorCode.INVALID.value,
                )
            }
        )
    return expire_orders_after


def clean_delete_expired_orders_after(delete_expired_orders_after: int) -> timedelta:
    if (
        delete_expired_orders_after < 1
        or delete_expired_orders_after > DELETE_EXPIRED_ORDERS_MAX_DAYS
    ):
        raise ValidationError(
            {
                "delete_expired_orders_after": ValidationError(
                    "Delete time for expired orders needs to be in range from 1 to "
                    f"{DELETE_EXPIRED_ORDERS_MAX_DAYS}.",
                    code=ChannelErrorCode.INVALID.value,
                )
            }
        )
    return timedelta(days=delete_expired_orders_after)
