from prices.taxed_money import TaxedMoney

from ...discount.utils import fetch_active_discounts
from ..models import Product


def _get_product_minimal_variant_price(product, discounts):
    # Start with the product's price as the minimal one
    minimal_variant_price = product.price
    for variant in product.variants.all():
        variant_price = variant.get_price(discounts=discounts)
        if isinstance(variant_price, TaxedMoney):
            # The "variant.get_price" method may return "TaxedMoney" instance but
            # because we haven't provided it with "taxes" kwarg we can ignore it
            # and "cast" it to just "Money" by taking net/gross (we take gross
            # just in case)
            variant_price = variant_price.gross
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


def update_products_minimal_variant_prices(products=None, discounts=None):
    if products is None:
        products = Product.objects.prefetch_related("variants").iterator()
    if discounts is None:
        discounts = fetch_active_discounts()
    for product in products:
        update_product_minimal_variant_price(product, discounts)


def update_products_minimal_variant_prices_of_discount(discount):
    all_discounts = fetch_active_discounts()
    update_products_minimal_variant_prices(discount.products.all(), all_discounts)
    for category in discount.categories.all():
        update_products_minimal_variant_prices(category.products.all(), all_discounts)
    for collection in discount.collections.all():
        update_products_minimal_variant_prices(collection.products.all(), all_discounts)
