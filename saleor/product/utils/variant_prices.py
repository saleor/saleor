from django.db.models.query_utils import Q

from ...discount.utils import fetch_active_discounts
from ..models import Product


def _get_product_minimal_variant_price(product, discounts):
    # Start with the product's price as the minimal one
    minimal_variant_price = product.price
    for variant in product.variants.all():
        variant_price = variant.get_price(discounts=discounts)
        minimal_variant_price = min(minimal_variant_price, variant_price)
    return minimal_variant_price


def update_product_minimal_variant_price(product, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()
    minimal_variant_price = _get_product_minimal_variant_price(product, discounts)
    if product.minimal_variant_price != minimal_variant_price:
        product.minimal_variant_price = minimal_variant_price
        product.save(update_fields=["minimal_variant_price"])
    return product


def update_products_minimal_variant_prices(products, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()
    for product in products:
        update_product_minimal_variant_price(product, discounts)


def update_products_minimal_variant_prices_of_catalogues(
    product_ids=[], category_ids=[], collection_ids=[]
):
    products = Product.objects.filter(
        Q(pk__in=product_ids)
        | Q(category_id__in=category_ids)
        | Q(collectionproduct__collection_id__in=collection_ids)
    ).distinct()
    update_products_minimal_variant_prices(products)


def update_products_minimal_variant_prices_of_discount(discount):
    update_products_minimal_variant_prices_of_catalogues(
        product_ids=discount.products.all().values_list("id", flat=True),
        category_ids=discount.categories.all().values_list("id", flat=True),
        collection_ids=discount.collections.all().values_list("id", flat=True),
    )
