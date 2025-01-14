import graphene

from ....checkout.actions import call_checkout_info_event
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    update_delivery_method_lists_for_checkout_info,
)
from ....checkout.utils import add_variants_to_checkout, invalidate_checkout
from ....warehouse.reservations import get_reservation_length, is_reservation_enabled
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError, NonNullList
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_variants_available_in_channel
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import ProductVariant
from ...site.dataloaders import get_site_promise
from ..types import Checkout
from .checkout_create import CheckoutLineInput
from .utils import (
    check_lines_quantity,
    check_permissions_for_custom_prices,
    get_checkout,
    get_variants_and_total_quantities,
    group_lines_input_on_add,
    update_checkout_external_shipping_method_if_invalid,
    update_checkout_shipping_method_if_invalid,
    validate_variants_are_published,
    validate_variants_available_for_purchase,
)


class CheckoutLinesAdd(BaseMutation):
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
        lines = NonNullList(
            CheckoutLineInput,
            required=True,
            description=(
                "A list of checkout lines, each containing information about "
                "an item in the checkout."
            ),
        )

    class Meta:
        description = (
            "Adds a checkout line to the existing checkout."
            "If line was already in checkout, its quantity will be increased."
        )
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
    def validate_checkout_lines(
        cls,
        info,
        variants,
        checkout_lines_data,
        country,
        channel_slug,
        delivery_method_info,
        lines=None,
    ):
        variants, quantities = get_variants_and_total_quantities(
            variants, checkout_lines_data
        )
        site = get_site_promise(info.context).get()
        check_lines_quantity(
            variants,
            quantities,
            country,
            channel_slug,
            site.settings.limit_quantity_per_checkout,
            delivery_method_info=delivery_method_info,
            existing_lines=lines,
            check_reservations=is_reservation_enabled(site.settings),
        )

    @classmethod
    def process_lines_input(
        cls,
        info,
        checkout,
        variants,
        checkout_lines_data,
        checkout_info,
        replace=False,
        raise_error_for_missing_lines=False,
    ):
        if variants and checkout_lines_data:
            site = get_site_promise(info.context).get()
            checkout = add_variants_to_checkout(
                checkout,
                variants,
                checkout_lines_data,
                checkout_info.channel,
                replace=replace,
                replace_reservations=True,
                reservation_length=get_reservation_length(
                    site=site, user=info.context.user
                ),
                raise_error_for_missing_lines=raise_error_for_missing_lines,
            )

        lines, _ = fetch_checkout_lines(checkout)
        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        update_delivery_method_lists_for_checkout_info(
            checkout_info=checkout_info,
            shipping_method=checkout_info.checkout.shipping_method,
            collection_point=checkout_info.checkout.collection_point,
            shipping_address=checkout_info.shipping_address,
            lines=lines,
            shipping_channel_listings=shipping_channel_listings,
        )
        return lines

    @classmethod
    def clean_input(
        cls,
        info,
        checkout,
        variants,
        checkout_lines_data,
        checkout_info,
        lines,
    ):
        channel_slug = checkout_info.channel.slug

        cls.validate_checkout_lines(
            info,
            variants,
            checkout_lines_data,
            checkout.get_country(),
            channel_slug,
            checkout_info.delivery_method_info,
            lines=lines,
        )

        variants_ids_to_validate = {
            variant.id
            for variant, line_data in zip(variants, checkout_lines_data, strict=False)
            if line_data.quantity_to_update and line_data.quantity != 0
        }
        # validate variant only when line quantity is bigger than 0
        if variants_ids_to_validate:
            validate_variants_available_for_purchase(
                variants_ids_to_validate, checkout.channel_id
            )
            validate_variants_available_in_channel(
                variants_ids_to_validate,
                checkout.channel_id,
                CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value,
            )
            validate_variants_are_published(
                variants_ids_to_validate, checkout.channel_id
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        lines,
        checkout_id=None,
        token=None,
        id=None,
    ):
        app = get_app_promise(info.context).get()
        check_permissions_for_custom_prices(app, lines)

        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)
        manager = get_plugin_manager_promise(info.context).get()
        variants = cls._get_variants_from_lines_input(lines)
        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        checkout_info = fetch_checkout_info(
            checkout, [], manager, shipping_channel_listings
        )
        existing_lines_info, _ = fetch_checkout_lines(
            checkout, skip_lines_with_unavailable_variants=False
        )
        input_lines_data = cls._get_grouped_lines_data(lines, existing_lines_info)
        cls.clean_input(
            info,
            checkout,
            variants,
            input_lines_data,
            checkout_info,
            existing_lines_info,
        )
        lines = cls.process_lines_input(
            info,
            checkout,
            variants,
            input_lines_data,
            checkout_info,
        )

        update_checkout_external_shipping_method_if_invalid(checkout_info, lines)
        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        invalidate_checkout(checkout_info, lines, manager, save=True)
        call_checkout_info_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_UPDATED,
            checkout_info=checkout_info,
            lines=lines,
        )

        return CheckoutLinesAdd(checkout=checkout)

    @classmethod
    def _get_variants_from_lines_input(cls, lines: list[dict]) -> list[ProductVariant]:
        """Return list of ProductVariant objects.

        Uses variants ids provided in CheckoutLineInput to fetch ProductVariant objects.
        """
        variant_ids = [line.get("variant_id") for line in lines]
        return cls.get_nodes_or_error(variant_ids, "variant_id", ProductVariant)

    @classmethod
    def _get_grouped_lines_data(cls, lines, existing_lines_info):
        return group_lines_input_on_add(lines, existing_lines_info)
