from ...product.models import ProductChannelListing


def mark_products_as_dirty(channel_to_product_ids: dict[int, set[int]]):
    """Mark products as dirty to recalculate prices.

    Takes the dictionary of channel_id to product_ids as input and marks the
    discounted_price_dirty flag as True for all product channel listings related to
    input channels and products.
    """

    if not channel_to_product_ids:
        return
    channels = list(channel_to_product_ids.keys())
    product_ids = {
        product_id
        for product_ids in channel_to_product_ids.values()
        for product_id in product_ids
    }
    listing_ids_to_update = []
    product_channel_listings = ProductChannelListing.objects.filter(
        product_id__in=product_ids, channel_id__in=channels
    ).values_list("id", "product_id", "channel_id")

    for id, product_id, channel_id in product_channel_listings.iterator():
        product_ids = channel_to_product_ids.get(channel_id, set())
        if product_id in product_ids:
            listing_ids_to_update.append(id)

    if listing_ids_to_update:
        ProductChannelListing.objects.filter(id__in=listing_ids_to_update).update(
            discounted_price_dirty=True
        )
