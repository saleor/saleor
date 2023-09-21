from typing import Iterable, Optional

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
    delete_external_shipping_id,
    get_or_create_checkout_metadata,
    invalidate_checkout_prices,
    is_shipping_required,
    set_external_shipping_id,
)
from ....shipping import interface as shipping_interface
from ....shipping import models as shipping_models
from ....shipping.utils import convert_to_shipping_method_data
from ....warehouse import models as warehouse_models
from ....webhook.const import APP_ID_PREFIX
from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_31, ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import WebhookEventInfo, from_global_id_or_error
from ...plugins.dataloaders import get_plugin_manager_promise
from ...shipping.types import ShippingMethod
from ...warehouse.types import Warehouse
from ..types import Checkout
from .utils import ERROR_DOES_NOT_SHIP, clean_delivery_method, get_checkout


class CheckoutDeliveryMethodUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
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
            "of the checkout." + ADDED_IN_31
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
    def perform_on_shipping_method(
        cls,
        info: ResolveInfo,
        shipping_method_id,
        checkout_info,
        lines,
        checkout,
        manager,
    ):
        shipping_method = cls.get_node_or_error(
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

        cls._check_delivery_method(
            checkout_info, lines, shipping_method=delivery_method, collection_point=None
        )

        cls._update_delivery_method(
            manager,
            checkout_info,
            lines,
            shipping_method=shipping_method,
            external_shipping_method=None,
            collection_point=None,
        )
        return CheckoutDeliveryMethodUpdate(checkout=checkout)

    @classmethod
    def perform_on_external_shipping_method(
        cls,
        info: ResolveInfo,
        shipping_method_id,
        checkout_info,
        lines,
        checkout,
        manager,
    ):
        delivery_method = manager.get_shipping_method(
            checkout=checkout,
            channel_slug=checkout.channel.slug,
            shipping_method_id=shipping_method_id,
        )

        if delivery_method is None and shipping_method_id:
            raise ValidationError(
                {
                    "delivery_method_id": ValidationError(
                        f"Couldn't resolve to a node: ${shipping_method_id}",
                        code=CheckoutErrorCode.NOT_FOUND.value,
                    )
                }
            )

        cls._check_delivery_method(
            checkout_info, lines, shipping_method=delivery_method, collection_point=None
        )

        cls._update_delivery_method(
            manager,
            checkout_info,
            lines,
            shipping_method=None,
            external_shipping_method=delivery_method,
            collection_point=None,
        )
        return CheckoutDeliveryMethodUpdate(checkout=checkout)

    @classmethod
    def perform_on_collection_point(
        cls,
        info: ResolveInfo,
        collection_point_id,
        checkout_info,
        lines,
        checkout,
        manager,
    ):
        collection_point = cls.get_node_or_error(
            info,
            collection_point_id,
            only_type=Warehouse,
            field="delivery_method_id",
            qs=warehouse_models.Warehouse.objects.select_related("address"),
        )
        cls._check_delivery_method(
            checkout_info,
            lines,
            shipping_method=None,
            collection_point=collection_point,
        )
        cls._update_delivery_method(
            manager,
            checkout_info,
            lines,
            shipping_method=None,
            external_shipping_method=None,
            collection_point=collection_point,
        )
        return CheckoutDeliveryMethodUpdate(checkout=checkout)

    @staticmethod
    def _check_delivery_method(
        checkout_info,
        lines,
        *,
        shipping_method: Optional[shipping_interface.ShippingMethodData],
        collection_point: Optional[Warehouse],
    ) -> None:
        delivery_method = shipping_method
        error_msg = "This shipping method is not applicable."

        if collection_point is not None:
            delivery_method = collection_point
            error_msg = "This pick up point is not applicable."

        delivery_method_is_valid = clean_delivery_method(
            checkout_info=checkout_info, lines=lines, method=delivery_method
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

    @classmethod
    def _update_delivery_method(
        cls,
        manager,
        checkout_info: "CheckoutInfo",
        lines: Iterable["CheckoutLineInfo"],
        *,
        shipping_method: Optional[ShippingMethod],
        external_shipping_method: Optional[shipping_interface.ShippingMethodData],
        collection_point: Optional[Warehouse],
    ) -> None:
        checkout = checkout_info.checkout
        if external_shipping_method:
            set_external_shipping_id(
                checkout=checkout, app_shipping_id=external_shipping_method.id
            )
        else:
            delete_external_shipping_id(checkout=checkout)
        checkout.shipping_method = shipping_method
        checkout.collection_point = collection_point
        invalidate_prices_updated_fields = invalidate_checkout_prices(
            checkout_info, lines, manager, save=False
        )
        checkout.save(
            update_fields=[
                "shipping_method",
                "collection_point",
            ]
            + invalidate_prices_updated_fields
        )
        get_or_create_checkout_metadata(checkout).save()
        cls.call_event(manager.checkout_updated, checkout)

    @staticmethod
    def _resolve_delivery_method_type(id_) -> Optional[str]:
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
        type_name = cls._resolve_delivery_method_type(delivery_method_id)

        checkout_info = fetch_checkout_info(checkout, lines, manager)
        if type_name == "Warehouse":
            return cls.perform_on_collection_point(
                info, delivery_method_id, checkout_info, lines, checkout, manager
            )
        if type_name == "ShippingMethod":
            return cls.perform_on_shipping_method(
                info, delivery_method_id, checkout_info, lines, checkout, manager
            )
        return cls.perform_on_external_shipping_method(
            info, delivery_method_id, checkout_info, lines, checkout, manager
        )
