import graphene
from django.core.exceptions import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    CheckoutInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
    get_or_fetch_checkout_deliveries,
)
from ....checkout.models import CheckoutDelivery
from ....checkout.utils import (
    is_shipping_required,
)
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
    def _resolve_delivery_method_id(id_) -> str | None:
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

        return id_

    @classmethod
    def get_checkout_delivery(
        cls, checkout_info: CheckoutInfo, shipping_method_id: str | None
    ) -> CheckoutDelivery | None:
        if shipping_method_id is None:
            return None
        checkout_deliveries = get_or_fetch_checkout_deliveries(checkout_info)
        internal_shipping_method_id = cls._resolve_delivery_method_id(
            shipping_method_id
        )
        if internal_shipping_method_id is None:
            return None

        for method in checkout_deliveries:
            if not method.active:
                continue
            if method.shipping_method_id == internal_shipping_method_id:
                return method

        raise ValidationError(
            {
                "shipping_method": ValidationError(
                    "This shipping method is not applicable.",
                    code=CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
                )
            }
        )

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

        checkout_delivery = cls.get_checkout_delivery(checkout_info, shipping_method_id)
        assign_delivery_method_to_checkout(
            checkout_info,
            lines,
            manager,
            checkout_delivery,
        )
        return CheckoutShippingMethodUpdate(
            checkout=SyncWebhookControlContext(checkout_info.checkout)
        )
