from ..checkout.error_codes import CheckoutErrorCode


class InsufficientStock(Exception):
    def __init__(self, item):
        super().__init__("Insufficient stock for %r" % (item,))
        self.item = item
        self.code = CheckoutErrorCode.INSUFFICIENT_STOCK
