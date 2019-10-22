from django.utils.translation import ugettext_lazy as _

from ..checkout.error_codes import CheckoutErrorCode


class InsufficientStock(Exception):
    def __init__(self, item):
        super().__init__("Insufficient stock for %r" % (item,))
        self.item = item
        self.code = CheckoutErrorCode.INSUFFICIENT_STOCK


class ReadOnlyException(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = _("API runs in read-only mode")
        super().__init__(msg)
