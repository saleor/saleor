import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from ....plugins.manager import get_plugins_manager
from ... import base_calculations
from ...fetch import fetch_checkout_info, fetch_checkout_lines
from ...models import CheckoutLine


@pytest.fixture
def checkout_with_prices(
    checkout_with_items,
    address,
    address_other_country,
    warehouse,
    customer_user,
    shipping_method,
    voucher,
):
    # Need to save shipping_method before fetching checkout info.
    checkout_with_items.shipping_method = shipping_method
    checkout_with_items.save(update_fields=["shipping_method"])

    manager = get_plugins_manager(allow_replica=False)
    lines = checkout_with_items.lines.all()
    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines_info, manager)

    for line, line_info in zip(lines, lines_info):
        line.total_price_net_amount = base_calculations.calculate_base_line_total_price(
            line_info
        ).amount
        line.total_price_gross_amount = line.total_price_net_amount * Decimal("1.230")

    checkout_with_items.discount_amount = Decimal("5.000")
    checkout_with_items.discount_name = "Voucher 5 USD"
    checkout_with_items.user = customer_user
    checkout_with_items.billing_address = address
    checkout_with_items.shipping_address = address_other_country
    checkout_with_items.collection_point = warehouse
    checkout_with_items.subtotal_net_amount = Decimal("100.000")
    checkout_with_items.subtotal_gross_amount = Decimal("123.000")
    checkout_with_items.total_net_amount = Decimal("150.000")
    checkout_with_items.total_gross_amount = Decimal("178.000")
    shipping_amount = base_calculations.base_checkout_delivery_price(
        checkout_info, lines_info
    ).amount
    checkout_with_items.shipping_price_net_amount = shipping_amount
    checkout_with_items.shipping_price_gross_amount = shipping_amount * Decimal("1.08")
    checkout_with_items.metadata_storage.metadata = {"meta_key": "meta_value"}
    checkout_with_items.metadata_storage.private_metadata = {
        "priv_meta_key": "priv_meta_value"
    }

    checkout_with_items.lines.bulk_update(
        lines,
        [
            "total_price_net_amount",
            "total_price_gross_amount",
        ],
    )

    checkout_with_items.save(
        update_fields=[
            "discount_amount",
            "discount_name",
            "user",
            "billing_address",
            "shipping_address",
            "collection_point",
            "subtotal_net_amount",
            "subtotal_gross_amount",
            "total_net_amount",
            "total_gross_amount",
            "shipping_price_net_amount",
            "shipping_price_gross_amount",
        ]
    )
    checkout_with_items.metadata_storage.save(
        update_fields=["metadata", "private_metadata"]
    )

    user = checkout_with_items.user
    user.metadata = {"user_public_meta_key": "user_public_meta_value"}
    user.save(update_fields=["metadata"])

    return checkout_with_items


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
        checkout.price_expiration = timezone.now() + datetime.timedelta(days=1)
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
