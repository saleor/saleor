from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from prices import Money
from promise import Promise

from ..core.db.connection import (
    allow_writer,
)
from ..core.prices import quantize_price
from ..core.tracing import traced_atomic_transaction
from ..discount import VoucherType
from ..shipping.interface import ExcludedShippingMethod, ShippingMethodData
from ..shipping.models import ShippingMethod, ShippingMethodChannelListing
from ..shipping.utils import (
    convert_shipping_method_data_to_checkout_delivery,
    convert_to_shipping_method_data,
    initialize_shipping_method_active_status,
)
from ..warehouse import WarehouseClickAndCollectOption
from ..warehouse.models import Warehouse
from ..webhook.event_types import WebhookEventAsyncType
from . import base_calculations
from .lock_objects import checkout_qs_select_for_update
from .models import Checkout, CheckoutDelivery, CheckoutLine

if TYPE_CHECKING:
    from ..account.models import Address, User
    from ..app.models import App
    from ..plugins.manager import PluginsManager
    from .fetch import CheckoutInfo, CheckoutLineInfo


PRIVATE_META_APP_SHIPPING_ID = "external_app_shipping_id"


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


def is_shipping_required(lines: list["CheckoutLineInfo"]):
    """Check if shipping is required for given checkout lines."""
    return any(line_info.product_type.is_shipping_required for line_info in lines)


def get_valid_internal_shipping_methods_for_checkout_info(
    checkout_info: "CheckoutInfo",
    subtotal: "Money",
) -> list[ShippingMethodData]:
    if not is_shipping_required(checkout_info.lines):
        return []
    if not checkout_info.shipping_address:
        return []

    country_code = (
        checkout_info.shipping_address.country.code
        if checkout_info.shipping_address
        else None
    )

    shipping_methods = ShippingMethod.objects.using(
        checkout_info.database_connection_name
    ).applicable_shipping_methods_for_instance(
        checkout_info.checkout,
        channel_id=checkout_info.checkout.channel_id,
        price=subtotal,
        shipping_address=checkout_info.shipping_address,
        country_code=country_code,
        lines=checkout_info.lines,
    )

    shipping_channel_listings = ShippingMethodChannelListing.objects.using(
        checkout_info.database_connection_name
    ).filter(
        channel_id=checkout_info.channel.id,
        shipping_method_id__in=[method.pk for method in shipping_methods],
    )

    channel_listings_map = {
        listing.shipping_method_id: listing for listing in shipping_channel_listings
    }

    internal_methods: list[ShippingMethodData] = []
    for method in shipping_methods:
        listing = channel_listings_map.get(method.pk)
        if listing:
            shipping_method_data = convert_to_shipping_method_data(method, listing)
            internal_methods.append(shipping_method_data)

    return internal_methods


def get_valid_collection_points_for_checkout(
    lines: list["CheckoutLineInfo"],
    channel_id: int,
    quantity_check: bool = True,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Return a collection of `Warehouse`s that can be used as a collection point.

    Note that `quantity_check=False` should be used, when stocks quantity will
    be validated in further steps (checkout completion) in order to raise
    'InsufficientProductStock' error instead of 'InvalidShippingError'.
    """
    if not is_shipping_required(lines):
        return []

    line_ids = [line_info.line.id for line_info in lines]
    lines = CheckoutLine.objects.using(database_connection_name).filter(id__in=line_ids)

    return (
        Warehouse.objects.using(
            database_connection_name
        ).applicable_for_click_and_collect(lines, channel_id)
        if quantity_check
        else Warehouse.objects.using(
            database_connection_name
        ).applicable_for_click_and_collect_no_quantity_check(lines, channel_id)
    )


def _remove_external_shipping_from_metadata(checkout: Checkout):
    from .utils import get_checkout_metadata

    metadata = get_checkout_metadata(checkout)
    if not metadata:
        return

    field_deleted = metadata.delete_value_from_private_metadata(
        PRIVATE_META_APP_SHIPPING_ID
    )
    if field_deleted:
        metadata.save(update_fields=["private_metadata"])


def _remove_undiscounted_base_shipping_price(checkout: Checkout):
    if checkout.undiscounted_base_shipping_price_amount:
        checkout.undiscounted_base_shipping_price_amount = Decimal(0)
        return ["undiscounted_base_shipping_price_amount"]
    return []


def _assign_undiscounted_base_shipping_price_to_checkout(
    checkout, checkout_delivery: CheckoutDelivery
):
    current_shipping_price = quantize_price(
        checkout.undiscounted_base_shipping_price, checkout.currency
    )
    new_shipping_price = quantize_price(checkout_delivery.price, checkout.currency)
    if current_shipping_price != new_shipping_price:
        checkout.undiscounted_base_shipping_price_amount = new_shipping_price.amount
        return ["undiscounted_base_shipping_price_amount"]
    return []


def assign_shipping_method_to_checkout(
    checkout: Checkout, checkout_delivery: CheckoutDelivery
) -> list[str]:
    fields_to_update = []
    fields_to_update += remove_click_and_collect_from_checkout(checkout)
    fields_to_update += _assign_undiscounted_base_shipping_price_to_checkout(
        checkout, checkout_delivery
    )
    if checkout.assigned_delivery_id != checkout_delivery.id:
        checkout.assigned_delivery = checkout_delivery
        fields_to_update.append("assigned_delivery_id")

    # make sure that we don't have obsolete data for shipping methods stored in
    # private metadata
    _remove_external_shipping_from_metadata(checkout=checkout)

    if checkout.shipping_method_name != checkout_delivery.name:
        checkout.shipping_method_name = checkout_delivery.name
        fields_to_update.append("shipping_method_name")

    return fields_to_update


def assign_collection_point_to_checkout(
    checkout, collection_point: Warehouse
) -> list[str]:
    fields_to_update = []
    fields_to_update += _remove_undiscounted_base_shipping_price(checkout)
    fields_to_update += remove_shipping_method_from_checkout(checkout)
    if checkout.collection_point_id != collection_point.id:
        checkout.collection_point_id = collection_point.id
        fields_to_update.append("collection_point_id")
    if checkout.shipping_address != collection_point.address:
        checkout.shipping_address = collection_point.address.get_copy()
        checkout.save_shipping_address = False
        fields_to_update.extend(["shipping_address_id", "save_shipping_address"])

    return fields_to_update


def remove_shipping_method_from_checkout(checkout: Checkout) -> list[str]:
    fields_to_update = []
    if checkout.assigned_delivery_id:
        checkout.assigned_delivery_id = None
        fields_to_update.append("assigned_delivery_id")
        if checkout.shipping_method_name is not None:
            checkout.shipping_method_name = None
            fields_to_update.append("shipping_method_name")
    return fields_to_update


def remove_click_and_collect_from_checkout(checkout: Checkout) -> list[str]:
    fields_to_update = []
    if checkout.collection_point_id:
        checkout.collection_point_id = None
        fields_to_update.append("collection_point_id")
        if checkout.shipping_address_id:
            checkout.shipping_address = None
            # reset the save_shipping_address flag to the default value
            checkout.save_shipping_address = True
            fields_to_update.extend(["shipping_address_id", "save_shipping_address"])
    return fields_to_update


def remove_delivery_method_from_checkout(checkout: Checkout) -> list[str]:
    fields_to_update = []
    fields_to_update += _remove_undiscounted_base_shipping_price(checkout)
    fields_to_update += remove_shipping_method_from_checkout(checkout)
    fields_to_update += remove_click_and_collect_from_checkout(checkout)
    return fields_to_update


def clear_cc_delivery_method(
    checkout_info: "CheckoutInfo", save: bool = True
) -> list[str]:
    checkout = checkout_info.checkout
    if checkout.collection_point_id is None:
        return []
    updated_fields = remove_click_and_collect_from_checkout(checkout)

    if "collection_point_id" in updated_fields:
        checkout_info.shipping_address = checkout_info.checkout.shipping_address

    if updated_fields:
        updated_fields.append("last_change")
        if save:
            checkout.safe_update(updated_fields)

    return updated_fields


def _get_refreshed_assigned_delivery_data(
    assigned_delivery: CheckoutDelivery | None,
    built_in_shipping_methods_dict: dict[int, ShippingMethodData],
    external_shipping_methods_dict: dict[str, ShippingMethodData],
) -> ShippingMethodData | None:
    """Get refreshed shipping method data for assigned delivery.

    Returns the updated ShippingMethodData for the assigned delivery method,
    or None if the assigned delivery is no longer valid.
    """
    if not assigned_delivery:
        return None

    if external_shipping_method_id := assigned_delivery.external_shipping_method_id:
        return external_shipping_methods_dict.get(external_shipping_method_id)

    if built_in_shipping_method_id := assigned_delivery.built_in_shipping_method_id:
        return built_in_shipping_methods_dict.get(built_in_shipping_method_id)

    return None


def _refresh_checkout_deliveries(
    checkout: "Checkout",
    assigned_delivery: CheckoutDelivery | None,
    checkout_deliveries: list["CheckoutDelivery"],
    built_in_shipping_methods_dict: dict[int, ShippingMethodData],
    external_shipping_methods_dict: dict[str, ShippingMethodData],
):
    """Refresh checkout deliveries assigned to the checkout.

    It updates the `CheckoutDelivery` instances associated with the checkout, based
    on the shipping methods available for the checkout.
    The non-available shipping methods are removed from the DB, except for the currently
    assigned delivery method, which is always preserved even if it's no longer valid.
    """
    exclude_from_delete = Q(
        built_in_shipping_method_id__in=list(built_in_shipping_methods_dict.keys())
    ) | Q(external_shipping_method_id__in=list(external_shipping_methods_dict.keys()))

    if assigned_delivery:
        # Always preserve the assigned delivery even if it's no longer available
        exclude_from_delete |= Q(pk=assigned_delivery.pk)

        refreshed_delivery_method = _get_refreshed_assigned_delivery_data(
            assigned_delivery,
            built_in_shipping_methods_dict,
            external_shipping_methods_dict,
        )

        # Missing refreshed delivery method means that assigned
        # delivery is no more valid.
        if not refreshed_delivery_method:
            assigned_delivery.is_valid = False
            assigned_delivery.save(update_fields=["is_valid"])

    CheckoutDelivery.objects.filter(
        checkout_id=checkout.pk,
    ).exclude(exclude_from_delete).delete()

    if checkout_deliveries:
        CheckoutDelivery.objects.bulk_create(
            checkout_deliveries,
            update_conflicts=True,
            unique_fields=[
                "checkout_id",
                "external_shipping_method_id",
                "built_in_shipping_method_id",
                "is_valid",
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


def get_available_built_in_shipping_methods_for_checkout_info(
    checkout_info: "CheckoutInfo",
) -> list["ShippingMethodData"]:
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


def _refreshed_assigned_delivery_has_impact_on_prices(
    assigned_delivery: CheckoutDelivery | None,
    built_in_shipping_methods_dict: dict[int, ShippingMethodData],
    external_shipping_methods_dict: dict[str, ShippingMethodData],
) -> bool:
    """Check if refreshed assigned delivery impacts checkout prices.

    If the assigned delivery method has changed in a way that affects pricing,
    such as a change in tax class, price or marking as invalid, this function
    returns True. Otherwise, it doesn't impact prices and returns False.
    """
    if not assigned_delivery:
        return False

    refreshed_delivery_method = _get_refreshed_assigned_delivery_data(
        assigned_delivery,
        built_in_shipping_methods_dict,
        external_shipping_methods_dict,
    )

    if not refreshed_delivery_method:
        return True

    refreshed_tax_class_id = (
        refreshed_delivery_method.tax_class.id
        if refreshed_delivery_method.tax_class
        else None
    )
    # Different tax class can impact on prices
    if refreshed_tax_class_id != assigned_delivery.tax_class_id:
        return True

    # Different price means that assigned delivery is invalid
    if refreshed_delivery_method.price != assigned_delivery.price:
        return True

    return False


def fetch_shipping_methods_for_checkout(
    checkout_info: "CheckoutInfo",
    requestor: Union["App", "User", None],
) -> Promise[list[CheckoutDelivery]]:
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

    def with_external_methods(external_shipping_methods: list[ShippingMethodData]):
        external_shipping_methods_dict: dict[str, ShippingMethodData] = {
            shipping_method.id: shipping_method
            for shipping_method in external_shipping_methods
        }
        all_methods = list(built_in_shipping_methods_dict.values()) + list(
            external_shipping_methods_dict.values()
        )
        # Circular import caused by the current definition of subscription payloads
        # and their usage in webhook/transport layer. Until moving them out from the
        # transport, we will have circular imports.
        from .webhooks.exclude_shipping import excluded_shipping_methods_for_checkout

        allow_replica = not (
            checkout_info.database_connection_name
            == settings.DATABASE_CONNECTION_DEFAULT_NAME
        )

        @allow_writer()
        def with_excluded_methods(excluded_methods: list[ExcludedShippingMethod]):
            initialize_shipping_method_active_status(all_methods, excluded_methods)
            checkout_deliveries = {}

            for shipping_method_data in all_methods:
                checkout_delivery_method = (
                    convert_shipping_method_data_to_checkout_delivery(
                        shipping_method_data, checkout
                    )
                )
                checkout_deliveries[shipping_method_data.id] = checkout_delivery_method

            with traced_atomic_transaction():
                locked_checkout = (
                    checkout_qs_select_for_update().filter(token=checkout.token).first()
                )
                if not locked_checkout:
                    return []
                if (
                    locked_checkout.assigned_delivery_id
                    != checkout.assigned_delivery_id
                ):
                    return []

                assigned_delivery = checkout.assigned_delivery

                checkout.delivery_methods_stale_at = (
                    timezone.now() + settings.CHECKOUT_DELIVERY_OPTIONS_TTL
                )
                checkout.save(update_fields=["delivery_methods_stale_at"])

                _refresh_checkout_deliveries(
                    checkout=locked_checkout,
                    assigned_delivery=assigned_delivery,
                    checkout_deliveries=list(checkout_deliveries.values()),
                    built_in_shipping_methods_dict=built_in_shipping_methods_dict,
                    external_shipping_methods_dict=external_shipping_methods_dict,
                )

                if _refreshed_assigned_delivery_has_impact_on_prices(
                    assigned_delivery,
                    built_in_shipping_methods_dict,
                    external_shipping_methods_dict,
                ):
                    from .utils import invalidate_checkout

                    invalidate_checkout(
                        checkout_info=checkout_info,
                        lines=checkout_info.lines,
                        manager=checkout_info.manager,
                        recalculate_discount=True,
                        save=True,
                    )
            if checkout_deliveries:
                return list(
                    CheckoutDelivery.objects.filter(
                        checkout_id=checkout.pk,
                        is_valid=True,
                    )
                )
            return []

        return excluded_shipping_methods_for_checkout(
            checkout,
            available_shipping_methods=all_methods,
            allow_replica=allow_replica,
            requestor=requestor,
        ).then(with_excluded_methods)

    return fetch_external_shipping_methods_for_checkout_info(
        checkout_info=checkout_info,
        available_built_in_methods=list(built_in_shipping_methods_dict.values()),
        requestor=requestor,
    ).then(with_external_methods)


def fetch_external_shipping_methods_for_checkout_info(
    checkout_info,
    available_built_in_methods: list[ShippingMethodData],
    requestor: Union["App", "User", None],
) -> Promise[list[ShippingMethodData]]:
    from .webhooks.list_shipping_methods import list_shipping_methods_for_checkout

    allow_replica = not (
        checkout_info.database_connection_name
        == settings.DATABASE_CONNECTION_DEFAULT_NAME
    )

    return list_shipping_methods_for_checkout(
        checkout=checkout_info.checkout,
        built_in_shipping_methods=available_built_in_methods,
        allow_replica=allow_replica,
        requestor=requestor,
    )


def get_or_fetch_checkout_deliveries(
    checkout_info: "CheckoutInfo",
    requestor: Union["App", "User", None],
    allow_sync_webhooks: bool = True,
) -> Promise[list[CheckoutDelivery]]:
    """Get or fetch shipping methods for the checkout.

    If the checkout's shipping methods are stale or missing, fetch and update them.
    Otherwise, return the existing valid shipping methods.
    """
    checkout = checkout_info.checkout
    if (
        checkout.delivery_methods_stale_at is None
        or checkout.delivery_methods_stale_at <= timezone.now()
    ) and allow_sync_webhooks:
        return fetch_shipping_methods_for_checkout(checkout_info, requestor=requestor)
    return Promise.resolve(
        list(
            CheckoutDelivery.objects.using(
                checkout_info.database_connection_name
            ).filter(
                checkout_id=checkout.pk,
                is_valid=True,
            )
        )
    )


def assign_delivery_method_to_checkout(
    checkout_info: "CheckoutInfo",
    lines_info: list["CheckoutLineInfo"],
    manager: "PluginsManager",
    delivery_method: CheckoutDelivery | Warehouse | None,
):
    fields_to_update = []
    checkout = checkout_info.checkout
    with transaction.atomic():
        if delivery_method is None:
            fields_to_update = remove_delivery_method_from_checkout(
                checkout=checkout_info.checkout
            )
            checkout_info.collection_point = None
        elif isinstance(delivery_method, CheckoutDelivery):
            fields_to_update = assign_shipping_method_to_checkout(
                checkout, delivery_method
            )
            checkout_info.collection_point = None
        elif isinstance(delivery_method, Warehouse):
            fields_to_update = assign_collection_point_to_checkout(
                checkout, delivery_method
            )
            checkout_info.shipping_address = checkout.shipping_address

        if not fields_to_update:
            return

        from .actions import call_checkout_info_event
        from .utils import invalidate_checkout

        invalidate_prices_updated_fields = invalidate_checkout(
            checkout_info, lines_info, manager, save=False
        )
        checkout.save(update_fields=fields_to_update + invalidate_prices_updated_fields)
        call_checkout_info_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout_info=checkout_info,
            lines=lines_info,
        )
