import operator
from functools import reduce
from typing import Optional

from django.db.models.query_utils import Q
from prices import Money

from ...discount.utils import calculate_discounted_price, fetch_active_discounts
from ..models import Product, ProductChannelListing, ProductVariantChannelListing


def _get_product_discounted_price(
    product_channel_listing, discounts
) -> Optional[Money]:
    # Start with the product's price as the minimal one
    minimal_variant_price = None
    variants_channel_listing = ProductVariantChannelListing.objects.filter(
        variant__product_id=product_channel_listing.product_id,
        channel_id=product_channel_listing.channel_id,
    )
    product = product_channel_listing.product
    collections = list(product.collections.all())
    for variant_channel_listing in variants_channel_listing:
        variant_price = calculate_discounted_price(
            product=product,
            price=variant_channel_listing.price,
            collections=collections,
            discounts=discounts,
        )
        if minimal_variant_price is None:
            minimal_variant_price = variant_price
        else:
            minimal_variant_price = min(minimal_variant_price, variant_price)
    return minimal_variant_price


def update_product_discounted_price(product, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()
    product_channel_listings = product.channel_listing.all()
    changed_products_channels_to_update = []
    for product_channel_listing in product_channel_listings:
        product_discounted_price = _get_product_discounted_price(
            product_channel_listing, discounts
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

    for product in products.prefetch_related("channel_listing"):
        update_product_discounted_price(product, discounts)


def update_products_discounted_prices_of_catalogues(
    product_ids=None, category_ids=None, collection_ids=None
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
    )
