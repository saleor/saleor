import operator
from collections import defaultdict
from functools import reduce
from typing import Optional

from django.db.models.query_utils import Q
from prices import Money

from ...discount.utils import calculate_discounted_price, fetch_active_discounts
from ..models import Product, ProductChannelListing, ProductVariantChannelListing


def _get_variant_prices_in_channels_dict(product):
    prices_dict = defaultdict(list)
    for variant_channel_listing in ProductVariantChannelListing.objects.filter(
        variant__product_id=product, price_amount__isnull=False
    ):
        channel_id = variant_channel_listing.channel_id
        prices_dict[channel_id].append(variant_channel_listing.price)
    return prices_dict


def _get_product_discounted_price(
    variant_prices, product, collections, discounts, channel
) -> Optional[Money]:
    discounted_variants_price = []
    for variant_price in variant_prices:
        discounted_variant_price = calculate_discounted_price(
            product=product,
            price=variant_price,
            collections=collections,
            discounts=discounts,
            channel=channel,
        )
        discounted_variants_price.append(discounted_variant_price)
    return min(discounted_variants_price)


def update_product_discounted_price(product, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()
    collections = list(product.collections.all())
    variant_prices_in_channels_dict = _get_variant_prices_in_channels_dict(product)
    changed_products_channels_to_update = []
    for product_channel_listing in product.channel_listings.all():
        channel_id = product_channel_listing.channel_id
        variant_prices_dict = variant_prices_in_channels_dict.get(channel_id)
        if not variant_prices_dict:
            continue
        product_discounted_price = _get_product_discounted_price(
            variant_prices_dict,
            product,
            collections,
            discounts,
            product_channel_listing.channel,
        )
        if product_channel_listing.discounted_price != product_discounted_price:
            product_channel_listing.discounted_price_amount = (
                product_discounted_price.amount
            )
            changed_products_channels_to_update.append(product_channel_listing)
    ProductChannelListing.objects.bulk_update(
        changed_products_channels_to_update, ["discounted_price_amount"]
    )


def update_products_discounted_prices(products, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()

    for product in products.prefetch_related("channel_listings"):
        update_product_discounted_price(product, discounts)


def update_products_discounted_prices_of_catalogues(
    product_ids=None, category_ids=None, collection_ids=None, variant_ids=None
):
    # Building the matching products query
    q_list = []
    if product_ids:
        q_list.append(Q(pk__in=product_ids))
    if category_ids:
        q_list.append(Q(category_id__in=category_ids))
    if collection_ids:
        q_list.append(Q(collectionproduct__collection_id__in=collection_ids))
    # Asserting that the function was called with some ids
    if variant_ids:
        q_list.append(Q(variants__id__in=variant_ids))
    if q_list:
        # Querying the products
        q_or = reduce(operator.or_, q_list)
        products = Product.objects.filter(q_or).distinct()

        update_products_discounted_prices(products)


def update_products_discounted_prices_of_discount(discount):
    update_products_discounted_prices_of_catalogues(
        product_ids=discount.products.all().values_list("id", flat=True),
        category_ids=discount.categories.all().values_list("id", flat=True),
        collection_ids=discount.collections.all().values_list("id", flat=True),
        variant_ids=discount.variants.all().values_list("id", flat=True),
    )
