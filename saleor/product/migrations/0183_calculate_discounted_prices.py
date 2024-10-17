# Generated by Django 3.2.18 on 2023-05-05 07:46

from collections import defaultdict, namedtuple
from decimal import ROUND_HALF_UP
from functools import partial

import mptt
import mptt.managers
from django.db import migrations
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from prices import Money, fixed_discount, percentage_discount

BATCH_SIZE = 500

DiscountInfo = namedtuple(
    "DiscountInfo",
    [
        "sale",
        "channel_listings",
        "product_ids",
        "category_ids",
        "collection_ids",
        "variants_ids",
    ],
)


def calculate_variants_discounted_price(apps, schema_editor):
    Product = apps.get_model("product", "Product")
    ProductVariant = apps.get_model("product", "ProductVariant")
    CollectionProduct = apps.get_model("product", "CollectionProduct")
    ProductChannelListing = apps.get_model("product", "ProductChannelListing")
    ProductVariantChannelListing = apps.get_model(
        "product", "ProductVariantChannelListing"
    )
    SaleChannelListing = apps.get_model("discount", "SaleChannelListing")
    manager = mptt.managers.TreeManager()
    Category = apps.get_model("product", "Category")
    manager.model = Category
    mptt.register(Category, order_insertion_by=["id"])
    Category.tree = manager
    Sale = apps.get_model("discount", "Sale")
    discounts = fetch_discounts(Sale, SaleChannelListing, Category)
    update_discounted_prices_task(
        Product,
        CollectionProduct,
        ProductChannelListing,
        ProductVariantChannelListing,
        ProductVariant,
        discounts,
    )


def fetch_discounts(sale_model, sale_listing_model, category_model):
    date = timezone.now()
    sales = list(
        sale_model.objects.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date), start_date__lte=date
        )
    )
    pks = {s.pk for s in sales}
    collections = fetch_collections(sale_model, pks)
    channel_listings = fetch_sale_channel_listings(sale_listing_model, pks)
    products = fetch_products(sale_model, pks)
    categories = fetch_categories(sale_model, category_model, pks)
    variants = fetch_variants(sale_model, pks)

    return [
        DiscountInfo(
            sale=sale,
            category_ids=categories[sale.pk],
            channel_listings=channel_listings[sale.pk],
            collection_ids=collections[sale.pk],
            product_ids=products[sale.pk],
            variants_ids=variants[sale.pk],
        )
        for sale in sales
    ]


def fetch_collections(sale_model, sale_pks):
    collections = (
        sale_model.collections.through.objects.filter(sale_id__in=sale_pks)
        .order_by("id")
        .values_list("sale_id", "collection_id")
    )
    collection_map = defaultdict(set)
    for sale_pk, collection_pk in collections:
        collection_map[sale_pk].add(collection_pk)
    return collection_map


def fetch_products(sale_model, sale_pks):
    products = (
        sale_model.products.through.objects.filter(sale_id__in=sale_pks)
        .order_by("id")
        .values_list("sale_id", "product_id")
    )
    product_map = defaultdict(set)
    for sale_pk, product_pk in products:
        product_map[sale_pk].add(product_pk)
    return product_map


def fetch_variants(
    sale_model,
    sale_pks,
):
    variants = (
        sale_model.variants.through.objects.filter(sale_id__in=sale_pks)
        .order_by("id")
        .values_list("sale_id", "productvariant_id")
    )
    variants_map = defaultdict(set)
    for sale_pk, variant_pk in variants:
        variants_map[sale_pk].add(variant_pk)
    return variants_map


def fetch_sale_channel_listings(
    sale_listing_model,
    sale_pks,
):
    channel_listings = sale_listing_model.objects.filter(sale_id__in=sale_pks)
    channel_listings_map = defaultdict(dict)
    for channel_listing in channel_listings:
        sale_id_row = channel_listings_map[channel_listing.sale_id]
        sale_id_row[channel_listing.channel_id] = channel_listing
    return channel_listings_map


def fetch_categories(
    sale_model,
    category_model,
    sale_pks,
):
    categories = (
        sale_model.categories.through.objects.filter(sale_id__in=sale_pks)
        .order_by("id")
        .values_list("sale_id", "category_id")
    )
    category_map = defaultdict(set)
    for sale_pk, category_pk in categories:
        category_map[sale_pk].add(category_pk)
    subcategory_map = defaultdict(set)
    for sale_pk, category_pks in category_map.items():
        subcategory_map[sale_pk] = set(
            category_model.tree.filter(pk__in=category_pks)
            .get_descendants(include_self=True)
            .values_list("pk", flat=True)
        )
    return subcategory_map


def update_discounted_prices_task(
    product_model,
    collection_product_model,
    product_listing_model,
    variant_listing_model,
    variant_model,
    discounts,
    start_pk: int = 0,
):
    products = list(
        product_model.objects.filter(pk__gt=start_pk)
        .prefetch_related("channel_listings", "collections")
        .order_by("pk")[:BATCH_SIZE]
    )

    if products:
        update_products_discounted_price(
            product_model,
            collection_product_model,
            product_listing_model,
            variant_listing_model,
            variant_model,
            products,
            discounts,
        )
        update_discounted_prices_task(
            product_model,
            collection_product_model,
            product_listing_model,
            variant_listing_model,
            variant_model,
            discounts,
            start_pk=products[-1].pk,
        )


def update_products_discounted_price(
    product_model,
    collection_product_model,
    product_listing_model,
    variant_listing_model,
    variant_model,
    products,
    discounts,
):
    """Update Products and ProductVariants discounted prices.

    The discounted price is the minimal price of the product/variant based on active
    sales that are applied to a given product.
    If there is no applied sale, the discounted price for the product is equal to the
    cheapest variant price, in the case of the variant it's equal to the variant price.
    """
    product_ids = [product.id for product in products]
    product_qs = product_model.objects.filter(id__in=product_ids)
    collection_products = collection_product_model.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )
    product_to_collection_ids_map = defaultdict(set)
    for collection_id, product_id in collection_products.values_list(
        "collection_id", "product_id"
    ):
        product_to_collection_ids_map[product_id].add(collection_id)

    product_to_variant_listings_per_channel_map = (
        _get_product_to_variant_channel_listings_per_channel_map(
            product_model, variant_model, variant_listing_model, product_ids
        )
    )

    changed_products_listings_to_update = []
    changed_variants_listings_to_update = []
    product_channel_listings = product_listing_model.objects.filter(
        Exists(product_qs.filter(id=OuterRef("product_id")))
    )
    for product_channel_listing in product_channel_listings:
        product_id = product_channel_listing.product_id
        channel_id = product_channel_listing.channel_id
        variant_listings = product_to_variant_listings_per_channel_map[product_id][
            channel_id
        ]
        if not variant_listings:
            continue
        collection_ids = product_to_collection_ids_map[product_id]
        (
            discounted_variants_price,
            variant_listings_to_update,
        ) = _get_discounted_variants_prices(
            variant_listings,
            product_channel_listing.product,
            collection_ids,
            discounts,
            product_channel_listing.channel_id,
        )

        product_discounted_price = min(discounted_variants_price)
        changed_variants_listings_to_update.extend(variant_listings_to_update)

        # check if the product discounted_price has changed
        if (
            product_channel_listing.discounted_price_amount
            != product_discounted_price.amount
        ):
            product_channel_listing.discounted_price_amount = (
                product_discounted_price.amount
            )
            changed_products_listings_to_update.append(product_channel_listing)

    if changed_products_listings_to_update:
        product_listing_model.objects.bulk_update(
            changed_products_listings_to_update, ["discounted_price_amount"]
        )
    if changed_variants_listings_to_update:
        variant_listing_model.objects.bulk_update(
            changed_variants_listings_to_update, ["discounted_price_amount"]
        )


def _get_product_to_variant_channel_listings_per_channel_map(
    product_model,
    variant_model,
    variant_listing_model,
    product_ids,
):
    products = product_model.objects.filter(id__in=product_ids)
    variants = variant_model.objects.filter(
        Exists(products.filter(id=OuterRef("product_id")))
    )
    variant_channel_listings = variant_listing_model.objects.filter(
        Exists(variants.filter(id=OuterRef("variant_id"))), price_amount__isnull=False
    )
    variant_to_product_id = {
        variant_id: product_id
        for variant_id, product_id in variants.values_list("id", "product_id")
    }

    price_data = defaultdict(lambda: defaultdict(list))
    for variant_channel_listing in variant_channel_listings:
        product_id = variant_to_product_id[variant_channel_listings.variant_id]
        price_data[product_id][variant_channel_listings.channel_id].append(
            variant_channel_listing
        )
    return price_data


def _get_discounted_variants_prices(
    variant_listings,
    product,
    collection_ids,
    discounts,
    channel_id,
):
    variants_listings_to_update = []
    discounted_variants_price = []
    for variant_listing in variant_listings:
        discounted_variant_price = Money(
            variant_listing.price_amount, variant_listing.currency
        )
        if discounts:
            discounted_variant_price = get_minimal_price(
                product=product,
                price=discounted_variant_price,
                collection_ids=collection_ids,
                discounts=discounts,
                channel_id=channel_id,
                variant_id=variant_listing.variant_id,
            )
        if variant_listing.discounted_price_amount != discounted_variant_price.amount:
            variant_listing.discounted_price_amount = discounted_variant_price.amount
            variants_listings_to_update.append(variant_listing)
        discounted_variants_price.append(discounted_variant_price)
    return discounted_variants_price, variants_listings_to_update


def get_minimal_price(
    product,
    price,
    collection_ids,
    discounts,
    channel_id,
    variant_id,
):
    """Return a sale_id and minimum product's price."""
    available_discounts = [
        discount
        for discount in get_product_discounts(
            product=product,
            collection_ids=collection_ids,
            discounts=discounts,
            channel_id=channel_id,
            variant_id=variant_id,
        )
        if discount
    ]
    if not available_discounts:
        return price

    min_price = min([discount(price) for discount in available_discounts])
    return min_price


def get_product_discounts(
    product,
    collection_ids,
    discounts,
    channel_id,
    variant_id,
):
    """Return sale ids, discount values for all discounts applicable to a product."""
    for discount in discounts:
        is_product_on_sale = (
            product.id in discount.product_ids
            or product.category_id in discount.category_ids
            or bool(collection_ids.intersection(discount.collection_ids))
        )
        is_variant_on_sale = variant_id and variant_id in discount.variants_ids
        if is_product_on_sale or is_variant_on_sale:
            sale_channel_listing = discount.channel_listings.get(channel_id)
            yield get_discount(discount.sale, sale_channel_listing)


def get_discount(sale, sale_channel_listing):
    if not sale_channel_listing:
        return
    if sale.type == "fixed":
        discount_amount = Money(
            sale_channel_listing.discount_value, sale_channel_listing.currency
        )
        return partial(fixed_discount, discount=discount_amount)
    if sale.type == "percentage":
        return partial(
            percentage_discount,
            percentage=sale_channel_listing.discount_value,
            rounding=ROUND_HALF_UP,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0182_productvariantchannellisting_discounted_price_amount"),
    ]

    operations = [
        migrations.RunPython(
            calculate_variants_discounted_price, migrations.RunPython.noop
        ),
    ]
