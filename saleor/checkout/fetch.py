import itertools
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from functools import cached_property, singledispatch
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID

from django.conf import settings
from prices import Money

from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.pricing.interface import LineInfo
from ..core.taxes import zero_money
from ..discount import VoucherType
from ..discount.interface import (
    VariantPromotionRuleInfo,
    fetch_variant_rules_info,
    fetch_voucher_info,
)
from ..shipping.interface import ShippingMethodData
from ..shipping.models import ShippingMethod, ShippingMethodChannelListing
from ..shipping.utils import (
    convert_to_shipping_method_data,
    initialize_shipping_method_active_status,
)
from ..warehouse import WarehouseClickAndCollectOption
from ..warehouse.models import Warehouse
from ..webhook.transport.shipping_helpers import convert_to_app_id_with_identifier

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
    from ..checkout.models import CheckoutLine
    from ..discount.models import (
        CheckoutDiscount,
        CheckoutLineDiscount,
        Voucher,
        VoucherCode,
    )
    from ..plugins.manager import PluginsManager
    from ..product.models import (
        Product,
        ProductChannelListing,
        ProductType,
        ProductVariant,
        ProductVariantChannelListing,
    )
    from ..tax.models import TaxClass, TaxConfiguration
    from .models import Checkout


@dataclass
class CheckoutLineInfo(LineInfo):
    line: "CheckoutLine"
    variant: "ProductVariant"
    product: "Product"
    product_type: "ProductType"
    discounts: list["CheckoutLineDiscount"]
    rules_info: list["VariantPromotionRuleInfo"]
    channel_listing: Optional["ProductVariantChannelListing"]

    tax_class: Optional["TaxClass"] = None

    @cached_property
    def variant_discounted_price(self) -> Money:
        """Return the discounted variant price.

        `variant_discounted_price` means price with the most beneficial applicable
        catalogue promotion.
        If listing is present return the discounted price from the listing,
        if listing is not present, calculate current unit price based on
        `undiscounted_unit_price` and catalogue promotion discounts.
        """
        if self.channel_listing and self.channel_listing.discounted_price is not None:
            return self.channel_listing.discounted_price
        catalogue_discounts = self.get_catalogue_discounts()
        total_price = self.undiscounted_unit_price * self.line.quantity
        for discount in catalogue_discounts:
            total_price -= discount.amount

        unit_price = max(
            total_price / self.line.quantity, zero_money(self.line.currency)
        )
        return quantize_price(unit_price, self.line.currency)

    @cached_property
    def undiscounted_unit_price(self) -> Money:
        """Provide undiscounted unit price.

        Return the undiscounted variant price when listing is present. If variant
        doesn't have listing, use denormalized price.
        """
        if self.channel_listing and self.channel_listing.price is not None:
            return self.variant.get_base_price(
                self.channel_listing, self.line.price_override
            )
        return self.line.undiscounted_unit_price

    @cached_property
    def prior_unit_price_amount(self) -> Decimal | None:
        """Provide prior unit price."""
        if self.channel_listing and self.channel_listing.price is not None:
            return self.variant.get_prior_price_amount(self.channel_listing)
        return self.line.prior_unit_price_amount


@dataclass
class CheckoutInfo:
    manager: "PluginsManager" = field(compare=False)
    checkout: "Checkout"
    user: Optional["User"]
    channel: "Channel"
    billing_address: Optional["Address"]
    shipping_address: Optional["Address"]
    tax_configuration: "TaxConfiguration"
    discounts: list["CheckoutDiscount"]
    lines: list[CheckoutLineInfo]
    shipping_channel_listings: list["ShippingMethodChannelListing"]
    shipping_method: Optional["ShippingMethod"] = None
    collection_point: Optional["Warehouse"] = None
    voucher: Optional["Voucher"] = None
    voucher_code: Optional["VoucherCode"] = None
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME
    pregenerated_payloads_for_excluded_shipping_method: dict | None = None

    allow_sync_webhooks: bool = True
    _cached_built_in_shipping_methods: list[ShippingMethodData] | None = None
    _cached_external_shipping_methods: list[ShippingMethodData] | None = None

    def get_all_shipping_methods(
        self,
    ) -> list["ShippingMethodData"]:
        """Return list of all available shipping methods.

        If self.allow_sync_webhooks is set to False, any external calls will be skipped.
        If self.allow_sync_webhooks is set to True, the external calls like: external
        shipping methods or exclude shipping methods will be called.

        The fetched values are stored in self object to remove any additional
        external/DB calls.
        """
        if (
            self._cached_external_shipping_methods is not None
            and self._cached_built_in_shipping_methods is not None
        ):
            return (
                self._cached_built_in_shipping_methods
                + self._cached_external_shipping_methods
            )

        if (
            not self.allow_sync_webhooks
            and self._cached_built_in_shipping_methods is not None
        ):
            return self._cached_built_in_shipping_methods

        if self._cached_built_in_shipping_methods is None:
            self._cached_built_in_shipping_methods = (
                get_available_built_in_shipping_methods_for_checkout_info(self)
            )

        if not self.allow_sync_webhooks:
            excluded_methods = []
            all_methods = self._cached_built_in_shipping_methods
        else:
            self._cached_external_shipping_methods = (
                get_external_shipping_methods_for_checkout_info(self)
            )
            all_methods = (
                self._cached_built_in_shipping_methods
                + self._cached_external_shipping_methods
            )
            # Filter shipping methods using sync webhooks
            excluded_methods = self.manager.excluded_shipping_methods_for_checkout(
                self.checkout,
                self.channel,
                all_methods,
                self.pregenerated_payloads_for_excluded_shipping_method,
            )
        initialize_shipping_method_active_status(all_methods, excluded_methods)
        return all_methods

    @cached_property
    def valid_pick_up_points(self) -> Iterable["Warehouse"]:
        from .utils import get_valid_collection_points_for_checkout

        return list(
            get_valid_collection_points_for_checkout(
                self.lines, self.channel.id, quantity_check=False
            )
        )

    def _update_denormalized_shipping_method_fields(
        self, delivery_method: ShippingMethodData | Warehouse
    ):
        checkout = self.checkout
        fields_to_update = []
        if isinstance(delivery_method, ShippingMethodData):
            new_shipping_method_name = delivery_method.name
            new_shipping_price = delivery_method.price
        else:
            new_shipping_method_name = None
            new_shipping_price = zero_money(checkout.currency)

        if checkout.shipping_method_name != new_shipping_method_name:
            checkout.shipping_method_name = new_shipping_method_name
            fields_to_update.append("shipping_method_name")
        current_shipping_price = quantize_price(
            checkout.undiscounted_base_shipping_price, checkout.currency
        )
        new_shipping_price = quantize_price(new_shipping_price, checkout.currency)
        if current_shipping_price != new_shipping_price:
            checkout.undiscounted_base_shipping_price_amount = new_shipping_price.amount
            fields_to_update.append("undiscounted_base_shipping_price_amount")

        if fields_to_update:
            with allow_writer():
                checkout.save(update_fields=fields_to_update)

    def get_delivery_method_info(self) -> "DeliveryMethodBase":
        from .utils import get_external_shipping_id

        delivery_method: ShippingMethodData | Warehouse | None = None

        if self.shipping_method:
            # Find listing for the currently selected shipping method
            shipping_channel_listing = None
            for listing in self.shipping_channel_listings:
                if listing.shipping_method_id == self.shipping_method.id:
                    shipping_channel_listing = listing
                    break

            if shipping_channel_listing:
                delivery_method = convert_to_shipping_method_data(
                    self.shipping_method, shipping_channel_listing
                )

        elif external_shipping_method_id := get_external_shipping_id(self.checkout):
            if self.allow_sync_webhooks:
                methods = {
                    method.id: method for method in self.get_all_shipping_methods()
                }
                if method := methods.get(external_shipping_method_id):
                    delivery_method = method
                else:
                    new_shipping_method_id = convert_to_app_id_with_identifier(
                        external_shipping_method_id
                    )
                    if new_shipping_method_id is None:
                        delivery_method = None
                    else:
                        delivery_method = methods.get(new_shipping_method_id)
            else:
                delivery_method = ShippingMethodData(
                    id=get_external_shipping_id(self.checkout),
                    name=self.checkout.shipping_method_name or "",
                    price=self.checkout.undiscounted_base_shipping_price,
                )

        else:
            delivery_method = self.collection_point

        if isinstance(delivery_method, ShippingMethodData):
            self._update_denormalized_shipping_method_fields(delivery_method)

        return get_delivery_method_info(delivery_method, self.shipping_address)

    @property
    def valid_shipping_methods(self) -> list["ShippingMethodData"]:
        return [method for method in self.get_all_shipping_methods() if method.active]

    @property
    def valid_delivery_methods(
        self,
    ) -> list[Union["ShippingMethodData", "Warehouse"]]:
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

    def get_customer_email(self) -> str | None:
        if self.checkout.email:
            return self.checkout.email
        if self.user:
            return self.user.email
        return None


@dataclass(frozen=True)
class DeliveryMethodBase:
    delivery_method: Union["ShippingMethodData", "Warehouse"] | None = None
    shipping_address: Optional["Address"] = None
    store_as_customer_address: bool = False

    @property
    def warehouse_pk(self) -> UUID | None:
        pass

    @property
    def delivery_method_order_field(self) -> dict:
        return {"shipping_method": self.delivery_method}

    @property
    def is_local_collection_point(self) -> bool:
        return False

    @property
    def delivery_method_name(self) -> dict[str, str | None]:
        return {"shipping_method_name": None}

    def get_warehouse_filter_lookup(self) -> dict[str, Any]:
        return {}

    def is_valid_delivery_method(self) -> bool:
        return False

    def is_method_in_valid_methods(self, checkout_info: "CheckoutInfo") -> bool:
        return False

    def is_delivery_method_set(self) -> bool:
        return bool(self.delivery_method)


@dataclass(frozen=True)
class ShippingMethodInfo(DeliveryMethodBase):
    delivery_method: "ShippingMethodData"
    shipping_address: Optional["Address"]
    store_as_customer_address: bool = True

    @property
    def delivery_method_name(self) -> dict[str, str | None]:
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
    def delivery_method_name(self) -> dict[str, str | None]:
        return {"collection_point_name": str(self.delivery_method)}

    def get_warehouse_filter_lookup(self) -> dict[str, Any]:
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
    delivery_method: Union["ShippingMethodData", "Warehouse"] | None,
    address: Optional["Address"] = None,
) -> DeliveryMethodBase:
    if delivery_method is None:
        return DeliveryMethodBase()
    if isinstance(delivery_method, ShippingMethodData):
        return ShippingMethodInfo(delivery_method, address)
    if isinstance(delivery_method, Warehouse):
        # TODO: Workaround for lack of using in tests.
        # The warehouse address should be loaded when CheckoutInfo is created.
        with allow_writer():
            return CollectionPointInfo(delivery_method, delivery_method.address)

    raise NotImplementedError()


def fetch_checkout_lines(
    checkout: "Checkout",
    prefetch_variant_attributes: bool = False,
    skip_lines_with_unavailable_variants: bool = True,
    skip_recalculation: bool = False,
    voucher: Optional["Voucher"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple[list[CheckoutLineInfo], list[int]]:
    """Fetch checkout lines as CheckoutLineInfo objects."""
    from ..discount.utils.voucher import attach_voucher_to_line_info
    from .utils import get_voucher_for_checkout

    select_related_fields = ["variant__product__product_type__tax_class"]
    prefetch_related_fields = [
        "variant__product__collections",
        "variant__product__channel_listings__channel",
        "variant__product__product_type__tax_class__country_rates",
        "variant__product__tax_class__country_rates",
        "variant__channel_listings__channel",
        "variant__channel_listings__variantlistingpromotionrule__promotion_rule__promotion__translations",
        "variant__channel_listings__variantlistingpromotionrule__promotion_rule__translations",
        "discounts__promotion_rule__promotion",
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
    product_channel_listing_mapping: dict[int, ProductChannelListing | None] = {}
    channel = checkout.channel

    for line in lines:
        variant = line.variant
        product = variant.product
        product_type = product.product_type
        collections = list(product.collections.all())
        discounts = list(line.discounts.all())

        variant_channel_listing = get_variant_channel_listing(
            variant, checkout.channel_id
        )
        translation_language_code = checkout.language_code
        rules_info = (
            fetch_variant_rules_info(variant_channel_listing, translation_language_code)
            if not line.is_gift
            else []
        )

        if not skip_recalculation and not _is_variant_valid(
            checkout, product, variant_channel_listing, product_channel_listing_mapping
        ):
            unavailable_variant_pks.append(variant.pk)
            lines_info.append(
                CheckoutLineInfo(
                    line=line,
                    variant=variant,
                    channel_listing=variant_channel_listing,
                    product=product,
                    product_type=product_type,
                    collections=collections,
                    tax_class=product.tax_class or product_type.tax_class,
                    discounts=discounts,
                    rules_info=rules_info,
                    channel=channel,
                    voucher=None,
                    voucher_code=None,
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
                discounts=discounts,
                rules_info=rules_info,
                channel=channel,
                voucher=None,
                voucher_code=None,
            )
        )

    if not skip_recalculation and checkout.voucher_code and lines_info:
        if not voucher:
            voucher, _ = get_voucher_for_checkout(
                checkout,
                channel_slug=channel.slug,
                with_prefetch=True,
                database_connection_name=database_connection_name,
            )
        if not voucher:
            # in case when voucher is expired, it will be null so no need to apply any
            # discount from voucher
            return lines_info, unavailable_variant_pks
        if voucher.type == VoucherType.SPECIFIC_PRODUCT or voucher.apply_once_per_order:
            voucher_info = fetch_voucher_info(voucher, checkout.voucher_code)
            attach_voucher_to_line_info(voucher_info, lines_info)
    return lines_info, unavailable_variant_pks


def get_variant_channel_listing(
    variant: "ProductVariant", channel_id: int
) -> Optional["ProductVariantChannelListing"]:
    variant_channel_listing = None
    for channel_listing in variant.channel_listings.all():
        if channel_listing.channel_id == channel_id:
            variant_channel_listing = channel_listing
    return variant_channel_listing


def _product_channel_listing_is_valid(
    checkout: "Checkout",
    product: "Product",
    product_channel_listing_mapping: dict,
):
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


def _is_variant_valid(
    checkout: "Checkout",
    product: "Product",
    variant_channel_listing: Optional["ProductVariantChannelListing"],
    product_channel_listing_mapping: dict,
):
    if not variant_channel_listing or variant_channel_listing.price is None:
        return False

    if not _product_channel_listing_is_valid(
        checkout,
        product,
        product_channel_listing_mapping,
    ):
        return False
    return True


def _get_product_channel_listing(
    product_channel_listing_mapping: dict, channel_id: int, product: "Product"
):
    product_channel_listing = product_channel_listing_mapping.get(product.id)
    if product.id not in product_channel_listing_mapping:
        for channel_listing in product.channel_listings.all():
            if channel_listing.channel_id == channel_id:
                product_channel_listing = channel_listing
        product_channel_listing_mapping[product.id] = product_channel_listing
    return product_channel_listing


def fetch_checkout_info(
    checkout: "Checkout",
    lines: list[CheckoutLineInfo],
    manager: "PluginsManager",
    shipping_channel_listings: Iterable["ShippingMethodChannelListing"] | None = None,
    voucher: Optional["Voucher"] = None,
    voucher_code: Optional["VoucherCode"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> CheckoutInfo:
    """Fetch checkout as CheckoutInfo object."""
    from .utils import get_voucher_for_checkout

    channel = checkout.channel
    tax_configuration = channel.tax_configuration
    shipping_address = checkout.shipping_address
    if shipping_channel_listings is None:
        shipping_channel_listings = channel.shipping_method_listings.all()

    if not voucher or not voucher_code:
        voucher, voucher_code = get_voucher_for_checkout(
            checkout,
            channel_slug=channel.slug,
            database_connection_name=database_connection_name,
        )

    checkout_info = CheckoutInfo(
        checkout=checkout,
        user=checkout.user,
        channel=channel,
        billing_address=checkout.billing_address,
        shipping_address=shipping_address,
        tax_configuration=tax_configuration,
        discounts=list(checkout.discounts.all()),
        lines=lines,
        manager=manager,
        shipping_channel_listings=list(shipping_channel_listings),
        shipping_method=checkout.shipping_method,
        collection_point=checkout.collection_point,
        voucher=voucher,
        voucher_code=voucher_code,
        database_connection_name=database_connection_name,
    )
    return checkout_info


def get_available_built_in_shipping_methods_for_checkout_info(
    checkout_info: "CheckoutInfo",
) -> list["ShippingMethodData"]:
    from . import base_calculations
    from .utils import get_valid_internal_shipping_methods_for_checkout_info

    lines = checkout_info.lines

    subtotal = base_calculations.base_checkout_subtotal(
        lines,
        checkout_info.channel,
        checkout_info.checkout.currency,
    )

    # if a voucher is applied to shipping, we don't want to subtract the discount amount
    # as some methods based on shipping price may become unavailable,
    # for example, method on which the discount was applied
    is_shipping_voucher = (
        checkout_info.voucher and checkout_info.voucher.type == VoucherType.SHIPPING
    )

    is_voucher_for_specific_product = (
        checkout_info.voucher
        and checkout_info.voucher.type == VoucherType.SPECIFIC_PRODUCT
    )

    if not is_shipping_voucher and not is_voucher_for_specific_product:
        subtotal -= checkout_info.checkout.discount

    valid_shipping_methods = get_valid_internal_shipping_methods_for_checkout_info(
        checkout_info,
        subtotal,
    )

    return valid_shipping_methods


def get_external_shipping_methods_for_checkout_info(
    checkout_info,
) -> list[ShippingMethodData]:
    manager = checkout_info.manager
    return manager.list_shipping_methods_for_checkout(
        checkout=checkout_info.checkout, channel_slug=checkout_info.channel.slug
    )


def get_all_shipping_methods_list(
    checkout_info,
):
    return list(
        itertools.chain(
            get_available_built_in_shipping_methods_for_checkout_info(
                checkout_info,
            ),
            get_external_shipping_methods_for_checkout_info(checkout_info),
        )
    )


def update_delivery_method_lists_for_checkout_info(
    checkout_info: "CheckoutInfo",
    shipping_method: Optional["ShippingMethod"],
    collection_point: Optional["Warehouse"],
    shipping_address: Optional["Address"],
    lines: list[CheckoutLineInfo],
    shipping_channel_listings: Iterable[ShippingMethodChannelListing],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    # Update checkout info fields with new data
    checkout_info.shipping_method = shipping_method
    checkout_info.collection_point = collection_point
    checkout_info.shipping_address = shipping_address
    checkout_info.lines = lines
    checkout_info.shipping_channel_listings = list(shipping_channel_listings)

    # Clear cached properties if they were already calculated, so they can be
    # recalculated.
    try:
        del checkout_info._cached_built_in_shipping_methods
        del checkout_info._cached_external_shipping_methods
    except AttributeError:
        pass

    try:
        del checkout_info.valid_pick_up_points
    except AttributeError:
        pass


def find_checkout_line_info(
    lines: list["CheckoutLineInfo"],
    line_id: "UUID",
) -> "CheckoutLineInfo":
    """Return checkout line info from lines parameter.

    The return value represents the updated version of checkout_line_info parameter.
    """
    return next(line_info for line_info in lines if line_info.line.pk == line_id)
