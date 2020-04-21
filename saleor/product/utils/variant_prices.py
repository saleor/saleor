import operator
from functools import reduce

from django.db.models.query_utils import Q
from prices import Money

from ...discount.utils import fetch_active_discounts
from ..models import Product


def _get_product_minimal_variant_price(product, discounts) -> Money:
    # Start with the product's price as the minimal one
    minimal_variant_price = product.price
    for variant in product.variants.all():
        variant_price = variant.get_price(discounts=discounts)
        minimal_variant_price = min(minimal_variant_price, variant_price)
    return minimal_variant_price


def update_product_minimal_variant_price(product, discounts=None, save=True):
    if discounts is None:
        discounts = fetch_active_discounts()
    minimal_variant_price = _get_product_minimal_variant_price(product, discounts)
    if product.minimal_variant_price != minimal_variant_price:
        product.minimal_variant_price_amount = minimal_variant_price.amount
        if save:
            product.save(update_fields=["minimal_variant_price_amount", "updated_at"])
    return product


def update_products_minimal_variant_prices(products, discounts=None):
    if discounts is None:
        discounts = fetch_active_discounts()
    changed_products_to_update = []
    for product in products:
        old_minimal_variant_price = product.minimal_variant_price
        updated_product = update_product_minimal_variant_price(
            product, discounts, save=False
        )
        # Check if the "minimal_variant_price" has changed
        if updated_product.minimal_variant_price != old_minimal_variant_price:
            changed_products_to_update.append(updated_product)
    # Bulk update the changed products
    Product.objects.bulk_update(
        changed_products_to_update, ["minimal_variant_price_amount"]
    )


def update_products_minimal_variant_prices_of_catalogues(
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

        update_products_minimal_variant_prices(products)


def update_products_minimal_variant_prices_of_discount(discount):
    update_products_minimal_variant_prices_of_catalogues(
        product_ids=discount.products.all().values_list("id", flat=True),
        category_ids=discount.categories.all().values_list("id", flat=True),
        collection_ids=discount.collections.all().values_list("id", flat=True),
    )
