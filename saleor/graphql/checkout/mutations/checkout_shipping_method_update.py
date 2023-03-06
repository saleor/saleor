from typing import Optional

import graphene
from django.core.exceptions import ValidationError

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import (
    delete_external_shipping_id,
    get_or_create_checkout_metadata,
    invalidate_checkout_prices,
    is_shipping_required,
    set_external_shipping_id,
)
from ....plugins.webhook.utils import APP_ID_PREFIX
from ....shipping import interface as shipping_interface
from ....shipping import models as shipping_models
from ....shipping.utils import convert_to_shipping_method_data
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import from_global_id_or_error
from ...discount.dataloaders import load_discounts
from ...plugins.dataloaders import get_plugin_manager_promise
from ...shipping.types import ShippingMethod
from ..types import Checkout
from .utils import ERROR_DOES_NOT_SHIP, clean_delivery_method, get_checkout


class CheckoutShippingMethodUpdate(BaseMutation):
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
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        )
        shipping_method_id = graphene.ID(required=True, description="Shipping method.")

    class Meta:
        description = "Updates the shipping method of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @staticmethod
    def _resolve_delivery_method_type(id_) -> Optional[str]:
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

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        checkout_id=None,
        id=None,
        shipping_method_id,
        token=None
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        manager = get_plugin_manager_promise(info.context).get()

        lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        if unavailable_variant_pks:
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
        discounts = load_discounts(info.context)
        checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
        if not is_shipping_required(lines):
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        ERROR_DOES_NOT_SHIP,
                        code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED.value,
                    )
                }
            )

        type_name = cls._resolve_delivery_method_type(shipping_method_id)

        if type_name == "ShippingMethod":
            return cls.perform_on_shipping_method(
                info, shipping_method_id, checkout_info, lines, checkout, manager
            )
        return cls.perform_on_external_shipping_method(
            info, shipping_method_id, checkout_info, lines, checkout, manager
        )

    @staticmethod
    def _check_delivery_method(
        checkout_info,
        lines,
        *,
        delivery_method: Optional[shipping_interface.ShippingMethodData],
    ) -> None:
        delivery_method_is_valid = clean_delivery_method(
            checkout_info=checkout_info,
            lines=lines,
            method=delivery_method,
        )
        if not delivery_method_is_valid or not delivery_method:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "This shipping method is not applicable.",
                        code=CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
                    )
                }
            )

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
        delivery_method = convert_to_shipping_method_data(shipping_method, listing)

        cls._check_delivery_method(
            checkout_info, lines, delivery_method=delivery_method
        )

        delete_external_shipping_id(checkout=checkout)
        checkout.shipping_method = shipping_method
        discounts = load_discounts(info.context)
        invalidate_prices_updated_fields = invalidate_checkout_prices(
            checkout_info, lines, manager, discounts, save=False
        )
        checkout.save(
            update_fields=[
                "shipping_method",
            ]
            + invalidate_prices_updated_fields
        )
        get_or_create_checkout_metadata(checkout).save(
            update_fields=[
                "private_metadata",
            ]
        )

        cls.call_event(manager.checkout_updated, checkout)
        return CheckoutShippingMethodUpdate(checkout=checkout)

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

        cls._check_delivery_method(
            checkout_info, lines, delivery_method=delivery_method
        )

        set_external_shipping_id(checkout=checkout, app_shipping_id=delivery_method.id)
        checkout.shipping_method = None
        discounts = load_discounts(info.context)
        invalidate_prices_updated_fields = invalidate_checkout_prices(
            checkout_info, lines, manager, discounts, save=False
        )
        checkout.save(
            update_fields=[
                "shipping_method",
            ]
            + invalidate_prices_updated_fields
        )
        get_or_create_checkout_metadata(checkout).save(
            update_fields=["private_metadata"]
        )
        cls.call_event(manager.checkout_updated, checkout)

        return CheckoutShippingMethodUpdate(checkout=checkout)
