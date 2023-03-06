import itertools
from dataclasses import dataclass
from functools import singledispatch
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)

from django.utils.functional import SimpleLazyObject

from ..discount import DiscountInfo, VoucherType
from ..discount.interface import fetch_voucher_info
from ..discount.utils import fetch_active_discounts
from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethod, ShippingMethodChannelListing
from ..shipping.utils import (
    convert_to_shipping_method_data,
    initialize_shipping_method_active_status,
)
from ..warehouse import WarehouseClickAndCollectOption
from ..warehouse.models import Warehouse

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..discount.interface import VoucherInfo
    from ..discount.models import Voucher
    from ..plugins.manager import PluginsManager
    from ..product.models import (
        Collection,
        Product,
        ProductChannelListing,
        ProductType,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from ..tax.models import TaxClass, TaxConfiguration
    from .models import Checkout, CheckoutLine


@dataclass
class CheckoutLineInfo:
    line: "CheckoutLine"
    variant: "ProductVariant"
    channel_listing: "ProductVariantChannelListing"
    product: "Product"
    product_type: "ProductType"
    collections: List["Collection"]
    tax_class: Optional["TaxClass"] = None
    voucher: Optional["Voucher"] = None


@dataclass
class CheckoutInfo:
    checkout: "Checkout"
    user: Optional["User"]
    channel: "Channel"
    billing_address: Optional["Address"]
    shipping_address: Optional["Address"]
    delivery_method_info: "DeliveryMethodBase"
    all_shipping_methods: List["ShippingMethodData"]
    tax_configuration: "TaxConfiguration"
    valid_pick_up_points: List["Warehouse"]
    voucher: Optional["Voucher"] = None

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

    def get_customer_email(self) -> Optional[str]:
        return self.user.email if self.user else self.checkout.email


@dataclass(frozen=True)
class DeliveryMethodBase:
    delivery_method: Optional[Union["ShippingMethodData", "Warehouse"]] = None
    shipping_address: Optional["Address"] = None
    store_as_customer_address: bool = False

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
    store_as_customer_address: bool = True

    @property
    def delivery_method_name(self) -> Dict[str, Optional[str]]:
        return {"shipping_method_name": str(self.delivery_method.name)}

    @property
    def delivery_method_order_field(self) -> dict:
        if not self.delivery_method.is_external:
            return {"shipping_method_id": int(self.delivery_method.id)}
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
        return {"collection_point_name": str(self.delivery_method)}

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
    delivery_method: Optional[Union["ShippingMethodData", "Warehouse", Callable]],
    address: Optional["Address"] = None,
) -> DeliveryMethodBase:
    if callable(delivery_method):
        delivery_method = delivery_method()
    if delivery_method is None:
        return DeliveryMethodBase()
    if isinstance(delivery_method, ShippingMethodData):
        return ShippingMethodInfo(delivery_method, address)
    if isinstance(delivery_method, Warehouse):
        return CollectionPointInfo(delivery_method, delivery_method.address)

    raise NotImplementedError()


def fetch_checkout_lines(
    checkout: "Checkout",
    prefetch_variant_attributes=False,
    skip_lines_with_unavailable_variants=True,
) -> Tuple[Iterable[CheckoutLineInfo], Iterable[int]]:
    """Fetch checkout lines as CheckoutLineInfo objects."""
    from .utils import get_voucher_for_checkout

    select_related_fields = ["variant__product__product_type__tax_class"]
    prefetch_related_fields = [
        "variant__product__collections",
        "variant__product__channel_listings__channel",
        "variant__product__product_type__tax_class__country_rates",
        "variant__product__tax_class__country_rates",
        "variant__channel_listings__channel",
    ]
    if prefetch_variant_attributes:
        prefetch_related_fields.extend(
            [
                "variant__attributes__assignment__attribute",
                "variant__attributes__values",
            ]
        )
    lines = checkout.lines.select_related(*select_related_fields).prefetch_related(
        *prefetch_related_fields
    )
    lines_info = []
    unavailable_variant_pks = []
    product_channel_listing_mapping: Dict[int, Optional["ProductChannelListing"]] = {}

    for line in lines:
        variant = line.variant
        product = variant.product
        product_type = product.product_type
        collections = list(product.collections.all())

        variant_channel_listing = _get_variant_channel_listing(
            variant, checkout.channel_id
        )

        if not _is_variant_valid(
            checkout, product, variant_channel_listing, product_channel_listing_mapping
        ):
            unavailable_variant_pks.append(variant.pk)
            if not skip_lines_with_unavailable_variants:
                lines_info.append(
                    CheckoutLineInfo(
                        line=line,
                        variant=variant,
                        channel_listing=variant_channel_listing,
                        product=product,
                        product_type=product_type,
                        collections=collections,
                        tax_class=product.tax_class or product_type.tax_class,
                    )
                )
            continue

        lines_info.append(
            CheckoutLineInfo(
                line=line,
                variant=variant,
                channel_listing=variant_channel_listing,
                product=product,
                product_type=product_type,
                collections=collections,
                tax_class=product.tax_class or product_type.tax_class,
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
            return lines_info, unavailable_variant_pks
        if voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order:
            discounts = fetch_active_discounts()
            voucher_info = fetch_voucher_info(voucher)
            apply_voucher_to_checkout_line(
                voucher_info, checkout, lines_info, discounts
            )
    return lines_info, unavailable_variant_pks


def _get_variant_channel_listing(variant: "ProductVariant", channel_id: int):
    variant_channel_listing = None
    for channel_listing in variant.channel_listings.all():
        if channel_listing.channel_id == channel_id:
            variant_channel_listing = channel_listing
    return variant_channel_listing


def _is_variant_valid(
    checkout: "Checkout",
    product: "Product",
    variant_channel_listing: "ProductVariantChannelListing",
    product_channel_listing_mapping: dict,
):
    if not variant_channel_listing or variant_channel_listing.price is None:
        return False

    product_channel_listing = _get_product_channel_listing(
        product_channel_listing_mapping, checkout.channel_id, product
    )

    if (
        not product_channel_listing
        or product_channel_listing.is_available_for_purchase() is False
        or not product_channel_listing.is_visible
    ):
        return False

    return True


def _get_product_channel_listing(
    product_channel_listing_mapping: dict, channel_id: int, product: "Product"
):
    product_channel_listing = product_channel_listing_mapping.get(product.id)
    if product.id not in product_channel_listing_mapping:
        for channel_listing in product.channel_listings.all():  # type: ignore
            if channel_listing.channel_id == channel_id:
                product_channel_listing = channel_listing
        product_channel_listing_mapping[product.id] = product_channel_listing
    return product_channel_listing


def apply_voucher_to_checkout_line(
    voucher_info: "VoucherInfo",
    checkout: "Checkout",
    lines_info: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
):
    """Attach voucher to valid checkout lines info.

    Apply a voucher to checkout line info when the voucher has the type
    SPECIFIC_PRODUCTS or is applied only to the cheapest item.
    """
    from .utils import get_discounted_lines

    voucher = voucher_info.voucher
    discounted_lines_by_voucher: List[CheckoutLineInfo] = []
    if voucher.apply_once_per_order:
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
                price_override=line_info.line.price_override,
            )
            if not cheapest_line or cheapest_line_price > line_price:
                cheapest_line_price = line_price
                cheapest_line = line_info
        if cheapest_line:
            discounted_lines_by_voucher.append(cheapest_line)
    else:
        discounted_lines_by_voucher.extend(
            get_discounted_lines(lines_info, voucher_info)
        )
    for line_info in lines_info:
        if line_info in discounted_lines_by_voucher:
            line_info.voucher = voucher


def fetch_checkout_info(
    checkout: "Checkout",
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Optional[
        Iterable["ShippingMethodChannelListing"]
    ] = None,
    fetch_delivery_methods=True,
) -> CheckoutInfo:
    """Fetch checkout as CheckoutInfo object."""
    from .utils import get_voucher_for_checkout

    channel = checkout.channel
    tax_configuration = channel.tax_configuration
    shipping_address = checkout.shipping_address
    if shipping_channel_listings is None:
        shipping_channel_listings = channel.shipping_method_listings.all()
    voucher = get_voucher_for_checkout(checkout, channel_slug=channel.slug)

    delivery_method_info = get_delivery_method_info(None, shipping_address)
    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        delivery_method_info=delivery_method_info,
        tax_configuration=tax_configuration,
        all_shipping_methods=[],
        valid_pick_up_points=[],
        voucher=voucher,
    )
    if fetch_delivery_methods:
        update_delivery_method_lists_for_checkout_info(
            checkout_info,
            checkout.shipping_method,
            checkout.collection_point,
            shipping_address,
            lines,
            discounts,
            manager,
            shipping_channel_listings,
        )

    return checkout_info


def update_checkout_info_delivery_method_info(
    checkout_info: CheckoutInfo,
    shipping_method: Optional[ShippingMethod],
    collection_point: Optional[Warehouse],
    shipping_channel_listings: Iterable[ShippingMethodChannelListing],
):
    """Update delivery_method_attribute for CheckoutInfo.

    The attribute is lazy-evaluated avoid external API calls unless accessed.
    """
    from ..plugins.webhook.shipping import convert_to_app_id_with_identifier
    from .utils import get_external_shipping_id

    delivery_method: Optional[Union[ShippingMethodData, Warehouse, Callable]] = None
    checkout = checkout_info.checkout
    if shipping_method:
        # Find listing for the currently selected shipping method
        shipping_channel_listing = None
        for listing in shipping_channel_listings:
            if listing.shipping_method_id == shipping_method.id:
                shipping_channel_listing = listing
                break

        delivery_method = convert_to_shipping_method_data(
            shipping_method, shipping_channel_listing
        )

    elif external_shipping_method_id := get_external_shipping_id(checkout):
        # A local function is used to delay evaluation
        # of the lazy `all_shipping_methods` attribute
        def _resolve_external_method():
            methods = {
                method.id: method for method in checkout_info.all_shipping_methods
            }
            if method := methods.get(external_shipping_method_id):
                return method
            new_shipping_method_id = convert_to_app_id_with_identifier(
                external_shipping_method_id
            )
            return methods.get(new_shipping_method_id)

        delivery_method = _resolve_external_method

    else:
        delivery_method = collection_point

    checkout_info.delivery_method_info = SimpleLazyObject(
        lambda: get_delivery_method_info(
            delivery_method,
            checkout_info.shipping_address,
        )
    )  # type: ignore


def update_checkout_info_shipping_address(
    checkout_info: CheckoutInfo,
    address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"],
):
    checkout_info.shipping_address = address

    update_delivery_method_lists_for_checkout_info(
        checkout_info,
        checkout_info.checkout.shipping_method,
        checkout_info.checkout.collection_point,
        address,
        lines,
        discounts,
        manager,
        shipping_channel_listings,
    )


def get_valid_internal_shipping_method_list_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    shipping_channel_listings: Iterable[ShippingMethodChannelListing],
) -> List["ShippingMethodData"]:
    from . import base_calculations
    from .utils import get_valid_internal_shipping_methods_for_checkout

    country_code = shipping_address.country.code if shipping_address else None

    subtotal = base_calculations.base_checkout_subtotal(
        lines,
        checkout_info.channel,
        checkout_info.checkout.currency,
        discounts,
    )

    # if a voucher is applied to shipping, we don't want to subtract the discount amount
    # as some methods based on shipping price may become unavailable,
    # for example, method on which the discount was applied
    is_shipping_voucher = (
        checkout_info.voucher and checkout_info.voucher.type == VoucherType.SHIPPING
    )
    if not is_shipping_voucher:
        subtotal -= checkout_info.checkout.discount

    valid_shipping_methods = get_valid_internal_shipping_methods_for_checkout(
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


def get_all_shipping_methods_list(
    checkout_info,
    shipping_address,
    lines,
    discounts,
    shipping_channel_listings,
    manager,
):
    return list(
        itertools.chain(
            get_valid_internal_shipping_method_list_for_checkout_info(
                checkout_info,
                shipping_address,
                lines,
                discounts,
                shipping_channel_listings,
            ),
            get_valid_external_shipping_method_list_for_checkout_info(
                checkout_info, shipping_address, lines, discounts, manager
            ),
        )
    )


def update_delivery_method_lists_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_method: Optional["ShippingMethod"],
    collection_point: Optional["Warehouse"],
    shipping_address: Optional["Address"],
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable["DiscountInfo"],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable[ShippingMethodChannelListing],
):
    """Update the list of shipping methods for checkout info.

    Shipping methods excluded by Saleor's own business logic are not present
    in the result list.

    Availability of shipping methods according to plugins is indicated
    by the `active` field.
    """

    def _resolve_all_shipping_methods():
        # Fetch all shipping method from all sources, including sync webhooks
        all_methods = get_all_shipping_methods_list(
            checkout_info,
            shipping_address,
            lines,
            discounts,
            shipping_channel_listings,
            manager,
        )
        # Filter shipping methods using sync webhooks
        excluded_methods = manager.excluded_shipping_methods_for_checkout(
            checkout_info.checkout, all_methods
        )
        initialize_shipping_method_active_status(all_methods, excluded_methods)
        return all_methods

    checkout_info.all_shipping_methods = SimpleLazyObject(
        _resolve_all_shipping_methods
    )  # type: ignore
    checkout_info.valid_pick_up_points = SimpleLazyObject(
        lambda: (get_valid_collection_points_for_checkout_info(lines, checkout_info))
    )  # type: ignore
    update_checkout_info_delivery_method_info(
        checkout_info,
        shipping_method,
        collection_point,
        shipping_channel_listings,
    )


def get_valid_collection_points_for_checkout_info(
    lines: Iterable[CheckoutLineInfo],
    checkout_info: CheckoutInfo,
):
    from .utils import get_valid_collection_points_for_checkout

    valid_collection_points = get_valid_collection_points_for_checkout(
        lines, checkout_info.channel.id, quantity_check=False
    )
    return SimpleLazyObject(lambda: list(valid_collection_points))


def update_checkout_info_delivery_method(
    checkout_info: CheckoutInfo,
    delivery_method: Optional[Union["ShippingMethodData", "Warehouse"]],
):
    checkout_info.delivery_method_info = get_delivery_method_info(
        delivery_method, checkout_info.shipping_address
    )
