import operator
from collections import defaultdict
from functools import reduce
from typing import Dict, Iterable, List

from django.db.models import Exists, OuterRef
from django.db.models.query_utils import Q
from prices import Money

from ...discount.utils import calculate_discounted_price, fetch_active_discounts
from ..models import (
    CollectionProduct,
    Product,
    ProductChannelListing,
    ProductVariant,
    ProductVariantChannelListing,
)


def update_products_discounted_price(products: Iterable[Product], discounts=None):
    """Update Products and ProductVariants discounted prices.

    The discounted price is the minimal price of the product/variant based on active
    sales that are applied to a given product.
    If there is no applied sale, the discounted price for the product is equal to the
    cheapest variant price, in the case of the variant it's equal to the variant price.
    """
    if discounts is None:
        discounts = fetch_active_discounts()
    product_ids = [product.id for product in products]
    product_qs = Product.objects.filter(id__in=product_ids)
    collection_products = CollectionProduct.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )
    product_to_collection_ids_map = defaultdict(set)
    for collection_id, product_id in collection_products.values_list(
        "collection_id", "product_id"
    ):
        product_to_collection_ids_map[product_id].add(collection_id)

    product_to_variant_prices_per_channel_map = (
        _get_product_to_variant_prices_per_channel_map(product_ids)
    )

    changed_products_channels_to_update = []
    product_channel_listings = ProductChannelListing.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )
    for product_channel_listing in product_channel_listings:
        product_id = product_channel_listing.product_id
        channel_id = product_channel_listing.channel_id
        variant_prices = product_to_variant_prices_per_channel_map[product_id][
            channel_id
        ]
        if not variant_prices:
            continue
        collection_ids = product_to_collection_ids_map[product_id]
        product_discounted_price = _get_product_discounted_price(
            variant_prices,
            product_channel_listing.product,
            collection_ids,
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


def _get_product_to_variant_prices_per_channel_map(product_ids: Iterable[int]):
    products = Product.objects.filter(id__in=product_ids)
    variants = ProductVariant.objects.filter(
        Exists(products.filter(id=OuterRef("product_id")))
    )
    variant_channel_listings = ProductVariantChannelListing.objects.filter(
        Exists(variants.filter(id=OuterRef("variant_id"))), price_amount__isnull=False
    )
    variant_to_product_id = {
        variant_id: product_id
        for variant_id, product_id in variants.values_list("id", "product_id")
    }

    price_data: Dict[int, Dict[int, List[Money]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for variant_channel_listings in variant_channel_listings:
        product_id = variant_to_product_id[variant_channel_listings.variant_id]
        # TODO: here we can provide NamedTuple with variant and price to have
        # variant instance
        price_data[product_id][variant_channel_listings.channel_id].append(
            variant_channel_listings.price
        )
    return price_data


def _get_product_discounted_price(
    variant_prices, product, collection_ids, discounts, channel
) -> Money:
    discounted_variants_price: List[Money] = []
    for variant_price in variant_prices:
        discounted_variant_price = calculate_discounted_price(
            product=product,
            price=variant_price,
            collection_ids=collection_ids,
            discounts=discounts,
            channel=channel,
        )
        discounted_variants_price.append(discounted_variant_price)
    return min(discounted_variants_price)


def _products_in_batches(products_qs):
    """Slice a products queryset into batches."""
    start_pk = 0

    # Results in memory usage of ~40MB for 500 products
    BATCH_SIZE = 500

    while True:
        products = list(
            products_qs.order_by("pk")
            .filter(pk__gt=start_pk)
            .prefetch_related("channel_listings", "collections")[:BATCH_SIZE]
        )
        if not products:
            break
        yield products
        start_pk = products[-1].pk


def update_products_discounted_prices(products, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()

    for product_batch in _products_in_batches(products):
        update_products_discounted_price(product_batch)


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
