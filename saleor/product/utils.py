from collections import namedtuple

from ..core.utils import to_local_currency
from .models import Product


def products_visible_to_user(user):
    if (user.is_authenticated() and
            user.is_active and user.is_staff):
        return Product.objects.all()
    else:
        return Product.objects.get_available_products()


def products_with_details(user):
    products = products_visible_to_user(user)
    products = products.prefetch_related('categories', 'images',
                                         'variants__stock',
                                         'variants__variant_images__image',
                                         'attributes__values')
    return products


def get_product_images(product):
    """
    Returns list of product images that will be placed in product gallery
    """
    return list(product.images.all())


def products_with_availability(products, discounts, local_currency):
    for product in products:
        yield (product, get_availability(product, discounts, local_currency))


ProductAvailability = namedtuple(
    'ProductAvailability', (
        'available', 'price_range', 'discount',
        'price_range_local_currency', 'discount_local_currency'))


def get_availability(product, discounts=None, local_currency=None):
    # In default currency
    price_range = product.get_price_range(discounts=discounts)
    uncdiscounted = product.get_price_range()
    if uncdiscounted.min_price > price_range.min_price:
        discount = uncdiscounted.min_price - price_range.min_price
    else:
        discount = None

    # Local currency
    if local_currency:
        price_range_local = to_local_currency(
            price_range, local_currency)
        undiscounted_local = to_local_currency(
            uncdiscounted, local_currency)
        if undiscounted_local and undiscounted_local.min_price > price_range_local.min_price:
            discount_local_currency = (
                undiscounted_local.min_price - price_range_local.min_price)
        else:
            discount_local_currency = None
    else:
        price_range_local = None
        discount_local_currency = None

    is_available = product.is_in_stock() and product.is_available()

    return ProductAvailability(
        available=is_available,
        price_range=price_range,
        discount=discount,
        price_range_local_currency=price_range_local,
        discount_local_currency=discount_local_currency)
