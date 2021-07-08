import itertools
from dataclasses import dataclass
from functools import singledispatch
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union

from prices import TaxedMoney

from saleor.warehouse import WarehouseClickAndCollectOption

from ..core.prices import quantize_price
from ..core.taxes import zero_taxed_money
from ..shipping.models import ShippingMethod, ShippingMethodChannelListing
from ..warehouse.models import Warehouse

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..discount import DiscountInfo
    from ..plugins.manager import PluginsManager
    from ..product.models import (
        Collection,
        Product,
        ProductType,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from .models import Checkout, CheckoutLine


@dataclass
class CheckoutLineInfo:
    line: "CheckoutLine"
    variant: "ProductVariant"
    channel_listing: "ProductVariantChannelListing"
    product: "Product"
    product_type: "ProductType"
    collections: List["Collection"]


@dataclass
class CheckoutInfo:
    checkout: "Checkout"
    user: Optional["User"]
    channel: "Channel"
    billing_address: Optional["Address"]
    shipping_address: Optional["Address"]
    shipping_method: Optional["ShippingMethod"]  # Will be deprecated
    delivery_method_info: "EmptyDeliveryMethod"
    valid_shipping_methods: List["ShippingMethod"]
    valid_pick_up_points: List["Warehouse"]
    shipping_method_channel_listings: Optional[ShippingMethodChannelListing]

    @property
    def valid_delivery_methods(self) -> List[Union["ShippingMethod", "Warehouse"]]:
        return list(
            itertools.chain(self.valid_shipping_methods, self.valid_pick_up_points)
        )

    def get_country(self) -> str:
        address = self.shipping_address or self.billing_address
        if address is None or not address.country:
            return self.checkout.country.code
        return address.country.code

    def get_customer_email(self) -> str:
        return self.user.email if self.user else self.checkout.email


@dataclass(frozen=True)
class EmptyDeliveryMethod:
    delivery_method: Optional[Union["ShippingMethod", "Warehouse"]] = None
    shipping_address: Optional["Address"] = None
    order_key: str = "shipping_method"

    @property
    def warehouse_pk(self) -> Optional[str]:
        pass

    @property
    def is_local_collection_point(self) -> bool:
        return False

    def get_warehouse_filter_lookup(self) -> Dict[str, Any]:
        return {}

    def calculate_checkout_shipping(
        self, checkout_info: "CheckoutInfo", lines=None
    ) -> TaxedMoney:
        return zero_taxed_money(checkout_info.checkout.currency)

    def is_valid_delivery_method(self) -> bool:
        return False

    def is_method_in_valid_methods(self, _) -> bool:
        return False

    def update_channel_listings(self, checkout_info: "CheckoutInfo") -> None:
        pass


@dataclass(frozen=True)
class ShippingMethodInfo(EmptyDeliveryMethod):
    delivery_method: "ShippingMethod"
    shipping_address: Optional["Address"]
    order_key: str = "shipping_method"

    def calculate_checkout_shipping(self, checkout_info, lines=None) -> TaxedMoney:
        """Return checkout shipping price."""
        # FIXME: Optimize checkout.is_shipping_required
        # Copied from base_calculation due to circular imports

        shipping_method = self.delivery_method

        if lines is not None and all(
            isinstance(line, CheckoutLineInfo) for line in lines
        ):
            from .utils import is_shipping_required

            shipping_required = is_shipping_required(lines)
        else:
            shipping_required = checkout_info.checkout.is_shipping_required()

            if not shipping_method or not shipping_required:
                return zero_taxed_money(checkout_info.checkout.currency)

        shipping_price = shipping_method.channel_listings.get(
            channel_id=checkout_info.checkout.channel_id,
        ).get_total()

        return quantize_price(
            TaxedMoney(net=shipping_price, gross=shipping_price),
            shipping_price.currency,
        )

    def is_valid_delivery_method(self) -> bool:
        if not self.shipping_address:
            return False
        return True

    def is_method_in_valid_methods(self, checkout_info: "CheckoutInfo") -> bool:
        valid_delivery_methods = checkout_info.valid_delivery_methods
        return bool(
            valid_delivery_methods and self.delivery_method in valid_delivery_methods
        )

    def update_channel_listings(self, checkout_info: "CheckoutInfo") -> None:
        checkout_info.shipping_method_channel_listings = (
            ShippingMethodChannelListing.objects.filter(
                shipping_method=self.delivery_method, channel=checkout_info.channel
            ).first()
        )


@dataclass(frozen=True)
class CollectionPointInfo(EmptyDeliveryMethod):
    delivery_method: "Warehouse"
    shipping_address: Optional["Address"]
    order_key: str = "collection_point"

    @property
    def warehouse_pk(self):
        return self.delivery_method.pk

    @property
    def is_local_collection_point(self):
        return (
            self.delivery_method.click_and_collect_option
            == WarehouseClickAndCollectOption.LOCAL_STOCK
        )

    def get_warehouse_filter_lookup(self) -> Dict[str, Any]:
        return (
            {"warehouse__pk": self.delivery_method.pk}
            if self.is_local_collection_point
            else {}
        )

    def calculate_checkout_shipping(
        self, checkout_info: "CheckoutInfo", lines=None
    ) -> TaxedMoney:
        return zero_taxed_money(checkout_info.checkout.currency)

    def is_valid_delivery_method(self) -> bool:
        return (
            self.shipping_address == self.delivery_method.address
            if self.shipping_address is not None
            else True
        )

    def is_method_in_valid_methods(self, _) -> bool:
        # TODO: We "pass" this requirement, due to the fact,
        # that in valid collection_points we check quantity.
        # We want to raise "Insufficient Stock" later
        # (or made up weaker requirement, without quantity check)
        return True


@singledispatch
def build_delivery_method(
    delivery_method: Optional[Union["ShippingMethod", "Warehouse"]],
    address=Optional["Address"],
) -> EmptyDeliveryMethod:
    raise NotImplementedError("Incompatible Type")


@build_delivery_method.register(ShippingMethod)
def _(delivery_method, address):
    return ShippingMethodInfo(delivery_method, address)


@build_delivery_method.register(Warehouse)  # type: ignore[no-redef]
def _(delivery_method, _):
    return CollectionPointInfo(delivery_method, delivery_method.address)


@build_delivery_method.register(type(None))  # type: ignore[no-redef]
def _(delivery_method, address):
    return EmptyDeliveryMethod()


def fetch_checkout_lines(checkout: "Checkout") -> Iterable[CheckoutLineInfo]:
    """Fetch checkout lines as CheckoutLineInfo objects."""
    lines = checkout.lines.prefetch_related(
        "variant__product__collections",
        "variant__channel_listings__channel",
        "variant__product__product_type",
    )
    lines_info = []

    for line in lines:
        variant = line.variant
        product = variant.product
        product_type = product.product_type
        collections = list(product.collections.all())

        variant_channel_listing = None
        for channel_listing in line.variant.channel_listings.all():
            if channel_listing.channel_id == checkout.channel_id:
                variant_channel_listing = channel_listing

        # FIXME: Temporary solution to pass type checks. Figure out how to handle case
        # when variant channel listing is not defined for a checkout line.
        if not variant_channel_listing:
            continue

        lines_info.append(
            CheckoutLineInfo(
                line=line,
                variant=variant,
                channel_listing=variant_channel_listing,
                product=product,
                product_type=product_type,
                collections=collections,
            )
        )
    return lines_info


def fetch_checkout_info(
    checkout: "Checkout",
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
) -> CheckoutInfo:
    """Fetch checkout as CheckoutInfo object."""

    channel = checkout.channel
    shipping_address = checkout.shipping_address
    shipping_method = checkout.shipping_method
    shipping_channel_listings = ShippingMethodChannelListing.objects.filter(
        shipping_method=shipping_method, channel=channel
    ).first()
    delivery_method = checkout.collection_point or shipping_method
    delivery_method_info = build_delivery_method(delivery_method, shipping_address)
    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        shipping_method=shipping_method,
        delivery_method_info=delivery_method_info,
        shipping_method_channel_listings=shipping_channel_listings,
        valid_shipping_methods=[],
        valid_pick_up_points=[],
    )

    valid_shipping_methods = get_valid_shipping_method_list_for_checkout_info(
        checkout_info, shipping_address, lines, discounts, manager
    )
    valid_pick_up_points = get_valid_collection_points_for_checkout_info(
        checkout_info, lines
    )
    checkout_info.valid_shipping_methods = valid_shipping_methods
    checkout_info.valid_pick_up_points = valid_pick_up_points
    checkout_info.delivery_method_info = delivery_method_info

    return checkout_info


def update_checkout_info_shipping_address(
    checkout_info: CheckoutInfo,
    address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
):
    checkout_info.shipping_address = address
    valid_methods = get_valid_shipping_method_list_for_checkout_info(
        checkout_info, address, lines, discounts, manager
    )
    checkout_info.valid_shipping_methods = valid_methods
    delivery_method = checkout_info.delivery_method_info.delivery_method
    checkout_info.delivery_method_info = build_delivery_method(delivery_method, address)


def get_valid_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
):
    from .utils import get_valid_shipping_methods_for_checkout

    country_code = shipping_address.country.code if shipping_address else None
    subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, discounts
    )
    valid_shipping_method = get_valid_shipping_methods_for_checkout(
        checkout_info, lines, subtotal, country_code=country_code
    )
    valid_shipping_method = (
        list(valid_shipping_method) if valid_shipping_method is not None else []
    )
    return valid_shipping_method


def get_valid_collection_points_for_checkout_info(
    checkout_info: "CheckoutInfo",
    lines: Iterable[CheckoutLineInfo],
):
    from .utils import get_valid_collection_points_for_checkout

    valid_collection_points = get_valid_collection_points_for_checkout(lines)
    return list(valid_collection_points) if valid_collection_points is not None else []


def update_checkout_info_shipping_method(
    checkout_info: CheckoutInfo, shipping_method: Optional["ShippingMethod"]
):
    checkout_info.shipping_method = shipping_method
    checkout_info.shipping_method_channel_listings = (
        (
            ShippingMethodChannelListing.objects.filter(
                shipping_method=shipping_method, channel=checkout_info.channel
            ).first()
        )
        if shipping_method
        else None
    )


def update_checkout_info_delivery_method(
    checkout_info: CheckoutInfo,
    delivery_method: Optional[Union["ShippingMethod", "Warehouse"]],
):
    checkout_info.delivery_method_info = build_delivery_method(
        delivery_method, checkout_info.shipping_address
    )
    checkout_info.delivery_method_info.update_channel_listings(checkout_info)
