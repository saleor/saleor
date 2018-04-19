from collections import namedtuple

from .. import ProductAvailabilityStatus, VariantAvailabilityStatus
from ...core.utils import to_local_currency

ProductAvailability = namedtuple(
    'ProductAvailability', (
        'available', 'on_sale', 'price_range', 'price_range_undiscounted',
        'discount', 'price_range_local_currency', 'discount_local_currency'))


def products_with_availability(products, discounts, taxes, local_currency):
    for product in products:
        yield (product, get_availability(
            product, discounts, taxes, local_currency))


def get_product_availability_status(product):
    is_available = product.is_available()
    are_all_variants_in_stock = all(
        variant.is_in_stock() for variant in product.variants.all())
    is_in_stock = any(
        variant.is_in_stock() for variant in product.variants.all())
    requires_variants = product.product_type.has_variants

    if not product.is_published:
        return ProductAvailabilityStatus.NOT_PUBLISHED
    if requires_variants and not product.variants.exists():
        # We check the requires_variants flag here in order to not show this
        # status with product types that don't require variants, as in that
        # case variants are hidden from the UI and user doesn't manage them.
        return ProductAvailabilityStatus.VARIANTS_MISSSING
    if not is_in_stock:
        return ProductAvailabilityStatus.OUT_OF_STOCK
    if not are_all_variants_in_stock:
        return ProductAvailabilityStatus.LOW_STOCK
    if not is_available and product.available_on is not None:
        return ProductAvailabilityStatus.NOT_YET_AVAILABLE
    return ProductAvailabilityStatus.READY_FOR_PURCHASE


def get_variant_availability_status(variant):
    if not variant.is_in_stock():
        return VariantAvailabilityStatus.OUT_OF_STOCK
    return VariantAvailabilityStatus.AVAILABLE


def get_availability(product, discounts=None, taxes=None, local_currency=None):
    # In default currency
    price_range = product.get_price_range(discounts=discounts, taxes=taxes)
    undiscounted = product.get_price_range(taxes=taxes)
    if undiscounted.start > price_range.start:
        discount = undiscounted.start - price_range.start
    else:
        discount = None

    # Local currency
    if local_currency:
        price_range_local = to_local_currency(
            price_range, local_currency)
        undiscounted_local = to_local_currency(
            undiscounted, local_currency)
        if (undiscounted_local and
                undiscounted_local.start > price_range_local.start):
            discount_local_currency = (
                undiscounted_local.start - price_range_local.start)
        else:
            discount_local_currency = None
    else:
        price_range_local = None
        discount_local_currency = None

    is_available = product.is_in_stock() and product.is_available()
    is_on_sale = (
        product.is_available() and discount is not None and
        undiscounted.start != price_range.start)

    return ProductAvailability(
        available=is_available,
        on_sale=is_on_sale,
        price_range=price_range,
        price_range_undiscounted=undiscounted,
        discount=discount,
        price_range_local_currency=price_range_local,
        discount_local_currency=discount_local_currency)
