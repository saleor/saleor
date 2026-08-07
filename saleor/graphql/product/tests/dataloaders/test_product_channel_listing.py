from .....product.models import ProductChannelListing
from ....context import SaleorContext
from ...dataloaders.products import (
    ProductChannelListingByProductIdAndChannelIdLoader,
    ProductChannelListingByProductIdAndChannelSlugLoader,
)


def test_product_channel_listing_by_product_id_and_channel_slug(
    product_available_in_many_channels, channel_USD, channel_PLN
):
    # given
    product = product_available_in_many_channels
    usd_listing = ProductChannelListing.objects.get(
        product=product, channel=channel_USD
    )
    pln_listing = ProductChannelListing.objects.get(
        product=product, channel=channel_PLN
    )
    keys = [
        (product.id, channel_USD.slug),
        (product.id, channel_PLN.slug),
        (product.id, "missing-channel"),
    ]

    # when
    context = SaleorContext()
    loader = ProductChannelListingByProductIdAndChannelSlugLoader(context)
    results = loader.load_many(keys).get()

    # then
    assert results == [usd_listing, pln_listing, None]


def test_product_channel_listing_by_product_id_and_channel_id(
    product_available_in_many_channels, channel_USD, channel_PLN
):
    # given
    product = product_available_in_many_channels
    usd_listing = ProductChannelListing.objects.get(
        product=product, channel=channel_USD
    )
    pln_listing = ProductChannelListing.objects.get(
        product=product, channel=channel_PLN
    )
    keys = [
        (product.id, channel_USD.id),
        (product.id, channel_PLN.id),
        (product.id, None),
        (product.id, 999999),
    ]

    # when
    context = SaleorContext()
    loader = ProductChannelListingByProductIdAndChannelIdLoader(context)
    results = loader.load_many(keys).get()

    # then
    assert results == [usd_listing, pln_listing, None, None]
