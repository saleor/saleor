from collections import defaultdict

from ...checkout.models import CheckoutLine
from ..core.dataloaders import DataLoader


class CheckoutLinesByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlines_by_checkout"

    def batch_load(self, keys):
        lines = CheckoutLine.objects.filter(checkout_id__in=keys)
        line_map = defaultdict(list)
        for variant in lines.iterator():
            line_map[variant.checkout_id].append(variant)
        return [line_map.get(checkout_id, []) for checkout_id in keys]
