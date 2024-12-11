import pytest

from ...models import ShippingMethodChannelListing
from ...utils import convert_to_shipping_method_data


@pytest.fixture
def shipping_method_data(shipping_method, channel_USD):
    listing = ShippingMethodChannelListing.objects.filter(
        channel=channel_USD, shipping_method=shipping_method
    ).get()
    return convert_to_shipping_method_data(shipping_method, listing)
