from typing import TYPE_CHECKING, Optional

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError

from ....checkout import AddressType, models
from ....checkout.actions import call_checkout_event
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.utils import add_variants_to_checkout, create_checkout_metadata
from ....core.exceptions import PermissionDenied
from ....core.tracing import traced_atomic_transaction
from ....core.utils import metadata_manager
from ....core.utils.country import get_active_country
from ....permission.enums import CheckoutPermissions
from ....product import models as product_models
from ....warehouse.reservations import get_reservation_length, is_reservation_enabled
from ....webhook.event_types import WebhookEventAsyncType
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...app.dataloaders import get_app_promise
from ...channel.utils import clean_channel
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.descriptions import ADDED_IN_321
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.enums import LanguageCodeEnum
from ...core.mutations import DeprecatedModelMutation
from ...core.scalars import PositiveDecimal
from ...core.types import BaseInputObjectType, CheckoutError, NonNullList
from ...core.utils import WebhookEventInfo
from ...core.validators import validate_variants_available_in_channel
from ...plugins.dataloaders import get_plugin_manager_promise
from ...product.types import ProductVariant
from ...site.dataloaders import get_site_promise
from ..types import Checkout
from .utils import (
    apply_gift_reward_if_applicable_on_checkout_creation,
    check_lines_quantity,
    check_permissions_for_custom_prices,
    get_variants_and_total_quantities,
    group_lines_input_on_add,
    validate_variants_are_published,
    validate_variants_available_for_purchase,
)

if TYPE_CHECKING:
    from ....account.models import Address
    from .utils import CheckoutLineData

from ...meta.inputs import MetadataInput, MetadataInputDescription


class CheckoutAddressValidationRules(BaseInputObjectType):
    check_required_fields = graphene.Boolean(
        description=(
            "Determines if an error should be raised when the provided address doesn't "
            "have all the required fields. The list of required fields is dynamic and "
            "depends on the country code (use the `addressValidationRules` query to "
            "fetch them). Note: country code is mandatory for all addresses regardless "
            "of the rules provided in this input."
        ),
        default_value=True,
    )
    check_fields_format = graphene.Boolean(
        description=(
            "Determines if an error should be raised when the provided address doesn't "
            "match the expected format. Example: using letters for postal code when "
            "the numbers are expected."
        ),
        default_value=True,
    )
    enable_fields_normalization = graphene.Boolean(
        description=(
            "Determines if Saleor should apply normalization on address fields. "
            "Example: converting city field to uppercase letters."
        ),
        default_value=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutValidationRules(BaseInputObjectType):
    shipping_address = CheckoutAddressValidationRules(
        description=(
            "The validation rules that can be applied to provided shipping address"
            " data."
        )
    )
    billing_address = CheckoutAddressValidationRules(
        description=(
            "The validation rules that can be applied to provided billing address data."
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutLineInput(BaseInputObjectType):
    quantity = graphene.Int(required=True, description="The number of items purchased.")
    variant_id = graphene.ID(required=True, description="ID of the product variant.")
    price = PositiveDecimal(
        required=False,
        description=(
            "Custom price of the item. Can be set only by apps "
            "with `HANDLE_CHECKOUTS` permission. When the line with the same variant "
            "will be provided multiple times, the last price will be used."
        ),
    )
    force_new_line = graphene.Boolean(
        required=False,
        default_value=False,
        description=(
            "Flag that allow force splitting the same variant into multiple lines "
            "by skipping the matching logic. "
        ),
    )
    metadata = NonNullList(
        MetadataInput,
        description="Fields required to update the object's metadata. "
        f"{MetadataInputDescription.PUBLIC_METADATA_INPUT}",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutCreateInput(BaseInputObjectType):
    channel = graphene.String(
        description="Slug of a channel in which to create a checkout."
    )
    lines = NonNullList(
        CheckoutLineInput,
        description=(
            "A list of checkout lines, each containing information about "
            "an item in the checkout."
        ),
        required=True,
    )
    email = graphene.String(description="The customer's email address.")
    save_shipping_address = graphene.Boolean(
        description=(
            "Indicates whether the shipping address should be saved "
            "to the user’s address book upon checkout completion."
            "Can only be set when a shipping address is provided. If not specified "
            "along with the address, the default behavior is to save the address."
        )
        + ADDED_IN_321
    )
    shipping_address = AddressInput(
        description=(
            "The mailing address to where the checkout will be shipped. "
            "Note: the address will be ignored if the checkout "
            "doesn't contain shippable items. `skipValidation` requires "
            "HANDLE_CHECKOUTS and AUTHENTICATED_APP permissions."
        )
    )
    save_billing_address = graphene.Boolean(
        description=(
            "Indicates whether the billing address should be saved "
            "to the user’s address book upon checkout completion. "
            "Can only be set when a billing address is provided. If not specified "
            "along with the address, the default behavior is to save the address."
        )
        + ADDED_IN_321
    )
    billing_address = AddressInput(
        description=(
            "Billing address of the customer. `skipValidation` requires "
            "HANDLE_CHECKOUTS and AUTHENTICATED_APP permissions."
        )
    )
    language_code = graphene.Argument(
        LanguageCodeEnum, required=False, description="Checkout language code."
    )
    validation_rules = CheckoutValidationRules(
        required=False,
        description=("The checkout validation rules that can be changed."),
    )

    metadata = NonNullList(
        MetadataInput,
        description=(
            f"Checkout public metadata. {ADDED_IN_321}"
            f"{MetadataInputDescription.PUBLIC_METADATA_INPUT}"
        ),
        required=False,
    )

    private_metadata = NonNullList(
        MetadataInput,
        description=(
            "Checkout private metadata. Requires one of the following permissions:"
            f"{CheckoutPermissions.MANAGE_CHECKOUTS.name}, "
            f"{CheckoutPermissions.HANDLE_CHECKOUTS.name} {ADDED_IN_321}"
            f"{MetadataInputDescription.PRIVATE_METADATA_INPUT}"
        ),
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT


class CheckoutCreate(DeprecatedModelMutation, I18nMixin):
    created = graphene.Field(
        graphene.Boolean,
        description=(
            "Whether the checkout was created or the current active one was returned. "
            "Refer to checkoutLinesAdd and checkoutLinesUpdate to merge a cart "
            "with an active checkout."
        ),
        deprecation_reason="Always returns `true`.",
    )

    class Arguments:
        input = CheckoutCreateInput(
            required=True, description="Fields required to create checkout."
        )

    class Meta:
        description = (
            "Create a new checkout.\n\n`skipValidation` field requires "
            "HANDLE_CHECKOUTS and AUTHENTICATED_APP permissions."
        )
        doc_category = DOC_CATEGORY_CHECKOUT
        model = models.Checkout
        object_type = Checkout
        return_field_name = "checkout"
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_CREATED,
                description="A checkout was created.",
            )
        ]

        # This mutation *does* save metadata but not via "support_meta_field"
        # flags. Checkout metadata is held in separate objects
        # Flags are set to False, so it's explicit and should not be enabled
        support_meta_field = False
        support_private_meta_field = False

    @classmethod
    def clean_checkout_lines(
        cls, info: ResolveInfo, lines, country, channel
    ) -> tuple[list[product_models.ProductVariant], list["CheckoutLineData"]]:
        app = get_app_promise(info.context).get()
        site = get_site_promise(info.context).get()
        check_permissions_for_custom_prices(app, lines)
        variant_ids = [line["variant_id"] for line in lines]
        variants = cls.get_nodes_or_error(
            variant_ids,
            "variant_id",
            ProductVariant,
            qs=product_models.ProductVariant.objects.prefetch_related(
                "product__product_type"
            ),
        )

        checkout_lines_data = group_lines_input_on_add(lines)

        variant_db_ids = {variant.id for variant in variants}
        validate_variants_available_for_purchase(variant_db_ids, channel.id)
        validate_variants_available_in_channel(
            variant_db_ids,
            channel.id,
            CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value,
        )
        validate_variants_are_published(variant_db_ids, channel.id)

        variants, quantities = get_variants_and_total_quantities(
            variants, checkout_lines_data
        )

        check_lines_quantity(
            variants,
            quantities,
            country,
            channel.slug,
            site.settings.limit_quantity_per_checkout,
            check_reservations=is_reservation_enabled(site.settings),
        )
        return variants, checkout_lines_data

    @classmethod
    def retrieve_shipping_address(
        cls, user, data: dict, info: ResolveInfo
    ) -> Optional["Address"]:
        address_validation_rules = data.get("validation_rules", {}).get(
            "shipping_address", {}
        )
        if data.get("shipping_address") is not None:
            return cls.validate_address(
                data["shipping_address"],
                address_type=AddressType.SHIPPING,
                format_check=address_validation_rules.get("check_fields_format", True),
                required_check=address_validation_rules.get(
                    "check_required_fields", True
                ),
                enable_normalization=address_validation_rules.get(
                    "enable_fields_normalization", True
                ),
                info=info,
            )
        return None

    @classmethod
    def retrieve_billing_address(
        cls, user, data: dict, info: ResolveInfo
    ) -> Optional["Address"]:
        address_validation_rules = data.get("validation_rules", {}).get(
            "billing_address", {}
        )
        if data.get("billing_address") is not None:
            return cls.validate_address(
                data["billing_address"],
                address_type=AddressType.BILLING,
                format_check=address_validation_rules.get("check_fields_format", True),
                required_check=address_validation_rules.get(
                    "check_required_fields", True
                ),
                enable_normalization=address_validation_rules.get(
                    "enable_fields_normalization", True
                ),
                info=info,
            )
        return None

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance: models.Checkout, data, **kwargs):
        user = info.context.user
        channel = data.pop("channel")

        metadata_list: list[MetadataInput] | None = data.pop("metadata", None)
        private_metadata_list: list[MetadataInput] | None = data.pop(
            "private_metadata", None
        )

        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        trying_to_set_private_metadata = private_metadata_list is not None

        if trying_to_set_private_metadata:
            can_set_private_metadata = cls.check_permissions(
                info.context,
                permissions=[
                    CheckoutPermissions.HANDLE_CHECKOUTS,
                    CheckoutPermissions.MANAGE_CHECKOUTS,
                ],
            )

            if not can_set_private_metadata:
                raise PermissionDenied(
                    "You need MANAGE_CHECKOUTS or HANDLE_CHECKOUTS permission to set privateMetadata"
                )

        cleaned_input["metadata_collection"] = cls.create_metadata_from_graphql_input(
            metadata_list, error_field_name="metadata"
        )
        cleaned_input["private_metadata_collection"] = (
            cls.create_metadata_from_graphql_input(
                private_metadata_list, error_field_name="private_metadata"
            )
        )

        cleaned_input["channel"] = channel
        cleaned_input["currency"] = channel.currency_code
        save_shipping_address = data.get("save_shipping_address")
        shipping_address_metadata: list[MetadataInput] | None = (
            data.get("shipping_address", {}).pop("metadata", [])
            if data.get("shipping_address")
            else None
        )
        save_billing_address = data.get("save_billing_address")
        billing_address_metadata: list[MetadataInput] | None = (
            data.get("billing_address", {}).pop("metadata", [])
            if data.get("billing_address")
            else None
        )

        shipping_address_metadata_collection = cls.create_metadata_from_graphql_input(
            shipping_address_metadata, error_field_name="metadata"
        )
        billing_address_metadata_collection = cls.create_metadata_from_graphql_input(
            billing_address_metadata, error_field_name="metadata"
        )

        shipping_address = cls.retrieve_shipping_address(user, data, info)
        billing_address = cls.retrieve_billing_address(user, data, info)
        if shipping_address:
            metadata_manager.store_on_instance(
                shipping_address_metadata_collection,
                shipping_address,
                metadata_manager.MetadataType.PUBLIC,
            )

        if billing_address:
            metadata_manager.store_on_instance(
                billing_address_metadata_collection,
                billing_address,
                metadata_manager.MetadataType.PUBLIC,
            )

        if save_shipping_address is not None and not shipping_address:
            raise ValidationError(
                {
                    "save_shipping_address": ValidationError(
                        "This option can only be selected if a shipping address "
                        "is provided.",
                        code=CheckoutErrorCode.MISSING_ADDRESS_DATA.value,
                    )
                }
            )

        if save_billing_address is not None and not billing_address:
            raise ValidationError(
                {
                    "save_billing_address": ValidationError(
                        "This option can only be selected if a billing address "
                        "is provided.",
                        code=CheckoutErrorCode.MISSING_ADDRESS_DATA.value,
                    )
                }
            )

        country = get_active_country(
            channel,
            shipping_address,
            billing_address,
        )
        lines = data.pop("lines", None)
        if lines:
            (
                cleaned_input["variants"],
                cleaned_input["lines_data"],
            ) = cls.clean_checkout_lines(
                info,
                lines,
                country,
                cleaned_input["channel"],
            )

        # Use authenticated user's email as default email
        if user:
            email = data.pop("email", None)
            cleaned_input["email"] = email or user.email

        language_code = data.get("language_code", settings.LANGUAGE_CODE)
        cleaned_input["language_code"] = language_code

        cleaned_input["shipping_address"] = shipping_address
        cleaned_input["billing_address"] = billing_address
        cleaned_input["country"] = country
        return cleaned_input

    @classmethod
    def save(cls, info: ResolveInfo, instance: models.Checkout, cleaned_input):
        with traced_atomic_transaction():
            # Create the checkout object
            instance.save()

            # Set checkout country
            country = cleaned_input["country"]
            instance.set_country(country)
            # Create checkout lines
            channel = cleaned_input["channel"]
            variants = cleaned_input.get("variants")
            checkout_lines_data = cleaned_input.get("lines_data")
            if variants and checkout_lines_data:
                site = get_site_promise(info.context).get()
                add_variants_to_checkout(
                    instance,
                    variants,
                    checkout_lines_data,
                    channel,
                    site.settings.limit_quantity_per_checkout,
                    reservation_length=get_reservation_length(
                        site=site, user=info.context.user
                    ),
                )

            # Save addresses
            shipping_address = cleaned_input.get("shipping_address")
            if shipping_address:
                shipping_address.save()
                instance.shipping_address = shipping_address.get_copy()

            billing_address = cleaned_input.get("billing_address")
            if billing_address:
                billing_address.save()
                instance.billing_address = billing_address.get_copy()

            instance.save()
            create_checkout_metadata(
                instance,
                metadata=cleaned_input.get("metadata_collection"),
                private_metadata=cleaned_input.get("private_metadata_collection"),
            )

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        instance = super().get_instance(info, **data)
        user = info.context.user
        if user:
            instance.user = user
        return instance

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        channel_input = input.get("channel")
        channel = clean_channel(
            channel_input, error_class=CheckoutErrorCode, allow_replica=False
        )
        if channel:
            input["channel"] = channel

        instance = cls.get_instance(info, **input)
        cleaned_input = cls.clean_input(info, instance, input)

        instance = cls.construct_instance(instance, cleaned_input)

        cls.clean_instance(info, instance)
        cls.save(info, instance, cleaned_input)
        cls._save_m2m(info, instance, cleaned_input)

        checkout = instance
        apply_gift_reward_if_applicable_on_checkout_creation(checkout)
        manager = get_plugin_manager_promise(info.context).get()
        call_checkout_event(
            manager,
            event_name=WebhookEventAsyncType.CHECKOUT_CREATED,
            checkout=checkout,
        )

        return CheckoutCreate(
            checkout=SyncWebhookControlContext(node=checkout), created=True
        )
