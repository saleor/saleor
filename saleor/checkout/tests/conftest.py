from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from ...checkout.models import CheckoutLine
from ...plugins.manager import get_plugins_manager
from ..fetch import fetch_checkout_info, fetch_checkout_lines


@pytest.fixture
def priced_checkout_factory():
    def factory(checkout):
        manager = get_plugins_manager(allow_replica=False)
        lines, _ = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(checkout, lines, manager)

        tax = Decimal("1.23")

        lines_to_update = []
        for line_info in lines:
            line = line_info.line
            lines_to_update.append(line)

            line.total_price = manager.calculate_checkout_line_total(
                checkout_info, lines, line_info, None
            )
            line.total_price_gross_amount *= tax

        CheckoutLine.objects.bulk_update(
            lines_to_update,
            [
                "total_price_net_amount",
                "total_price_gross_amount",
            ],
        )

        checkout.shipping_price = manager.calculate_checkout_shipping(
            checkout_info, lines, None
        )
        checkout.subtotal = manager.calculate_checkout_subtotal(
            checkout_info, lines, None
        )
        checkout.total = manager.calculate_checkout_total(checkout_info, lines, None)

        checkout.shipping_price_gross_amount *= tax
        checkout.subtotal_gross_amount *= tax
        checkout.total_gross_amount *= tax
        # Cache prices until invalidated by force
        checkout.price_expiration = timezone.now() + timedelta(days=1)
        checkout.save()

        return checkout

    return factory


@pytest.fixture
def priced_checkout_with_item(priced_checkout_factory, checkout_with_item):
    return priced_checkout_factory(checkout_with_item)


@pytest.fixture
def priced_checkout_with_items(priced_checkout_factory, checkout_with_items):
    return priced_checkout_factory(checkout_with_items)


@pytest.fixture
def priced_checkout_with_voucher_percentage(
    priced_checkout_factory, checkout_with_voucher_percentage
):
    return priced_checkout_factory(checkout_with_voucher_percentage)
