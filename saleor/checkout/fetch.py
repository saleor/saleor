import itertools
from dataclasses import dataclass
from functools import singledispatch
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Union

from django.utils.encoding import smart_text

from ..discount import DiscountInfo, VoucherType
from ..discount.utils import fetch_active_discounts
from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethodChannelListing
from ..shipping.utils import convert_to_shipping_method_data
from ..warehouse import WarehouseClickAndCollectOption
from ..warehouse.models import Warehouse

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..discount.models import Voucher
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
    voucher: Optional["Voucher"] = None


@dataclass
class CheckoutInfo:
    checkout: "Checkout"
    user: Optional["User"]
    channel: "Channel"
    billing_address: Optional["Address"]
    shipping_address: Optional["Address"]
    delivery_method_info: "DeliveryMethodBase"
    valid_shipping_methods: List["ShippingMethodData"]
    valid_pick_up_points: List["Warehouse"]
    shipping_method_channel_listings: Optional[ShippingMethodChannelListing]

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

    def update_channel_listings(self, checkout_info: "CheckoutInfo") -> None:
        checkout_info.shipping_method_channel_listings = None


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

    def update_channel_listings(self, checkout_info: "CheckoutInfo") -> None:
        if not self.delivery_method.is_external:
            checkout_info.shipping_method_channel_listings = (
                ShippingMethodChannelListing.objects.filter(
                    shipping_method_id=int(self.delivery_method.id),
                    channel=checkout_info.channel,
                ).first()
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


def fetch_checkout_lines(
    checkout: "Checkout", prefetch_variant_attributes=False
) -> Iterable[CheckoutLineInfo]:
    """Fetch checkout lines as CheckoutLineInfo objects."""
    from .utils import get_discounted_lines, get_voucher_for_checkout

    prefetched_fields = [
        "variant__product__collections",
        "variant__channel_listings__channel",
        "variant__product__product_type",
    ]
    if prefetch_variant_attributes:
        prefetched_fields.extend(
            [
                "variant__attributes__assignment__attribute",
                "variant__attributes__values",
            ]
        )
    lines = checkout.lines.prefetch_related(*prefetched_fields)
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
    if checkout.voucher_code and lines_info:
        channel_slug = checkout.channel.slug
        voucher = get_voucher_for_checkout(
            checkout, channel_slug=channel_slug, with_prefetch=True
        )
        if not voucher:
            # in case when voucher is expired, it will be null so no need to apply any
            # discount from voucher
            return lines_info
        if voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order:
            discounted_lines_by_voucher: List[CheckoutLineInfo] = []
            if voucher.apply_once_per_order:
                discounts = fetch_active_discounts()
                channel = checkout.channel
                cheapest_line_price = None
                cheapest_line = None
                for line_info in lines_info:
                    line_price = line_info.variant.get_price(
                        product=line_info.product,
                        collections=line_info.collections,
                        channel=channel,
                        channel_listing=line_info.channel_listing,
                        discounts=discounts,
                    )
                    if not cheapest_line or cheapest_line_price > line_price:
                        cheapest_line_price = line_price
                        cheapest_line = line_info
                if cheapest_line:
                    discounted_lines_by_voucher.append(cheapest_line)
            else:
                discounted_lines_by_voucher.extend(
                    get_discounted_lines(lines_info, voucher)
                )
            for line_info in lines_info:
                if line_info in discounted_lines_by_voucher:
                    line_info.voucher = voucher
    return lines_info


def fetch_checkout_info(
    checkout: "Checkout",
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    *,
    # Ugly hack to disable fetching shipping methods if they aren't needed
    # Preventing multiple redundant and potentially costful API calls in
    # checkout lines add/update/delete mutations
    fetch_delivery_methods: bool = True,
) -> CheckoutInfo:
    """Fetch checkout as CheckoutInfo object."""
    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=checkout.channel,
        billing_address=checkout.billing_address,
        shipping_address=checkout.shipping_address,
        delivery_method_info=DeliveryMethodBase(),
        shipping_method_channel_listings=None,
        valid_shipping_methods=[],
        valid_pick_up_points=[],
    )

    if fetch_delivery_methods:
        populate_checkout_info_shippings(checkout_info, lines, discounts, manager)
        valid_pick_up_points = get_valid_collection_points_for_checkout_info(
            checkout.shipping_address, lines, checkout_info
        )
        checkout_info.valid_pick_up_points = valid_pick_up_points

    return checkout_info


def populate_checkout_info_shippings(
    checkout_info: CheckoutInfo,
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
):
    from .utils import get_external_shipping_id

    checkout = checkout_info.checkout
    channel = checkout_info.channel
    shipping_address = checkout_info.shipping_address
    shipping_method = checkout.shipping_method

    external_shipping_methods = (
        get_valid_external_shipping_method_list_for_checkout_info(
            checkout_info, shipping_address, lines, discounts, manager
        )
    )

    shipping_channel_listings = None
    if shipping_method:
        shipping_channel_listings = ShippingMethodChannelListing.objects.filter(
            shipping_method=shipping_method, channel=channel
        ).first()

        delivery_method: Optional[
            Union["ShippingMethodData", "Warehouse"]
        ] = convert_to_shipping_method_data(shipping_method)
    else:
        delivery_method = checkout.collection_point

    checkout_info.shipping_method_channel_listings = shipping_channel_listings

    if not delivery_method:
        external_shipping_method_id = get_external_shipping_id(checkout)
        if external_shipping_method_id:
            external_shipping_methods_map = {
                external_shipping_method.id: external_shipping_method
                for external_shipping_method in external_shipping_methods
            }
            delivery_method = external_shipping_methods_map.get(
                external_shipping_method_id
            )

    if delivery_method:
        delivery_method_info = get_delivery_method_info(
            delivery_method, shipping_address
        )
        checkout_info.delivery_method_info = delivery_method_info

    valid_shipping_methods: List["ShippingMethodData"] = list(
        itertools.chain(
            get_valid_local_shipping_method_list_for_checkout_info(
                checkout_info, shipping_address, lines, discounts, manager
            ),
            external_shipping_methods,
        )
    )

    checkout_info.valid_shipping_methods = valid_shipping_methods


def update_checkout_info_shipping_address(
    checkout_info: CheckoutInfo,
    address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
):
    checkout_info.shipping_address = address

    valid_shipping_methods: List[
        "ShippingMethodData"
    ] = get_valid_shipping_method_list_for_checkout_info(
        checkout_info, address, lines, discounts, manager
    )

    checkout_info.valid_shipping_methods = valid_shipping_methods

    delivery_method = checkout_info.delivery_method_info.delivery_method
    checkout_info.delivery_method_info = get_delivery_method_info(
        delivery_method, address
    )


def get_valid_local_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
) -> List["ShippingMethodData"]:
    from .utils import get_valid_shipping_methods_for_checkout

    country_code = shipping_address.country.code if shipping_address else None
    subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, discounts
    )
    subtotal -= checkout_info.checkout.discount
    valid_shipping_method = get_valid_shipping_methods_for_checkout(
        checkout_info, lines, subtotal, country_code=country_code
    )

    if valid_shipping_method is None:
        return []

    return [
        convert_to_shipping_method_data(shipping)  # type: ignore
        for shipping in valid_shipping_method
    ]


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


def get_valid_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
) -> List["ShippingMethodData"]:
    return list(
        itertools.chain(
            get_valid_local_shipping_method_list_for_checkout_info(
                checkout_info, shipping_address, lines, discounts, manager
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
    checkout_info.delivery_method_info.update_channel_listings(checkout_info)
