from collections import defaultdict, namedtuple
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db.models import F
from django.utils.encoding import smart_text
from django_prices.templatetags import prices_i18n
from prices import Price, PriceRange

from . import ProductAvailabilityStatus, VariantAvailabilityStatus
from ..cart.utils import get_cart_from_request, get_or_create_cart_from_request
from ..core.utils import get_paginator_items, to_local_currency
from ..core.utils.filters import get_now_sorted_by
from .forms import ProductForm


def products_visible_to_user(user):
    # pylint: disable=cyclic-import
    from .models import Product
    if user.is_authenticated and user.is_active and user.is_staff:
        return Product.objects.all()
    return Product.objects.available_products()


def products_with_details(user):
    products = products_visible_to_user(user)
    products = products.prefetch_related(
        'category', 'images', 'variants__stock',
        'variants__variant_images__image', 'attributes__values',
        'product_type__variant_attributes__values',
        'product_type__product_attributes__values')
    return products


def products_for_homepage():
    user = AnonymousUser()
    products = products_with_details(user)
    products = products.filter(is_featured=True)
    return products


def get_product_images(product):
    """Return list of product images that will be placed in product gallery."""
    return list(product.images.all())


def products_with_availability(products, discounts, local_currency):
    for product in products:
        yield product, get_availability(product, discounts, local_currency)


ProductAvailability = namedtuple(
    'ProductAvailability', (
        'available', 'on_sale', 'price_range', 'price_range_undiscounted',
        'discount', 'price_range_local_currency', 'discount_local_currency'))


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
    is_on_sale = (
        product.is_available() and discount is not None and
        undiscounted.min_price != price_range.min_price)

    return ProductAvailability(
        available=is_available,
        on_sale=is_on_sale,
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
    form = ProductForm(
        cart=cart, product=product, data=request.POST or None,
        discounts=request.discounts)
    return form, cart


def products_for_cart(user):
    products = products_visible_to_user(user)
    products = products.prefetch_related('variants__variant_images__image')
    return products


def product_json_ld(product, attributes=None):
    # type: (saleor.product.models.Product, saleor.product.utils.ProductAvailability, dict) -> dict  # noqa
    """Generate JSON-LD data for product."""
    data = {'@context': 'http://schema.org/',
            '@type': 'Product',
            'name': smart_text(product),
            'image': [
                product_image.image.url
                for product_image in product.images.all()],
            'description': product.description,
            'offers': []}

    for variant in product.variants.all():
        price = variant.get_price_per_item()
        available = 'http://schema.org/InStock'
        if not product.is_available() or not variant.is_in_stock():
            available = 'http://schema.org/OutOfStock'
        variant_data = {
            '@type': 'Offer',
            'availability': available,
            'itemCondition': 'http://schema.org/NewCondition',
            'price': price.gross,
            'priceCurrency': price.currency,
            'sku': variant.sku}
        data['offers'].append(variant_data)

    if attributes is not None:
        brand = ''
        for key in attributes:
            if key.name == 'brand':
                brand = attributes[key].name
                break
            elif key.name == 'publisher':
                brand = attributes[key].name

        if brand:
            data['brand'] = {'@type': 'Thing', 'name': brand}
    return data


def get_variant_picker_data(product, discounts=None, local_currency=None):
    availability = get_availability(product, discounts, local_currency)
    variants = product.variants.all()
    data = {'variantAttributes': [], 'variants': []}

    variant_attributes = product.product_type.variant_attributes.all()

    # Collect only available variants
    filter_available_variants = defaultdict(list)

    for variant in variants:
        price = variant.get_price_per_item(discounts)
        price_undiscounted = variant.get_price_per_item()
        if local_currency:
            price_local_currency = to_local_currency(price, local_currency)
        else:
            price_local_currency = None

        schema_data = {'@type': 'Offer',
                       'itemCondition': 'http://schema.org/NewCondition',
                       'priceCurrency': price.currency,
                       'price': price.net}
        in_stock = variant.is_in_stock()
        if in_stock:
            schema_data['availability'] = 'http://schema.org/InStock'
        else:
            schema_data['availability'] = 'http://schema.org/OutOfStock'

        variant_data = {
            'id': variant.id,
            'availability': in_stock,
            'price': price_as_dict(price),
            'priceUndiscounted': price_as_dict(price_undiscounted),
            'attributes': variant.attributes,
            'priceLocalCurrency': price_as_dict(price_local_currency),
            'schemaData': schema_data}
        data['variants'].append(variant_data)

        for variant_key, variant_value in variant.attributes.items():
            filter_available_variants[int(variant_key)].append(
                int(variant_value))

    for attribute in variant_attributes:
        available_variants = filter_available_variants.get(attribute.pk, None)

        if available_variants:
            data['variantAttributes'].append({
                'pk': attribute.pk,
                'name': attribute.name,
                'slug': attribute.slug,
                'values': [
                    {'pk': value.pk, 'name': value.name, 'slug': value.slug}
                    for value in attribute.values.filter(
                        pk__in=available_variants)]})

    data['availability'] = {
        'discount': price_as_dict(availability.discount),
        'priceRange': price_range_as_dict(availability.price_range),
        'priceRangeUndiscounted': price_range_as_dict(
            availability.price_range_undiscounted),
        'priceRangeLocalCurrency': price_range_as_dict(
            availability.price_range_local_currency)}
    return data


def get_product_attributes_data(product):
    attributes = product.product_type.product_attributes.all()
    attributes_map = {attribute.pk: attribute for attribute in attributes}
    values_map = get_attributes_display_map(product, attributes)
    return {attributes_map.get(attr_pk): value_obj
            for (attr_pk, value_obj) in values_map.items()}


def price_as_dict(price):
    if not price:
        return None
    return {'currency': price.currency,
            'gross': price.gross,
            'grossLocalized': prices_i18n.gross(price),
            'net': price.net,
            'netLocalized': prices_i18n.net(price)}


def price_range_as_dict(price_range):
    if not price_range:
        return None
    return {'maxPrice': price_as_dict(price_range.max_price),
            'minPrice': price_as_dict(price_range.min_price)}


def get_variant_url_from_product(product, attributes):
    return '%s?%s' % (product.get_absolute_url(), urlencode(attributes))


def get_variant_url(variant):
    attributes = {}
    values = {}
    for attribute in variant.product.product_type.variant_attributes.all():
        attributes[str(attribute.pk)] = attribute
        for value in attribute.values.all():
            values[str(value.pk)] = value

    return get_variant_url_from_product(variant.product, attributes)


def get_attributes_display_map(obj, attributes):
    display_map = {}
    for attribute in attributes:
        value = obj.attributes.get(smart_text(attribute.pk))
        if value:
            choices = {smart_text(a.pk): a for a in attribute.values.all()}
            choice_obj = choices.get(value)
            if choice_obj:
                display_map[attribute.pk] = choice_obj
            else:
                display_map[attribute.pk] = value
    return display_map


def get_product_availability_status(product):
    from .models import Stock

    is_available = product.is_available()
    has_stock_records = Stock.objects.filter(variant__product=product)
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
    if not has_stock_records:
        return ProductAvailabilityStatus.NOT_CARRIED
    if not is_in_stock:
        return ProductAvailabilityStatus.OUT_OF_STOCK
    if not are_all_variants_in_stock:
        return ProductAvailabilityStatus.LOW_STOCK
    if not is_available and product.available_on is not None:
        return ProductAvailabilityStatus.NOT_YET_AVAILABLE
    return ProductAvailabilityStatus.READY_FOR_PURCHASE


def get_variant_availability_status(variant):
    has_stock_records = variant.stock.exists()
    if not has_stock_records:
        return VariantAvailabilityStatus.NOT_CARRIED
    if not variant.is_in_stock():
        return VariantAvailabilityStatus.OUT_OF_STOCK
    return VariantAvailabilityStatus.AVAILABLE


def get_product_costs_data(product):
    zero_price = Price(0, 0, currency=settings.DEFAULT_CURRENCY)
    zero_price_range = PriceRange(zero_price, zero_price)
    purchase_costs_range = zero_price_range
    gross_margin = (0, 0)

    if not product.variants.exists():
        return purchase_costs_range, gross_margin

    variants = product.variants.all()
    costs, margins = get_cost_data_from_variants(variants)

    if costs:
        purchase_costs_range = PriceRange(min(costs), max(costs))
    if margins:
        gross_margin = (margins[0], margins[-1])
    return purchase_costs_range, gross_margin


def sort_cost_data(costs, margins):
    costs = sorted(costs, key=lambda x: x.gross)
    margins = sorted(margins)
    return costs, margins


def get_cost_data_from_variants(variants):
    costs = []
    margins = []
    for variant in variants:
        costs_data = get_variant_costs_data(variant)
        costs += costs_data['costs']
        margins += costs_data['margins']
    return sort_cost_data(costs, margins)


def get_variant_costs_data(variant):
    costs = []
    margins = []
    for stock in variant.stock.all():
        costs.append(get_cost_price(stock))
        margin = get_margin_for_variant(stock)
        if margin:
            margins.append(margin)
    costs = sorted(costs, key=lambda x: x.gross)
    margins = sorted(margins)
    return {'costs': costs, 'margins': margins}


def get_cost_price(stock):
    zero_price = Price(0, 0, currency=settings.DEFAULT_CURRENCY)
    if not stock.cost_price:
        return zero_price
    return stock.cost_price


def get_margin_for_variant(stock):
    if not stock.cost_price:
        return None
    price = stock.variant.get_price_per_item()
    margin = price - stock.cost_price
    percent = round((margin.gross / price.gross) * 100, 0)
    return percent


def allocate_stock(stock, quantity):
    stock.quantity_allocated = F('quantity_allocated') + quantity
    stock.save(update_fields=['quantity_allocated'])


def deallocate_stock(stock, quantity):
    stock.quantity_allocated = F('quantity_allocated') - quantity
    stock.save(update_fields=['quantity_allocated'])


def increase_stock(stock, quantity):
    stock.quantity = F('quantity') + quantity
    stock.save(update_fields=['quantity'])


def decrease_stock(stock, quantity):
    stock.quantity = F('quantity') - quantity
    stock.quantity_allocated = F('quantity_allocated') - quantity
    stock.save(update_fields=['quantity', 'quantity_allocated'])


def get_product_list_context(request, filter_set):
    """
    :param request: request object
    :param filter_set: filter set for product list
    :return: context dictionary
    """
    # Avoiding circular dependency
    from .filters import SORT_BY_FIELDS
    products_paginated = get_paginator_items(
        filter_set.qs, settings.PAGINATE_BY, request.GET.get('page'))
    products_and_availability = list(products_with_availability(
        products_paginated, request.discounts, request.currency))
    now_sorted_by = get_now_sorted_by(filter_set)
    arg_sort_by = request.GET.get('sort_by')
    is_descending = arg_sort_by.startswith('-') if arg_sort_by else False
    return {
        'filter_set': filter_set,
        'products': products_and_availability,
        'products_paginated': products_paginated,
        'sort_by_choices': SORT_BY_FIELDS,
        'now_sorted_by': now_sorted_by,
        'is_descending': is_descending}
