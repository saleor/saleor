from typing import TYPE_CHECKING

import graphene
from django.core.exceptions import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ....checkout.utils import is_shipping_required
from ....shipping import interface as shipping_interface
from ....shipping import models as shipping_models
from ....shipping.interface import ShippingMethodData
from ....shipping.utils import convert_to_shipping_method_data
from ....warehouse import models as warehouse_models
from ....webhook.const import APP_ID_PREFIX
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import WebhookEventInfo, from_global_id_or_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ...shipping.types import ShippingMethod
from ...warehouse.types import Warehouse
from ..types import Checkout
from .utils import (
    ERROR_DOES_NOT_SHIP,
    assign_delivery_method_to_checkout,
    clean_delivery_method,
    get_checkout,
)

if TYPE_CHECKING:
    from ....plugins.manager import PluginsManager


class CheckoutDeliveryMethodUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID.",
            required=False,
        )
        token = UUID(
            description=f"Checkout token.{DEPRECATED_IN_3X_INPUT} Use `id` instead.",
            required=False,
        )

        delivery_method_id = graphene.ID(
            description="Delivery Method ID (`Warehouse` ID or `ShippingMethod` ID).",
            required=False,
        )

    class Meta:
        description = (
            "Updates the delivery method (shipping method or pick up point) "
            "of the checkout. "
            "Updates the checkout shipping_address for click and collect delivery "
            "for a warehouse address. "
        )
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                description=(
                    "Triggered when updating the checkout delivery method with "
                    "the external one."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            ),
        ]

    @classmethod
    def get_collection_point_as_delivery_method_data(
        cls,
        checkout_info: CheckoutInfo,
        delivery_method_id: str,
        info: ResolveInfo,
    ) -> warehouse_models.Warehouse:
        collection_point = cls.get_node_or_error(
            info,
            delivery_method_id,
            only_type=Warehouse,
            field="delivery_method_id",
            qs=warehouse_models.Warehouse.objects.select_related("address"),
        )
        return collection_point

    @classmethod
    def get_built_in_shipping_method_as_delivery_method_data(
        cls,
        checkout_info: CheckoutInfo,
        shipping_method_id: str,
        info: ResolveInfo,
    ) -> ShippingMethodData:
        shipping_method: shipping_models.ShippingMethod = cls.get_node_or_error(
            info,
            shipping_method_id,
            only_type=ShippingMethod,
            field="delivery_method_id",
            qs=shipping_models.ShippingMethod.objects.prefetch_related(
                "postal_code_rules"
            ),
        )

        listing = shipping_models.ShippingMethodChannelListing.objects.filter(
            shipping_method=shipping_method,
            channel=checkout_info.channel,
        ).first()
        if not listing:
            raise ValidationError(
                {
                    "delivery_method_id": ValidationError(
                        "This shipping method is not applicable in the given channel.",
                        code=CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )
        delivery_method = convert_to_shipping_method_data(shipping_method, listing)
        return delivery_method

    @classmethod
    def get_external_shipping_method_as_delivery_method_data(
        cls,
        checkout_info: CheckoutInfo,
        shipping_method_id: str,
        manager: "PluginsManager",
    ) -> ShippingMethodData:
        delivery_method = manager.get_shipping_method(
            checkout=checkout_info.checkout,
            channel_slug=checkout_info.channel.slug,
            shipping_method_id=shipping_method_id,
        )

        if delivery_method is None:
            raise ValidationError(
                {
                    "delivery_method_id": ValidationError(
                        f"Couldn't resolve to a node: ${shipping_method_id}",
                        code=CheckoutErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return delivery_method

    @staticmethod
    def _check_delivery_method(
        checkout_info,
        lines,
        delivery_method_data: ShippingMethodData | warehouse_models.Warehouse,
    ) -> None:
        delivery_method = delivery_method_data
        if isinstance(delivery_method, warehouse_models.Warehouse):
            error_msg = "This pick up point is not applicable."
        else:
            error_msg = "This shipping method is not applicable."

        delivery_method_is_valid = clean_delivery_method(
            checkout_info=checkout_info, method=delivery_method
        )
        if not delivery_method_is_valid:
            raise ValidationError(
                {
                    "delivery_method_id": ValidationError(
                        error_msg,
                        code=CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )

    @staticmethod
    def _resolve_delivery_method_type(id_) -> str | None:
        if id_ is None:
            return None

        possible_types = ("Warehouse", "ShippingMethod", APP_ID_PREFIX)
        type_, id_ = from_global_id_or_error(id_)
        str_type = str(type_)

        if str_type not in possible_types:
            raise ValidationError(
                {
                    "delivery_method_id": ValidationError(
                        "ID does not belong to Warehouse or ShippingMethod",
                        code=CheckoutErrorCode.INVALID.value,
                    )
                }
            )

        return str_type

    @classmethod
    def get_delivery_method_data(
        cls,
        checkout_info: CheckoutInfo,
        lines_info: list[CheckoutLineInfo],
        delivery_method_id: str,
        manager: "PluginsManager",
        info: ResolveInfo,
    ) -> shipping_interface.ShippingMethodData | warehouse_models.Warehouse | None:
        if delivery_method_id is None:
            return None

        delivery_method_data: ShippingMethodData | warehouse_models.Warehouse | None = (
            None
        )
        type_name = cls._resolve_delivery_method_type(delivery_method_id)
        if type_name == "Warehouse":
            delivery_method_data = cls.get_collection_point_as_delivery_method_data(
                checkout_info, delivery_method_id, info
            )
        elif type_name == "ShippingMethod":
            delivery_method_data = (
                cls.get_built_in_shipping_method_as_delivery_method_data(
                    checkout_info, delivery_method_id, info
                )
            )
        elif type_name == APP_ID_PREFIX:
            delivery_method_data = (
                cls.get_external_shipping_method_as_delivery_method_data(
                    checkout_info, delivery_method_id, manager
                )
            )

        if delivery_method_data:
            cls._check_delivery_method(checkout_info, lines_info, delivery_method_data)

        return delivery_method_data

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info,
        /,
        token=None,
        id=None,
        delivery_method_id=None,
    ):
        checkout = get_checkout(cls, info, checkout_id=None, token=token, id=id)

        use_legacy_error_flow_for_checkout = (
            checkout.channel.use_legacy_error_flow_for_checkout
        )

        manager = get_plugin_manager_promise(info.context).get()
        lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        if use_legacy_error_flow_for_checkout and unavailable_variant_pks:
            not_available_variants_ids = {
                graphene.Node.to_global_id("ProductVariant", pk)
                for pk in unavailable_variant_pks
            }
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Some of the checkout lines variants are unavailable.",
                        code=CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value,
                        params={"variants": not_available_variants_ids},
                    )
                }
            )

        if use_legacy_error_flow_for_checkout and not is_shipping_required(lines):
            raise ValidationError(
                {
                    "delivery_method": ValidationError(
                        ERROR_DOES_NOT_SHIP,
                        code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED.value,
                    )
                }
            )
        checkout_info = fetch_checkout_info(checkout, lines, manager)

        delivery_method_data = cls.get_delivery_method_data(
            checkout_info, lines, delivery_method_id, manager, info
        )
        assign_delivery_method_to_checkout(
            checkout_info,
            lines,
            manager,
            delivery_method_data,
        )
        return CheckoutDeliveryMethodUpdate(
            checkout=SyncWebhookControlContext(checkout_info.checkout)
        )
