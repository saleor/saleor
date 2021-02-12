from ..checkout.error_codes import CheckoutErrorCode


class InsufficientStock(Exception):
    def __init__(self, items, context=None):
        items = [str(item) for item in items]
        super().__init__(f"Insufficient stock for {', '.join(items)}")
        self.items = items
        self.context = context
        self.code = CheckoutErrorCode.INSUFFICIENT_STOCK


class AllocationError(Exception):
    def __init__(self, order_lines):
        order_lines = [str(line) for line in order_lines]
        super().__init__(
            f"Unable to deallocate stock for lines {', '.join(order_lines)}."
        )
        self.order_lines = order_lines


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
