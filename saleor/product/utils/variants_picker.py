from collections import defaultdict
from decimal import Decimal
from typing import Iterable

from django_prices.templatetags import prices_i18n

from ...core.extensions.manager import get_extensions_manager
from ...core.taxes import display_gross_prices
from ...core.utils import to_local_currency
from ...discount import DiscountInfo
from ...seo.schema.product import variant_json_ld
from .availability import get_product_availability


def get_variant_picker_data(
    product,
    discounts: Iterable[DiscountInfo] = None,
    extensions=None,
    local_currency=None,
    country=None,
):
    if not extensions:
        extensions = get_extensions_manager()
    availability = get_product_availability(
        product, discounts, country, local_currency, extensions
    )
    variants = product.variants.all()
    data = {"variantAttributes": [], "variants": []}

    variant_attributes = product.product_type.variant_attributes.all()

    # Collect only available variants
    filter_available_variants = defaultdict(list)

    for variant in variants:
        price = extensions.apply_taxes_to_product(
            variant.product, variant.get_price(discounts), country
        )
        price_undiscounted = extensions.apply_taxes_to_product(
            variant.product, variant.get_price(), country
        )
        if local_currency:
            price_local_currency = to_local_currency(price, local_currency)
        else:
            price_local_currency = None
        in_stock = variant.is_in_stock()
        schema_data = variant_json_ld(price.net, variant, in_stock)
        variant_data = {
            "id": variant.id,
            "availability": in_stock,
            "price": price_as_dict(price),
            "priceUndiscounted": price_as_dict(price_undiscounted),
            "attributes": variant.attributes,
            "priceLocalCurrency": price_as_dict(price_local_currency),
            "schemaData": schema_data,
        }
        data["variants"].append(variant_data)

        for variant_key, variant_value in variant.attributes.items():
            filter_available_variants[int(variant_key)].append(int(variant_value))

    for attribute in variant_attributes:
        available_variants = filter_available_variants.get(attribute.pk, None)

        if available_variants:
            data["variantAttributes"].append(
                {
                    "pk": attribute.pk,
                    "name": attribute.translated.name,
                    "slug": attribute.translated.slug,
                    "values": [
                        {
                            "pk": value.pk,
                            "name": value.translated.name,
                            "slug": value.translated.slug,
                        }
                        for value in attribute.values.filter(
                            pk__in=available_variants
                        ).prefetch_related("translations")
                    ],
                }
            )

    product_price = extensions.apply_taxes_to_product(product, product.price, country)
    tax_rates = Decimal(0)
    if product_price.tax and product_price.net:
        tax_rates = (product_price.tax / product_price.net) * 100
        tax_rates = tax_rates.quantize(Decimal("1."))

    data["availability"] = {
        "discount": price_as_dict(availability.discount),
        "taxRate": tax_rates,
        "priceRange": price_range_as_dict(availability.price_range),
        "priceRangeUndiscounted": price_range_as_dict(
            availability.price_range_undiscounted
        ),
        "priceRangeLocalCurrency": price_range_as_dict(
            availability.price_range_local_currency
        ),
    }
    data["priceDisplay"] = {
        "displayGross": display_gross_prices(),
        "handleTaxes": extensions.show_taxes_on_storefront(),
    }
    return data


def price_as_dict(price):
    if price is None:
        return None
    return {
        "currency": price.currency,
        "gross": price.gross.amount,
        "grossLocalized": prices_i18n.amount(price.gross),
        "net": price.net.amount,
        "netLocalized": prices_i18n.amount(price.net),
    }


def price_range_as_dict(price_range):
    if not price_range:
        return None
    return {
        "minPrice": price_as_dict(price_range.start),
        "maxPrice": price_as_dict(price_range.stop),
    }
