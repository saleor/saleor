from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Optional, Tuple, Union

import opentracing
from django.conf import settings
from prices import MoneyRange, TaxedMoney, TaxedMoneyRange

from saleor.product.models import Collection, Product, ProductVariant

from ...core.utils import to_local_currency
from ...discount import DiscountInfo
from ...discount.utils import calculate_discounted_price
from ...plugins.manager import get_plugins_manager
from ...warehouse.availability import (
    are_all_product_variants_in_stock,
    is_product_in_stock,
    is_variant_in_stock,
)
from .. import ProductAvailabilityStatus, VariantAvailabilityStatus

if TYPE_CHECKING:
    # flake8: noqa
    from ...plugins.manager import PluginsManager


@dataclass
class ProductAvailability:
    on_sale: bool
    price_range: TaxedMoneyRange
    price_range_undiscounted: TaxedMoneyRange
    discount: Optional[TaxedMoney]
    price_range_local_currency: Optional[TaxedMoneyRange]
    discount_local_currency: Optional[TaxedMoneyRange]


@dataclass
class VariantAvailability:
    on_sale: bool
    price: TaxedMoney
    price_undiscounted: TaxedMoney
    discount: Optional[TaxedMoney]
    price_local_currency: Optional[TaxedMoney]
    discount_local_currency: Optional[TaxedMoney]


def get_product_availability_status(
    product: "Product", country: str
) -> ProductAvailabilityStatus:
    is_visible = product.is_visible
    are_all_variants_in_stock = are_all_product_variants_in_stock(product, country)
    is_in_stock = is_product_in_stock(product, country)
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
    if not is_visible and product.publication_date is not None:
        return ProductAvailabilityStatus.NOT_YET_AVAILABLE
    return ProductAvailabilityStatus.READY_FOR_PURCHASE


def get_variant_availability_status(variant, country):
    if not is_variant_in_stock(variant, country):
        return VariantAvailabilityStatus.OUT_OF_STOCK
    return VariantAvailabilityStatus.AVAILABLE


def _get_total_discount_from_range(
    undiscounted: TaxedMoneyRange, discounted: TaxedMoneyRange
) -> Optional[TaxedMoney]:
    """Calculate the discount amount between two TaxedMoneyRange.

    Subtract two prices and return their total discount, if any.
    Otherwise, it returns None.
    """
    return _get_total_discount(undiscounted.start, discounted.start)


def _get_total_discount(
    undiscounted: TaxedMoney, discounted: TaxedMoney
) -> Optional[TaxedMoney]:
    """Calculate the discount amount between two TaxedMoney.

    Subtract two prices and return their total discount, if any.
    Otherwise, it returns None.
    """
    if undiscounted > discounted:
        return undiscounted - discounted
    return None


def _get_product_price_range(
    discounted: Union[MoneyRange, TaxedMoneyRange],
    undiscounted: Union[MoneyRange, TaxedMoneyRange],
    local_currency: Optional[str] = None,
) -> Tuple[TaxedMoneyRange, TaxedMoney]:
    price_range_local = None
    discount_local_currency = None

    if local_currency:
        price_range_local = to_local_currency(discounted, local_currency)
        undiscounted_local = to_local_currency(undiscounted, local_currency)
        if undiscounted_local and undiscounted_local.start > price_range_local.start:
            discount_local_currency = undiscounted_local.start - price_range_local.start

    return price_range_local, discount_local_currency


def get_variant_base_price(*, variant: ProductVariant, product: Product):
    return (
        variant.price_override if variant.price_override is not None else product.price
    )


def get_variant_price(
    *,
    variant: ProductVariant,
    product: Product,
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo]
):
    return calculate_discounted_price(
        product=product,
        price=get_variant_base_price(variant=variant, product=product),
        collections=collections,
        discounts=discounts,
    )


def get_product_price_range(
    *,
    product: Product,
    variants: Iterable[ProductVariant],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo]
) -> MoneyRange:
    with opentracing.global_tracer().start_active_span("get_product_price_range"):
        if variants:
            prices = [
                get_variant_price(
                    variant=variant,
                    product=product,
                    collections=collections,
                    discounts=discounts,
                )
                for variant in variants
            ]
            return MoneyRange(min(prices), max(prices))
        price = calculate_discounted_price(
            product=product,
            price=product.price,
            collections=collections,
            discounts=discounts,
        )
        return MoneyRange(start=price, stop=price)


def get_product_availability(
    *,
    product: Product,
    variants: Iterable[ProductVariant],
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
    country: Optional[str] = None,
    local_currency: Optional[str] = None,
    plugins: Optional["PluginsManager"] = None,
) -> ProductAvailability:
    with opentracing.global_tracer().start_active_span("get_product_availability"):
        if not plugins:
            plugins = get_plugins_manager()
        discounted_net_range = get_product_price_range(
            product=product,
            variants=variants,
            collections=collections,
            discounts=discounts,
        )
        undiscounted_net_range = get_product_price_range(
            product=product, variants=variants, collections=collections, discounts=[]
        )
        discounted = TaxedMoneyRange(
            start=plugins.apply_taxes_to_product(
                product, discounted_net_range.start, country
            ),
            stop=plugins.apply_taxes_to_product(
                product, discounted_net_range.stop, country
            ),
        )
        undiscounted = TaxedMoneyRange(
            start=plugins.apply_taxes_to_product(
                product, undiscounted_net_range.start, country
            ),
            stop=plugins.apply_taxes_to_product(
                product, undiscounted_net_range.stop, country
            ),
        )

        discount = _get_total_discount_from_range(undiscounted, discounted)
        price_range_local, discount_local_currency = _get_product_price_range(
            discounted, undiscounted, local_currency
        )

        is_on_sale = product.is_visible and discount is not None
        return ProductAvailability(
            on_sale=is_on_sale,
            price_range=discounted,
            price_range_undiscounted=undiscounted,
            discount=discount,
            price_range_local_currency=price_range_local,
            discount_local_currency=discount_local_currency,
        )


def get_variant_availability(
    variant: ProductVariant,
    product: Product,
    collections: Iterable[Collection],
    discounts: Iterable[DiscountInfo],
    country: Optional[str] = None,
    local_currency: Optional[str] = None,
    plugins: Optional["PluginsManager"] = None,
) -> VariantAvailability:
    with opentracing.global_tracer().start_active_span("get_variant_availability"):
        if not plugins:
            plugins = get_plugins_manager()
        discounted = plugins.apply_taxes_to_product(
            product,
            get_variant_price(
                variant=variant,
                product=product,
                collections=collections,
                discounts=discounts,
            ),
            country,
        )
        undiscounted = plugins.apply_taxes_to_product(
            product,
            get_variant_price(
                variant=variant, product=product, collections=collections, discounts=[]
            ),
            country,
        )

        discount = _get_total_discount(undiscounted, discounted)

        if country is None:
            country = settings.DEFAULT_COUNTRY

        if local_currency:
            price_local_currency = to_local_currency(discounted, local_currency)
            discount_local_currency = to_local_currency(discount, local_currency)
        else:
            price_local_currency = None
            discount_local_currency = None

        is_on_sale = product.is_visible and discount is not None

        return VariantAvailability(
            on_sale=is_on_sale,
            price=discounted,
            price_undiscounted=undiscounted,
            discount=discount,
            price_local_currency=price_local_currency,
            discount_local_currency=discount_local_currency,
        )
