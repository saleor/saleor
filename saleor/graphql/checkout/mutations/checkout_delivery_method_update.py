from typing import TYPE_CHECKING

import graphene
from django.core.exceptions import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
    get_or_fetch_checkout_deliveries,
)
from ....checkout.models import CheckoutDelivery
from ....checkout.utils import is_shipping_required
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
from ..types import Checkout
from .utils import (
    ERROR_DOES_NOT_SHIP,
    assign_delivery_method_to_checkout,
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
    def get_collection_point(
        cls,
        checkout_info: CheckoutInfo,
        internal_delivery_method_id: str,
    ) -> warehouse_models.Warehouse:
        collection_point = (
            warehouse_models.Warehouse.objects.select_related("address")
            .filter(pk=internal_delivery_method_id)
            .first()
        )
        if (
            not collection_point
            or collection_point not in checkout_info.valid_pick_up_points
        ):
            error_msg = "This pick up point is not applicable."
            raise ValidationError(
                {
                    "delivery_method_id": ValidationError(
                        error_msg,
                        code=CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )
        return collection_point

    @staticmethod
    def _resolve_delivery_method_type(id_) -> tuple[str | None, str | None]:
        if id_ is None:
            return None, None

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

        return str_type, id_

    @classmethod
    def get_checkout_delivery(
        cls, checkout_info: CheckoutInfo, internal_shipping_method_id: str | None
    ) -> CheckoutDelivery | None:
        if internal_shipping_method_id is None:
            return None

        checkout_deliveries = get_or_fetch_checkout_deliveries(checkout_info)
        for method in checkout_deliveries:
            if not method.active:
                continue
            if method.shipping_method_id == internal_shipping_method_id:
                return method

        raise ValidationError(
            {
                "delivery_method_id": ValidationError(
                    "This shipping method is not applicable.",
                    code=CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.value,
                )
            }
        )

    @classmethod
    def get_delivery_method_data(
        cls,
        checkout_info: CheckoutInfo,
        lines_info: list[CheckoutLineInfo],
        delivery_method_id: str,
        manager: "PluginsManager",
        info: ResolveInfo,
    ) -> CheckoutDelivery | warehouse_models.Warehouse | None:
        if delivery_method_id is None:
            return None

        delivery_method_data: CheckoutDelivery | warehouse_models.Warehouse | None = (
            None
        )
        type_name, internal_id = cls._resolve_delivery_method_type(delivery_method_id)
        if internal_id is None:
            return None
        if type_name == "Warehouse":
            delivery_method_data = cls.get_collection_point(checkout_info, internal_id)
        else:
            delivery_method_data = cls.get_checkout_delivery(checkout_info, internal_id)
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
