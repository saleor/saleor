from collections import namedtuple

from ..cart.utils import get_cart_from_request, get_or_create_cart_from_request
from ..core.utils import to_local_currency
from .forms import get_form_class_for_product
from .models.utils import get_attributes_display_map
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
        yield product, get_availability(product, discounts, local_currency)


ProductAvailability = namedtuple(
    'ProductAvailability', (
        'available', 'price_range', 'price_range_undiscounted', 'discount',
        'price_range_local_currency', 'discount_local_currency'))


def get_availability(product, discounts=None, local_currency=None):
    # In default currency
    price_range = product.get_price_range(discounts=discounts)
    undiscounted = product.get_price_range()
    if undiscounted.min_price > price_range.min_price:
        discount = undiscounted.min_price - price_range.min_price
    else:
        discount = None

    # Local currency
    if local_currency:
        price_range_local = to_local_currency(
            price_range, local_currency)
        undiscounted_local = to_local_currency(
            undiscounted, local_currency)
        if (undiscounted_local and
                undiscounted_local.min_price > price_range_local.min_price):
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
        price_range_undiscounted=undiscounted,
        discount=discount,
        price_range_local_currency=price_range_local,
        discount_local_currency=discount_local_currency)


def handle_cart_form(request, product, create_cart=False):
    if create_cart:
        cart = get_or_create_cart_from_request(request)
    else:
        cart = get_cart_from_request(request)

    form_class = get_form_class_for_product(product)
    form = form_class(cart=cart, product=product,
                      data=request.POST or None, discounts=request.discounts)
    return form, cart


def products_for_cart(user):
    products = products_visible_to_user(user)
    products = products.prefetch_related(
        'variants', 'variants__variant_images__image')
    return products


def get_variant_picker_data(variants, attributes):
    data = {'attributes': [], 'variants': []}
    for attribute in attributes:
        data['attributes'].append({
            'pk': attribute.pk,
            'display': attribute.display,
            'name': attribute.name,
            'values': [{'pk': value.pk, 'display': value.display}
                       for value in attribute.values.all()]
        })
    for variant in variants:
        price = variant.get_price_per_item()
        variant_data = {
            'id': variant.id,
            'price': float(price.gross),
            'currency': price.currency,
            'attributes': variant.attributes
        }
        data['variants'].append(variant_data)
    return data


def get_product_attributes_data(product):
    attributes = product.product_class.product_attributes.prefetch_related(
        'values')
    attributes_map = {attribute.pk: attribute for attribute in attributes}
    values_map = get_attributes_display_map(product, attributes)
    return {attributes_map.get(attr_pk): value_obj
            for (attr_pk, value_obj) in values_map.items()}
