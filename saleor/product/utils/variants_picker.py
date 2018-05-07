from collections import defaultdict

from django_prices.templatetags import prices_i18n

from ...core.utils import to_local_currency
from ...core.utils.taxes import display_gross_prices, get_tax_rate_by_name
from ...seo.schema.product import variant_json_ld
from .availability import get_availability


def get_variant_picker_data(
        product, discounts=None, taxes=None, local_currency=None):
    availability = get_availability(product, discounts, taxes, local_currency)
    variants = product.variants.all()
    data = {'variantAttributes': [], 'variants': []}

    variant_attributes = product.product_type.variant_attributes.all()

    # Collect only available variants
    filter_available_variants = defaultdict(list)

    for variant in variants:
        price = variant.get_price(discounts, taxes)
        price_undiscounted = variant.get_price(taxes=taxes)
        if local_currency:
            price_local_currency = to_local_currency(price, local_currency)
        else:
            price_local_currency = None
        in_stock = variant.is_in_stock()
        schema_data = variant_json_ld(price, variant, in_stock)
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
        'taxRate': get_tax_rate_by_name(product.tax_rate, taxes),
        'priceRange': price_range_as_dict(availability.price_range),
        'priceRangeUndiscounted': price_range_as_dict(
            availability.price_range_undiscounted),
        'priceRangeLocalCurrency': price_range_as_dict(
            availability.price_range_local_currency)}
    data['priceDisplay'] = {
        'displayGross': display_gross_prices(),
        'handleTaxes': bool(taxes)}
    return data


def price_as_dict(price):
    if price is None:
        return None
    return {
        'currency': price.currency,
        'gross': price.gross.amount,
        'grossLocalized': prices_i18n.amount(price.gross),
        'net': price.net.amount,
        'netLocalized': prices_i18n.amount(price.net)}


def price_range_as_dict(price_range):
    if not price_range:
        return None
    return {
        'maxPrice': price_as_dict(price_range.start),
        'minPrice': price_as_dict(price_range.stop)}
