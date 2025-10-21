import itertools
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from prices import Money

from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.pricing.interface import LineInfo
from ..core.taxes import zero_money
from ..core.tracing import traced_atomic_transaction
from ..discount import VoucherType
from ..discount.interface import (
    VariantPromotionRuleInfo,
    fetch_variant_rules_info,
    fetch_voucher_info,
)
from ..shipping.interface import ShippingMethodData
from ..shipping.utils import (
    convert_checkout_delivery_to_shipping_method_data,
    initialize_shipping_method_active_status,
)
from ..warehouse import WarehouseClickAndCollectOption
from ..warehouse.models import Warehouse
from .lock_objects import checkout_qs_select_for_update
from .models import Checkout, CheckoutDelivery, CheckoutLine

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..channel.models import Channel
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

        # if price_override is set, it takes precedence over any other price for
        # further calculations
        if self.line.price_override is not None:
            return Money(self.line.price_override, self.line.currency)

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
    collection_point: Optional["Warehouse"] = None
    voucher: Optional["Voucher"] = None
    voucher_code: Optional["VoucherCode"] = None
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME
    pregenerated_payloads_for_excluded_shipping_method: dict | None = None

    allow_sync_webhooks: bool = True

    @cached_property
    def valid_pick_up_points(self) -> Iterable["Warehouse"]:
        from .utils import get_valid_collection_points_for_checkout

        return list(
            get_valid_collection_points_for_checkout(
                self.lines, self.channel.id, quantity_check=False
            )
        )

    def get_delivery_method_info(self) -> "DeliveryMethodBase":
        delivery_method: ShippingMethodData | Warehouse | None = None

        if assigned_sm := self.checkout.assigned_delivery:
            delivery_method = convert_checkout_delivery_to_shipping_method_data(
                assigned_sm
            )
            return ShippingMethodInfo(delivery_method, self.shipping_address)

        delivery_method = self.collection_point
        if delivery_method is not None:
            return CollectionPointInfo(delivery_method, delivery_method.address)

        return DeliveryMethodBase()

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

    def get_details_for_conversion_to_order(self) -> dict[str, Any]:
        return {"shipping_method_name": None}


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
        return self.delivery_method.active

    def get_details_for_conversion_to_order(self) -> dict[str, str | int | None]:
        details: dict[str, str | int | None] = {
            "shipping_method_name": str(self.delivery_method.name)
        }
        if not self.delivery_method.is_external:
            details["shipping_method_id"] = int(self.delivery_method.id)

        if self.delivery_method.tax_class:
            details["shipping_tax_class_id"] = self.delivery_method.tax_class.id
            details["shipping_tax_class_name"] = str(
                self.delivery_method.tax_class.name
            )
            details["shipping_tax_class_private_metadata"] = (
                self.delivery_method.tax_class.private_metadata
            )
            details["shipping_tax_class_metadata"] = (
                self.delivery_method.tax_class.metadata
            )
        return details


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
        valid_delivery_methods = checkout_info.valid_pick_up_points
        return bool(
            valid_delivery_methods and self.delivery_method in valid_delivery_methods
        )

    def get_details_for_conversion_to_order(self) -> dict[str, Any]:
        return {
            "collection_point_name": str(self.delivery_method),
            "collection_point": self.delivery_method,
        }


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
    voucher: Optional["Voucher"] = None,
    voucher_code: Optional["VoucherCode"] = None,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> CheckoutInfo:
    """Fetch checkout as CheckoutInfo object."""
    from .utils import get_voucher_for_checkout

    channel = checkout.channel
    tax_configuration = channel.tax_configuration
    shipping_address = checkout.shipping_address

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


# FIXME: Maciek: On main, we have different implementation. Needs to rebase first,
# Then replace with the new objects
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


# FIXME: Maciek: Rename to cc realted or extend with new model
def update_delivery_method_lists_for_checkout_info(
    checkout_info: "CheckoutInfo",
    collection_point: Optional["Warehouse"],
    shipping_address: Optional["Address"],
    lines: list[CheckoutLineInfo],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    # Update checkout info fields with new data
    checkout_info.collection_point = collection_point
    checkout_info.shipping_address = shipping_address
    checkout_info.lines = lines

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


@allow_writer()
def fetch_shipping_methods_for_checkout(
    checkout_info: "CheckoutInfo",
) -> list[CheckoutDelivery]:
    """Fetch shipping methods for the checkout.

    Fetches all available shipping methods, both built-in and external, for the given
    checkout. Each method is returned as a CheckoutDelivery instance. Existing
    shipping methods in the database are updated or removed as needed, while the
    checkout's currently assigned shipping method (`assigned_delivery`) is
    always preserved, even if it is no longer available.
    """
    checkout = checkout_info.checkout

    built_in_shipping_methods_dict: dict[int, ShippingMethodData] = {
        int(shipping_method.id): shipping_method
        for shipping_method in get_available_built_in_shipping_methods_for_checkout_info(
            checkout_info=checkout_info
        )
    }
    external_shipping_methods_dict: dict[str, ShippingMethodData] = {
        shipping_method.id: shipping_method
        for shipping_method in get_external_shipping_methods_for_checkout_info(
            checkout_info=checkout_info
        )
    }
    all_methods = list(built_in_shipping_methods_dict.values()) + list(
        external_shipping_methods_dict.values()
    )
    excluded_methods = checkout_info.manager.excluded_shipping_methods_for_checkout(
        checkout,
        checkout_info.channel,
        all_methods,
        checkout_info.pregenerated_payloads_for_excluded_shipping_method,
    )
    initialize_shipping_method_active_status(all_methods, excluded_methods)

    checkout_deliveries = {}

    for shipping_method_data in all_methods:
        tax_class_details = {}
        if shipping_method_data.tax_class:
            tax_class_details = {
                "tax_class_id": shipping_method_data.tax_class.id,
                "tax_class_name": shipping_method_data.tax_class.name,
                "tax_class_metadata": shipping_method_data.tax_class.metadata,
                "tax_class_private_metadata": shipping_method_data.tax_class.private_metadata,
            }
        sm_is_external = shipping_method_data.is_external
        built_in_shipping_method_id = (
            int(shipping_method_data.id) if not sm_is_external else None
        )
        external_shipping_method_id = (
            shipping_method_data.id if sm_is_external else None
        )
        checkout_deliveries[shipping_method_data.id] = CheckoutDelivery(
            checkout=checkout,
            external_shipping_method_id=external_shipping_method_id,
            built_in_shipping_method_id=built_in_shipping_method_id,
            name=shipping_method_data.name or "",
            description=shipping_method_data.description,
            price_amount=shipping_method_data.price.amount,
            currency=shipping_method_data.price.currency,
            maximum_delivery_days=shipping_method_data.maximum_delivery_days,
            minimum_delivery_days=shipping_method_data.minimum_delivery_days,
            metadata=shipping_method_data.metadata,
            private_metadata=shipping_method_data.private_metadata,
            active=shipping_method_data.active,
            message=shipping_method_data.message,
            is_valid=True,
            is_external=sm_is_external,
            **tax_class_details,
        )

    with traced_atomic_transaction():
        locked_checkout = (
            checkout_qs_select_for_update().filter(token=checkout.token).first()
        )
        if not locked_checkout:
            return []
        if locked_checkout.assigned_delivery_id != checkout.assigned_delivery_id:
            return []

        checkout.shipping_methods_stale_at = (
            timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
        )
        checkout.save(update_fields=["shipping_methods_stale_at"])

        exclude_from_delete = Q(
            built_in_shipping_method_id__in=built_in_shipping_methods_dict.keys()
        ) | Q(external_shipping_method_id__in=external_shipping_methods_dict.keys())

        if assigned_delivery := checkout.assigned_delivery:
            if (
                assigned_delivery.built_in_shipping_method_id
                and assigned_delivery.built_in_shipping_method_id
                not in built_in_shipping_methods_dict.keys()
            ):
                exclude_from_delete |= Q(
                    built_in_shipping_method_id=assigned_delivery.built_in_shipping_method_id
                )
                assigned_delivery.is_valid = False
                assigned_delivery.save(update_fields=["is_valid"])
            elif (
                assigned_delivery.external_shipping_method_id
                and assigned_delivery.external_shipping_method_id
                not in external_shipping_methods_dict.keys()
            ):
                exclude_from_delete |= Q(
                    external_shipping_method_id=assigned_delivery.external_shipping_method_id
                )
                assigned_delivery.is_valid = False
                assigned_delivery.save(update_fields=["is_valid"])

        CheckoutDelivery.objects.filter(
            checkout_id=checkout.pk,
        ).exclude(exclude_from_delete).delete()

        if checkout_deliveries:
            CheckoutDelivery.objects.bulk_create(
                checkout_deliveries.values(),
                update_conflicts=True,
                unique_fields=[
                    "checkout_id",
                    "external_shipping_method_id",
                    "built_in_shipping_method_id",
                ],
                update_fields=[
                    "name",
                    "description",
                    "price_amount",
                    "currency",
                    "maximum_delivery_days",
                    "minimum_delivery_days",
                    "metadata",
                    "private_metadata",
                    "active",
                    "message",
                    "updated_at",
                    "is_valid",
                    "is_external",
                    "tax_class_id",
                    "tax_class_name",
                    "tax_class_metadata",
                    "tax_class_private_metadata",
                ],
            )

    if checkout_deliveries:
        return list(
            CheckoutDelivery.objects.filter(
                checkout_id=checkout.pk,
                is_valid=True,
            )
        )
    return []


def get_or_fetch_checkout_deliveries(
    checkout_info: "CheckoutInfo",
) -> list[CheckoutDelivery]:
    """Get or fetch shipping methods for the checkout.

    If the checkout's shipping methods are stale or missing, fetch and update them.
    Otherwise, return the existing valid shipping methods.
    """
    checkout = checkout_info.checkout
    if (
        checkout.shipping_methods_stale_at is None
        or checkout.shipping_methods_stale_at <= timezone.now()
    ):
        return fetch_shipping_methods_for_checkout(checkout_info)
    return list(
        CheckoutDelivery.objects.filter(
            checkout_id=checkout.pk,
            is_valid=True,
        )
    )
