from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Union

from ..checkout.error_codes import CheckoutErrorCode

if TYPE_CHECKING:
    from ..checkout.models import CheckoutLine
    from ..order.models import OrderLine
    from ..product.models import ProductVariant


@dataclass
class InsufficientStockData:
    variant: Optional["ProductVariant"] = None
    checkout_line: Optional["CheckoutLine"] = None
    order_line: Optional["OrderLine"] = None
    warehouse_pk: Union[str, int, None] = None
    available_quantity: Optional[int] = None


class InsufficientStock(Exception):
    def __init__(self, items: List[InsufficientStockData]):
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


class ReadOnlyException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "API runs in read-only mode"
        super().__init__(msg)


class ProductNotPublished(Exception):
    def __init__(self, context=None):
        super().__init__("Can't add unpublished product.")
        self.context = context
        self.code = CheckoutErrorCode.PRODUCT_NOT_PUBLISHED


class PermissionDenied(Exception):
    def __init__(self, message=None):
        default_message = "You do not have permission to perform this action"
        if message is None:
            message = default_message
        super().__init__(message)
