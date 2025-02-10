import graphene
from django.core.exceptions import ValidationError

from ....checkout.actions import call_checkout_info_event
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ....checkout.utils import (
    delete_external_shipping_id_if_present,
    invalidate_checkout,
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
from .utils import ERROR_DOES_NOT_SHIP, clean_delivery_method, get_checkout


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

        if delivery_method and delivery_method.price.currency != checkout.currency:
            raise ValidationError(
                {
                    "delivery_method_id": ValidationError(
                        "Cannot choose shipping method with different currency than the checkout.",
                        code=CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.value,
                    )
                }
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
        collection_point,
        checkout_info,
        lines,
        checkout,
        manager,
    ):
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
        shipping_method: shipping_interface.ShippingMethodData | None,
        collection_point: Warehouse | None,
    ) -> None:
        delivery_method = shipping_method
        error_msg = "This shipping method is not applicable."

        if collection_point is not None:
            delivery_method = collection_point
            error_msg = "This pick up point is not applicable."

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

    @classmethod
    def _update_delivery_method(
        cls,
        manager,
        checkout_info: "CheckoutInfo",
        lines: list["CheckoutLineInfo"],
        *,
        shipping_method: ShippingMethod | None,
        external_shipping_method: shipping_interface.ShippingMethodData | None,
        collection_point: Warehouse | None,
    ) -> None:
        checkout_fields_to_update = ["shipping_method", "collection_point"]
        checkout = checkout_info.checkout
        if external_shipping_method:
            set_external_shipping_id(
                checkout=checkout, app_shipping_id=external_shipping_method.id
            )
        else:
            delete_external_shipping_id_if_present(checkout=checkout)

        # Clear checkout shipping address if it was switched from C&C.
        if checkout.collection_point_id and not collection_point:
            checkout.shipping_address = None
            checkout_fields_to_update += ["shipping_address"]

        checkout.shipping_method = shipping_method
        checkout.collection_point = collection_point
        if collection_point is not None:
            checkout.shipping_address = collection_point.address.get_copy()
            checkout_info.shipping_address = checkout.shipping_address
            checkout_fields_to_update += ["shipping_address"]
        invalidate_prices_updated_fields = invalidate_checkout(
            checkout_info, lines, manager, save=False
        )
        checkout.save(
            update_fields=checkout_fields_to_update + invalidate_prices_updated_fields
        )
        call_checkout_info_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout_info=checkout_info,
            lines=lines,
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

    @staticmethod
    def validate_collection_point(checkout_info, collection_point):
        if collection_point not in checkout_info.valid_pick_up_points:
            raise ValidationError(
                {
                    "delivery_method_id": ValidationError(
                        "This pick up point is not applicable.",
                        code=CheckoutErrorCode.DELIVERY_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )

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
            collection_point = cls.get_node_or_error(
                info,
                delivery_method_id,
                only_type=Warehouse,
                field="delivery_method_id",
                qs=warehouse_models.Warehouse.objects.select_related("address"),
            )
            cls.validate_collection_point(checkout_info, collection_point)
            return cls.perform_on_collection_point(
                collection_point, checkout_info, lines, checkout, manager
            )
        if type_name == "ShippingMethod":
            return cls.perform_on_shipping_method(
                info, delivery_method_id, checkout_info, lines, checkout, manager
            )
        return cls.perform_on_external_shipping_method(
            info, delivery_method_id, checkout_info, lines, checkout, manager
        )
