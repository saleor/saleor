import pytest

from ...models import PreorderAllocation


@pytest.fixture
def preorder_allocation(
    order_line, preorder_variant_global_and_channel_threshold, channel_PLN
):
    variant = preorder_variant_global_and_channel_threshold
    product_variant_channel_listing = variant.channel_listings.get(channel=channel_PLN)
    return PreorderAllocation.objects.create(
        order_line=order_line,
        product_variant_channel_listing=product_variant_channel_listing,
        quantity=order_line.quantity,
    )
