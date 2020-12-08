from collections import defaultdict

from django.db.models import F

from ...checkout.models import Checkout, CheckoutLine
from ..core.dataloaders import DataLoader


class CheckoutByIdLoader(DataLoader):
    context_key = "checkout_by_id"

    def batch_load(self, keys):
        checkouts = Checkout.objects.in_bulk(keys)
        return [checkouts.get(checkout_id) for checkout_id in keys]


class CheckoutByUserLoader(DataLoader):
    context_key = "checkout_by_user"

    def batch_load(self, keys):
        checkouts = Checkout.objects.filter(user_id__in=keys, channel__is_active=True)
        checkout_by_user_map = defaultdict(list)
        for checkout in checkouts:
            checkout_by_user_map[checkout.user_id].append(checkout)
        return [checkout_by_user_map.get(user_id) for user_id in keys]


class CheckoutByUserAndChannelLoader(DataLoader):
    context_key = "checkout_by_user_and_channel"

    def batch_load(self, keys):
        user_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        checkouts = Checkout.objects.filter(
            user_id__in=user_ids,
            channel__slug__in=channel_slugs,
            channel__is_active=True,
        ).annotate(channel_slug=F("channel__slug"))
        checkout_by_user_and_channel_map = defaultdict(list)
        for checkout in checkouts:
            key = (checkout.user_id, checkout.channel_slug)
            checkout_by_user_and_channel_map[key].append(checkout)
        return [checkout_by_user_and_channel_map.get(key) for key in keys]


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
