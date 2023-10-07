from typing import TYPE_CHECKING, Iterable

import graphene
from django.core.exceptions import ValidationError

from ....checkout import AddressType, models
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ....checkout.utils import (
    change_shipping_address_in_checkout,
    invalidate_checkout_prices,
    is_shipping_required,
)
from ....core.tracing import traced_atomic_transaction
from ....graphql.account.mixins import AddressMetadataMixin
from ....warehouse.reservations import is_reservation_enabled
from ....webhook.event_types import WebhookEventAsyncType
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...core.descriptions import ADDED_IN_34, ADDED_IN_35, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
from ..types import Checkout
from .checkout_create import CheckoutAddressValidationRules
from .utils import (
    ERROR_DOES_NOT_SHIP,
    check_lines_quantity,
    get_checkout,
    update_checkout_shipping_method_if_invalid,
)

if TYPE_CHECKING:
    from ....checkout.fetch import DeliveryMethodBase


class CheckoutShippingAddressUpdate(AddressMetadataMixin, BaseMutation, I18nMixin):
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
        shipping_address = AddressInput(
            required=True,
            description="The mailing address to where the checkout will be shipped.",
        )
        validation_rules = CheckoutAddressValidationRules(
            required=False,
            description=(
                "The rules for changing validation for received shipping address data."
                + ADDED_IN_35
            ),
        )

    class Meta:
        description = "Update shipping address in the existing checkout."
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            )
        ]

    @classmethod
    def process_checkout_lines(
        cls,
        info,
        lines: Iterable["CheckoutLineInfo"],
        country: str,
        channel_slug: str,
        delivery_method_info: "DeliveryMethodBase",
    ) -> None:
        variants = []
        quantities = []
        for line_info in lines:
            variants.append(line_info.variant)
            quantities.append(line_info.line.quantity)
        site = get_site_promise(info.context).get()
        check_lines_quantity(
            variants,
            quantities,
            country,
            channel_slug,
            site.settings.limit_quantity_per_checkout,
            delivery_method_info=delivery_method_info,
            # Set replace=True to avoid existing_lines and quantities from
            # being counted twice by the check_stock_quantity_bulk
            replace=True,
            existing_lines=lines,
            check_reservations=is_reservation_enabled(site.settings),
        )

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info,
        /,
        shipping_address,
        validation_rules=None,
        checkout_id=None,
        token=None,
        id=None,
    ):
        checkout = get_checkout(
            cls,
            info,
            checkout_id=checkout_id,
            token=token,
            id=id,
            qs=models.Checkout.objects.prefetch_related(
                "lines__variant__product__product_type"
            ),
        )
        use_legacy_error_flow_for_checkout = (
            checkout.channel.use_legacy_error_flow_for_checkout
        )

        lines, _ = fetch_checkout_lines(
            checkout,
        )

        if use_legacy_error_flow_for_checkout and not is_shipping_required(lines):
            raise ValidationError(
                {
                    "shipping_address": ValidationError(
                        ERROR_DOES_NOT_SHIP,
                        code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED.value,
                    )
                }
            )
        address_validation_rules = validation_rules or {}
        shipping_address_instance = cls.validate_address(
            shipping_address,
            address_type=AddressType.SHIPPING,
            instance=checkout.shipping_address,
            info=info,
            format_check=address_validation_rules.get("check_fields_format", True),
            required_check=address_validation_rules.get("check_required_fields", True),
            enable_normalization=address_validation_rules.get(
                "enable_fields_normalization", True
            ),
        )
        manager = get_plugin_manager_promise(info.context).get()
        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        checkout_info = fetch_checkout_info(
            checkout, lines, manager, shipping_channel_listings
        )

        country = shipping_address_instance.country.code
        checkout.set_country(country, commit=True)

        # Resolve and process the lines, validating variants quantities
        if lines and use_legacy_error_flow_for_checkout:
            cls.process_checkout_lines(
                info,
                lines,
                country,
                checkout_info.channel.slug,
                checkout_info.delivery_method_info,
            )

        update_checkout_shipping_method_if_invalid(checkout_info, lines)

        shipping_address_updated_fields = []
        with traced_atomic_transaction():
            shipping_address_instance.save()
            shipping_address_updated_fields = change_shipping_address_in_checkout(
                checkout_info,
                shipping_address_instance,
                lines,
                manager,
                shipping_channel_listings,
            )
        invalidate_prices_updated_fields = invalidate_checkout_prices(
            checkout_info, lines, manager, save=False
        )
        checkout.save(
            update_fields=shipping_address_updated_fields
            + invalidate_prices_updated_fields
        )

        cls.call_event(manager.checkout_updated, checkout)

        return CheckoutShippingAddressUpdate(checkout=checkout)
