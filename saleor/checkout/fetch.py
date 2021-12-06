import itertools
from dataclasses import dataclass
from functools import singledispatch
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union

from django.utils.encoding import smart_text

from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethodChannelListing
from ..shipping.utils import convert_to_shipping_method_data
from ..warehouse import WarehouseClickAndCollectOption
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
    delivery_method_info: "DeliveryMethodBase"
    all_shipping_methods: List["ShippingMethodData"]
    valid_pick_up_points: List["Warehouse"]

    @property
    def valid_shipping_methods(self) -> List["ShippingMethodData"]:
        return [method for method in self.all_shipping_methods if method.active]

    @property
    def valid_delivery_methods(
        self,
    ) -> List[Union["ShippingMethodData", "Warehouse"]]:
        return list(
            itertools.chain(
                self.valid_shipping_methods,
                self.valid_pick_up_points,
            )
        )

    def get_country(self) -> str:
        address = self.shipping_address or self.billing_address
        if address is None or not address.country:
            return self.checkout.country.code
        return address.country.code

    def get_customer_email(self) -> str:
        return self.user.email if self.user else self.checkout.email


@dataclass(frozen=True)
class DeliveryMethodBase:
    delivery_method: Optional[Union["ShippingMethodData", "Warehouse"]] = None
    shipping_address: Optional["Address"] = None

    @property
    def warehouse_pk(self) -> Optional[str]:
        pass

    @property
    def delivery_method_order_field(self) -> dict:
        return {"shipping_method": self.delivery_method}

    @property
    def is_local_collection_point(self) -> bool:
        return False

    @property
    def delivery_method_name(self) -> Dict[str, Optional[str]]:
        return {"shipping_method_name": None}

    def get_warehouse_filter_lookup(self) -> Dict[str, Any]:
        return {}

    def is_valid_delivery_method(self) -> bool:
        return False

    def is_method_in_valid_methods(self, checkout_info: "CheckoutInfo") -> bool:
        return False


@dataclass(frozen=True)
class ShippingMethodInfo(DeliveryMethodBase):
    delivery_method: "ShippingMethodData"
    shipping_address: Optional["Address"]

    @property
    def delivery_method_name(self) -> Dict[str, Optional[str]]:
        return {"shipping_method_name": smart_text(self.delivery_method.name)}

    @property
    def delivery_method_order_field(self) -> dict:
        if not self.delivery_method.is_external:
            return {"shipping_method_id": self.delivery_method.id}
        return {}

    def is_valid_delivery_method(self) -> bool:
        return bool(self.shipping_address)

    def is_method_in_valid_methods(self, checkout_info: "CheckoutInfo") -> bool:
        valid_delivery_methods = checkout_info.valid_delivery_methods
        return bool(
            valid_delivery_methods and self.delivery_method in valid_delivery_methods
        )


@dataclass(frozen=True)
class CollectionPointInfo(DeliveryMethodBase):
    delivery_method: "Warehouse"
    shipping_address: Optional["Address"]

    @property
    def warehouse_pk(self):
        return self.delivery_method.pk

    @property
    def delivery_method_order_field(self) -> dict:
        return {"collection_point": self.delivery_method}

    @property
    def is_local_collection_point(self):
        return (
            self.delivery_method.click_and_collect_option
            == WarehouseClickAndCollectOption.LOCAL_STOCK
        )

    @property
    def delivery_method_name(self) -> Dict[str, Optional[str]]:
        return {"collection_point_name": smart_text(self.delivery_method)}

    def get_warehouse_filter_lookup(self) -> Dict[str, Any]:
        return (
            {"warehouse_id": self.delivery_method.pk}
            if self.is_local_collection_point
            else {}
        )

    def is_valid_delivery_method(self) -> bool:
        return (
            self.shipping_address is not None
            and self.shipping_address == self.delivery_method.address
        )

    def is_method_in_valid_methods(self, checkout_info) -> bool:
        valid_delivery_methods = checkout_info.valid_delivery_methods
        return bool(
            valid_delivery_methods and self.delivery_method in valid_delivery_methods
        )


@singledispatch
def get_delivery_method_info(
    delivery_method: Optional[Union["ShippingMethodData", "Warehouse"]],
    address=Optional["Address"],
) -> DeliveryMethodBase:
    if delivery_method is None:
        return DeliveryMethodBase()
    if isinstance(delivery_method, ShippingMethodData):
        return ShippingMethodInfo(delivery_method, address)
    if isinstance(delivery_method, Warehouse):
        return CollectionPointInfo(delivery_method, delivery_method.address)

    raise NotImplementedError()


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
    shipping_channel_listings: Optional[
        Iterable["ShippingMethodChannelListing"]
    ] = None,
) -> CheckoutInfo:
    """Fetch checkout as CheckoutInfo object."""

    from .utils import get_external_shipping_id

    channel = checkout.channel
    shipping_address = checkout.shipping_address
    if shipping_channel_listings is None:
        shipping_channel_listings = channel.shipping_method_listings.all()

    shipping_method = checkout.shipping_method
    shipping_channel_listing = None
    if shipping_method:
        # Find listing for the currently selected shipping method
        for listing in shipping_channel_listings:
            if listing.shipping_method_id == shipping_method.id:
                shipping_channel_listing = listing
                break

        delivery_method: Optional[
            Union["ShippingMethodData", "Warehouse"]
        ] = convert_to_shipping_method_data(shipping_method, shipping_channel_listing)
    else:
        delivery_method = checkout.collection_point

    if not delivery_method:
        external_shipping_method_id = get_external_shipping_id(checkout)
        delivery_method = manager.get_shipping_method(
            checkout=checkout,
            channel_slug=channel.slug,
            shipping_method_id=external_shipping_method_id,
        )

    delivery_method_info = get_delivery_method_info(delivery_method, shipping_address)
    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        delivery_method_info=delivery_method_info,
        all_shipping_methods=[],
        valid_pick_up_points=[],
    )

    all_shipping_methods: List[
        "ShippingMethodData"
    ] = get_shipping_method_list_for_checkout_info(
        checkout_info,
        shipping_address,
        lines,
        discounts,
        manager,
        shipping_channel_listings,
    )

    valid_pick_up_points = get_valid_collection_points_for_checkout_info(
        shipping_address, lines, checkout_info
    )
    checkout_info.all_shipping_methods = all_shipping_methods
    checkout_info.valid_pick_up_points = valid_pick_up_points
    checkout_info.delivery_method_info = delivery_method_info

    return checkout_info


def update_checkout_info_shipping_address(
    checkout_info: CheckoutInfo,
    address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
):
    checkout_info.shipping_address = address

    all_shipping_methods: List[
        "ShippingMethodData"
    ] = get_shipping_method_list_for_checkout_info(
        checkout_info, address, lines, discounts, manager, shipping_channel_listings
    )

    checkout_info.all_shipping_methods = all_shipping_methods

    delivery_method = checkout_info.delivery_method_info.delivery_method
    checkout_info.delivery_method_info = get_delivery_method_info(
        delivery_method, address
    )


def get_valid_saleor_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable[ShippingMethodChannelListing],
) -> List["ShippingMethodData"]:
    from .utils import get_valid_saleor_shipping_methods_for_checkout

    country_code = shipping_address.country.code if shipping_address else None
    subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, discounts
    )
    subtotal -= checkout_info.checkout.discount
    valid_shipping_methods = get_valid_saleor_shipping_methods_for_checkout(
        checkout_info,
        lines,
        subtotal,
        shipping_channel_listings,
        country_code=country_code,
    )

    return valid_shipping_methods


def get_valid_external_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
) -> List["ShippingMethodData"]:

    return manager.list_shipping_methods_for_checkout(
        checkout=checkout_info.checkout, channel_slug=checkout_info.channel.slug
    )


def get_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable[ShippingMethodChannelListing],
) -> List["ShippingMethodData"]:
    return list(
        itertools.chain(
            get_valid_saleor_shipping_method_list_for_checkout_info(
                checkout_info,
                shipping_address,
                lines,
                discounts,
                manager,
                shipping_channel_listings,
            ),
            get_valid_external_shipping_method_list_for_checkout_info(
                checkout_info, shipping_address, lines, discounts, manager
            ),
        )
    )


def get_valid_collection_points_for_checkout_info(
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    checkout_info: CheckoutInfo,
):
    from .utils import get_valid_collection_points_for_checkout

    if shipping_address:
        country_code = shipping_address.country.code
    else:
        country_code = checkout_info.channel.default_country.code

    valid_collection_points = get_valid_collection_points_for_checkout(
        lines, country_code=country_code, quantity_check=False
    )
    return list(valid_collection_points)


def update_checkout_info_delivery_method(
    checkout_info: CheckoutInfo,
    delivery_method: Optional[Union["ShippingMethodData", "Warehouse"]],
):
    checkout_info.delivery_method_info = get_delivery_method_info(
        delivery_method, checkout_info.shipping_address
    )
