from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Optional, Tuple, Union

from prices import TaxedMoney, TaxedMoneyRange

from saleor.graphql.core.types import MoneyRange
from saleor.product.models import Product, ProductVariant

from ...core.utils import to_local_currency
from ...discount import DiscountInfo
from ...extensions.manager import get_extensions_manager
from .. import ProductAvailabilityStatus, VariantAvailabilityStatus

if TYPE_CHECKING:
    from django.db.models.query import QuerySet

    from ...extensions.manager import ExtensionsManager


@dataclass
class ProductAvailability:
    available: bool
    on_sale: bool
    price_range: TaxedMoneyRange
    price_range_undiscounted: TaxedMoneyRange
    discount: Optional[TaxedMoney]
    price_range_local_currency: Optional[TaxedMoneyRange]
    discount_local_currency: Optional[TaxedMoneyRange]


@dataclass
class VariantAvailability:
    available: bool
    on_sale: bool
    price: TaxedMoney
    price_undiscounted: TaxedMoney
    discount: Optional[TaxedMoney]
    price_local_currency: Optional[TaxedMoney]
    discount_local_currency: Optional[TaxedMoney]


def products_with_availability(
    products: "QuerySet[Product]",
    discounts,
    country: str,
    local_currency: str,
    extensions: "ExtensionsManager",
):
    for product in products:
        yield (
            product,
            get_product_availability(
                product, discounts, country, local_currency, extensions=extensions
            ),
        )


def get_product_availability_status(product: "Product") -> ProductAvailabilityStatus:
    is_visible = product.is_visible
    are_all_variants_in_stock = all(
        variant.is_in_stock() for variant in product.variants.all()
    )
    is_in_stock = any(variant.is_in_stock() for variant in product.variants.all())
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


def get_variant_availability_status(
    variant: ProductVariant
) -> VariantAvailabilityStatus:
    if not variant.is_in_stock():
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


def get_product_availability(
    product: Product,
    discounts: Iterable[DiscountInfo] = None,
    country: Optional[str] = None,
    local_currency: Optional[str] = None,
    extensions: Optional["ExtensionsManager"] = None,
) -> ProductAvailability:

    if not extensions:
        extensions = get_extensions_manager()
    discounted_net_range = product.get_price_range(discounts=discounts)
    undiscounted_net_range = product.get_price_range()
    discounted = TaxedMoneyRange(
        start=extensions.apply_taxes_to_product(
            product, discounted_net_range.start, country
        ),
        stop=extensions.apply_taxes_to_product(
            product, discounted_net_range.stop, country
        ),
    )
    undiscounted = TaxedMoneyRange(
        start=extensions.apply_taxes_to_product(
            product, undiscounted_net_range.start, country
        ),
        stop=extensions.apply_taxes_to_product(
            product, undiscounted_net_range.stop, country
        ),
    )

    discount = _get_total_discount_from_range(undiscounted, discounted)
    price_range_local, discount_local_currency = _get_product_price_range(
        discounted, undiscounted, local_currency
    )

    is_on_sale = product.is_visible and discount is not None

    return ProductAvailability(
        available=product.is_available,
        on_sale=is_on_sale,
        price_range=discounted,
        price_range_undiscounted=undiscounted,
        discount=discount,
        price_range_local_currency=price_range_local,
        discount_local_currency=discount_local_currency,
    )


def get_variant_availability(
    variant: ProductVariant,
    discounts: Iterable[DiscountInfo] = None,
    country: Optional[str] = None,
    local_currency: Optional[str] = None,
    extensions: Optional["ExtensionsManager"] = None,
) -> VariantAvailability:

    if not extensions:
        extensions = get_extensions_manager()
    discounted = extensions.apply_taxes_to_product(
        variant.product, variant.get_price(discounts=discounts), country
    )
    undiscounted = extensions.apply_taxes_to_product(
        variant.product, variant.get_price(), country
    )

    discount = _get_total_discount(undiscounted, discounted)

    if local_currency:
        price_local_currency = to_local_currency(discounted, local_currency)
        discount_local_currency = to_local_currency(discount, local_currency)
    else:
        price_local_currency = None
        discount_local_currency = None

    is_on_sale = variant.is_visible and discount is not None

    return VariantAvailability(
        available=variant.is_available,
        on_sale=is_on_sale,
        price=discounted,
        price_undiscounted=undiscounted,
        discount=discount,
        price_local_currency=price_local_currency,
        discount_local_currency=discount_local_currency,
    )
