import pytest

from ....plugins.manager import get_plugins_manager
from ....shipping.models import ShippingMethodChannelListing
from ...fetch import CheckoutInfo, fetch_checkout_info, fetch_checkout_lines


@pytest.fixture
def checkout_info(checkout_lines_info):
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_lines_info[0].line.checkout
    checkout_info = fetch_checkout_info(checkout, checkout_lines_info, manager)
    return checkout_info


@pytest.fixture
def checkout_with_items_and_shipping_info(checkout_with_items_and_shipping):
    checkout = checkout_with_items_and_shipping
    channel = checkout.channel
    shipping_address = checkout.shipping_address
    shipping_method = checkout.shipping_method
    shipping_channel_listing = ShippingMethodChannelListing.objects.get(
        channel=channel,
        shipping_method=shipping_method,
    )
    manager = get_plugins_manager(allow_replica=False)
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        shipping_channel_listings=[shipping_channel_listing],
        tax_configuration=channel.tax_configuration,
        discounts=[],
        manager=manager,
        lines=lines,
    )
    return checkout_info
