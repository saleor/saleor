from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from ...checkout import base_calculations
from ...checkout.fetch import (
    fetch_active_discounts,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ...plugins.manager import get_plugins_manager


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

    manager = get_plugins_manager()
    channel = checkout_with_items.channel
    discounts_info = fetch_active_discounts()
    lines = checkout_with_items.lines.all()
    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(
        checkout_with_items, lines, discounts_info, manager
    )

    for line, line_info in zip(lines, lines_info):
        line.total_price_net_amount = base_calculations.calculate_base_line_total_price(
            line_info, channel, discounts_info
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
def mocked_fetch_checkout():
    def mocked_fetch_side_effect(
        checkout_info, manager, lines, address, discounts, force_update=False
    ):
        return checkout_info, lines

    with patch(
        "saleor.checkout.calculations.fetch_checkout_prices_if_expired",
        new=Mock(side_effect=mocked_fetch_side_effect),
    ) as mocked_fetch:
        yield mocked_fetch


@pytest.fixture
def mocked_fetch_order():
    def mocked_fetch_side_effect(order, manager, lines, force_update=False):
        return order, lines

    with patch(
        "saleor.order.calculations.fetch_order_prices_if_expired",
        new=Mock(side_effect=mocked_fetch_side_effect),
    ) as mocked_fetch:
        yield mocked_fetch
