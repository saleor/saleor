from collections import defaultdict

from ...checkout.models import Checkout, CheckoutLine
from ..core.dataloaders import DataLoader


class CheckoutByIdLoader(DataLoader):
    context_key = "checkout_by_id"

    def batch_load(self, keys):
        checkouts = Checkout.objects.in_bulk(keys)
        return [checkouts.get(checkout_id) for checkout_id in keys]


class CheckoutLineByIdLoader(DataLoader):
    context_key = "checkout_line_by_id"

    def batch_load(self, keys):
        checkout_lines = CheckoutLine.objects.in_bulk(keys)
        return [checkout_lines.get(line_id) for line_id in keys]


class CheckoutLinesByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlines_by_checkout"

    def batch_load(self, keys):
        lines = CheckoutLine.objects.filter(checkout_id__in=keys)
        line_map = defaultdict(list)
        for variant in lines.iterator():
            line_map[variant.checkout_id].append(variant)
        return [line_map.get(checkout_id, []) for checkout_id in keys]
