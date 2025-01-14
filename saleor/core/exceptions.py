from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from graphql import GraphQLError

from ..checkout.error_codes import CheckoutErrorCode

if TYPE_CHECKING:
    from ..checkout.models import CheckoutLine
    from ..order.models import OrderLine
    from ..product.models import ProductVariant


@dataclass
class InsufficientStockData:
    available_quantity: int
    variant: Optional["ProductVariant"] = None
    checkout_line: Optional["CheckoutLine"] = None
    order_line: Optional["OrderLine"] = None
    warehouse_pk: UUID | None = None


class NonExistingCheckoutLines(Exception):
    def __init__(self, line_pks: set[UUID]):
        self.line_pks = line_pks
        super().__init__("Checkout lines don't exist.")


class InsufficientStock(Exception):
    def __init__(self, items: list[InsufficientStockData]):
        details = [str(item.variant or item.order_line) for item in items]
        super().__init__(f"Insufficient stock for {', '.join(details)}")
        self.items = items
        self.code = CheckoutErrorCode.INSUFFICIENT_STOCK


class AllocationError(Exception):
    def __init__(self, order_lines):
        lines = [str(line) for line in order_lines]
        super().__init__(f"Unable to deallocate stock for lines {', '.join(lines)}.")
        self.order_lines = order_lines


class PreorderAllocationError(Exception):
    def __init__(self, order_line):
        super().__init__(f"Unable to allocate in stock for line {str(order_line)}.")
        self.order_line = order_line


class ProductNotPublished(Exception):
    def __init__(self, context=None):
        super().__init__("Can't add unpublished product.")
        self.context = context
        self.code = CheckoutErrorCode.PRODUCT_NOT_PUBLISHED


class PermissionDenied(Exception):
    def __init__(self, message=None, *, permissions: Iterable[Enum] | None = None):
        if not message:
            if permissions:
                permission_list = ", ".join(p.name for p in permissions)
                message = (
                    "To access this path, you need one of the "
                    f"following permissions: {permission_list}"
                )
            else:
                message = "You do not have permission to perform this action"
        super().__init__(message)
        self.permissions = permissions


class GiftCardNotApplicable(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
        self.code = CheckoutErrorCode.GIFT_CARD_NOT_APPLICABLE.value


class CircularSubscriptionSyncEvent(GraphQLError):
    pass


class SyncEventError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message, code)
        self.message = message
        self.code = code

    def __str__(self):
        return self.message
