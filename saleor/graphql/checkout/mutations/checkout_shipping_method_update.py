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
from ....checkout.utils import (
    is_shipping_required,
)
from ....shipping import interface as shipping_interface
from ....shipping import models as shipping_models
from ....shipping.utils import convert_to_shipping_method_data
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
from ..types import Checkout
from .utils import (
    ERROR_DOES_NOT_SHIP,
    assign_delivery_method_to_checkout,
    clean_delivery_method,
    get_checkout,
)

if TYPE_CHECKING:
    from ....plugins.manager import PluginsManager


class CheckoutShippingMethodUpdate(BaseMutation):
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
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        )
        shipping_method_id = graphene.ID(
            required=False, default_value=None, description="Shipping method."
        )

    class Meta:
        description = "Updates the shipping method of the checkout."
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                description=(
                    "Triggered when updating the checkout shipping method with "
                    "the external one."
                ),
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            ),
        ]

    @staticmethod
    def _resolve_delivery_method_type(id_) -> str | None:
        if id_ is None:
            return None

        possible_types = ("ShippingMethod", APP_ID_PREFIX)
        type_, id_ = from_global_id_or_error(id_)
        str_type = str(type_)

        if str_type not in possible_types:
            raise ValidationError(
                {
                    "shipping_method_id": ValidationError(
                        "ID does not belong to known shipping methods",
                        code=CheckoutErrorCode.INVALID.value,
                    )
                }
            )

        return str_type

    @staticmethod
    def _check_delivery_method(
        checkout_info, lines, delivery_method: shipping_interface.ShippingMethodData
    ) -> None:
        delivery_method_is_valid = clean_delivery_method(
            checkout_info=checkout_info,
            method=delivery_method,
        )
        if not delivery_method_is_valid:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "This shipping method is not applicable.",
                        code=CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )

    @classmethod
    def get_built_in_shipping_method_as_delivery_method_data(
        cls,
        checkout_info,
        shipping_method_id,
        info: ResolveInfo,
    ) -> shipping_interface.ShippingMethodData:
        shipping_method: shipping_models.ShippingMethod = cls.get_node_or_error(
            info,
            shipping_method_id,
            only_type=ShippingMethod,
            field="shipping_method_id",
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
                    "shipping_method": ValidationError(
                        "Shipping method not found for this channel.",
                        code=CheckoutErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return convert_to_shipping_method_data(shipping_method, listing)

    @classmethod
    def get_external_shipping_method_as_delivery_method_data(
        cls,
        checkout_info: CheckoutInfo,
        shipping_method_id: str,
        manager: "PluginsManager",
    ):
        delivery_method = manager.get_shipping_method(
            checkout=checkout_info.checkout,
            channel_slug=checkout_info.channel.slug,
            shipping_method_id=shipping_method_id,
        )
        if delivery_method is None:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "This shipping method is not applicable.",
                        code=CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )
        return delivery_method

    @classmethod
    def get_delivery_method_data(
        cls,
        checkout_info: CheckoutInfo,
        lines_info: list[CheckoutLineInfo],
        shipping_method_id: str,
        manager: "PluginsManager",
        info: ResolveInfo,
    ) -> shipping_interface.ShippingMethodData | None:
        if shipping_method_id is None:
            return None

        type_name = cls._resolve_delivery_method_type(shipping_method_id)
        if type_name == "ShippingMethod":
            delivery_method_data = (
                cls.get_built_in_shipping_method_as_delivery_method_data(
                    checkout_info, shipping_method_id, info
                )
            )
        else:
            delivery_method_data = (
                cls.get_external_shipping_method_as_delivery_method_data(
                    checkout_info, shipping_method_id, manager
                )
            )

        if delivery_method_data:
            cls._check_delivery_method(checkout_info, lines_info, delivery_method_data)

        return delivery_method_data

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        checkout_id=None,
        id=None,
        shipping_method_id=None,
        token=None,
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

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
        checkout_info = fetch_checkout_info(checkout, lines, manager)
        if use_legacy_error_flow_for_checkout and not is_shipping_required(lines):
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        ERROR_DOES_NOT_SHIP,
                        code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED.value,
                    )
                }
            )
        delivery_method_data = cls.get_delivery_method_data(
            checkout_info, lines, shipping_method_id, manager, info
        )
        assign_delivery_method_to_checkout(
            checkout_info,
            lines,
            manager,
            delivery_method_data,
        )
        return CheckoutShippingMethodUpdate(
            checkout=SyncWebhookControlContext(checkout_info.checkout)
        )
