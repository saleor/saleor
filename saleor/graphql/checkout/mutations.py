import datetime
import uuid
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, Union

import graphene
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from graphql.error import GraphQLError

from ...checkout import AddressType, models
from ...checkout.complete_checkout import complete_checkout
from ...checkout.error_codes import CheckoutErrorCode
from ...checkout.fetch import (
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
    update_delivery_method_lists_for_checkout_info,
)
from ...checkout.utils import (
    add_promo_code_to_checkout,
    add_variants_to_checkout,
    calculate_checkout_quantity,
    change_billing_address_in_checkout,
    change_shipping_address_in_checkout,
    clear_delivery_method,
    delete_external_shipping_id,
    is_shipping_required,
    recalculate_checkout_discount,
    remove_promo_code_from_checkout,
    remove_voucher_from_checkout,
    set_external_shipping_id,
    validate_variants_in_checkout_lines,
)
from ...core import analytics
from ...core.exceptions import InsufficientStock, PermissionDenied
from ...core.permissions import AccountPermissions
from ...core.tracing import traced_atomic_transaction
from ...core.transactions import transaction_with_commit_on_errors
from ...order import models as order_models
from ...product import models as product_models
from ...product.models import ProductChannelListing
from ...shipping import interface as shipping_interface
from ...shipping import models as shipping_models
from ...shipping.utils import convert_to_shipping_method_data
from ...warehouse import models as warehouse_models
from ...warehouse.availability import check_stock_and_preorder_quantity_bulk
from ...warehouse.reservations import get_reservation_length, is_reservation_enabled
from ..account.i18n import I18nMixin
from ..account.types import AddressInput
from ..channel.utils import clean_channel
from ..core.descriptions import (
    ADDED_IN_31,
    DEPRECATED_IN_3X_FIELD,
    DEPRECATED_IN_3X_INPUT,
)
from ..core.enums import LanguageCodeEnum
from ..core.mutations import BaseMutation, ModelMutation
from ..core.scalars import UUID
from ..core.types.common import CheckoutError
from ..core.utils import from_global_id_or_error
from ..core.validators import (
    validate_one_of_args_is_in_mutation,
    validate_variants_available_in_channel,
)
from ..discount.types import Voucher
from ..giftcard.types import GiftCard
from ..order.types import Order
from ..product.types import ProductVariant
from ..shipping.types import ShippingMethod
from ..utils import get_user_or_app_from_context, resolve_global_ids_to_primary_keys
from ..warehouse.types import Warehouse
from .types import Checkout, CheckoutLine

ERROR_DOES_NOT_SHIP = "This checkout doesn't need shipping"


if TYPE_CHECKING:
    from ...account.models import Address
    from ...checkout.fetch import CheckoutInfo


def clean_delivery_method(
    checkout_info: "CheckoutInfo",
    lines: Iterable[CheckoutLineInfo],
    method: Optional[
        Union[
            shipping_interface.ShippingMethodData,
            warehouse_models.Warehouse,
        ]
    ],
) -> bool:
    """Check if current shipping method is valid."""

    if not method:
        # no shipping method was provided, it is valid
        return True

    if not is_shipping_required(lines):
        raise ValidationError(
            ERROR_DOES_NOT_SHIP, code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED.value
        )

    if not checkout_info.shipping_address and isinstance(
        method, shipping_interface.ShippingMethodData
    ):
        raise ValidationError(
            "Cannot choose a shipping method for a checkout without the "
            "shipping address.",
            code=CheckoutErrorCode.SHIPPING_ADDRESS_NOT_SET.value,
        )

    valid_methods = checkout_info.valid_delivery_methods
    return method in valid_methods


def update_checkout_shipping_method_if_invalid(
    checkout_info: "CheckoutInfo", lines: Iterable[CheckoutLineInfo]
):
    quantity = calculate_checkout_quantity(lines)

    # remove shipping method when empty checkout
    if quantity == 0 or not is_shipping_required(lines):
        clear_delivery_method(checkout_info)

    is_valid = clean_delivery_method(
        checkout_info=checkout_info,
        lines=lines,
        method=checkout_info.delivery_method_info.delivery_method,
    )

    if not is_valid:
        clear_delivery_method(checkout_info)


def check_lines_quantity(
    variants,
    quantities,
    country,
    channel_slug,
    global_quantity_limit,
    allow_zero_quantity=False,
    existing_lines=None,
    replace=False,
    check_reservations=False,
):
    """Clean quantities and check if stock is sufficient for each checkout line.

    By default, zero quantity is not allowed,
    but if this validation is used for updating existing checkout lines,
    allow_zero_quantities can be set to True
    and checkout lines with this quantity can be later removed.
    """

    for quantity in quantities:
        if not allow_zero_quantity and quantity <= 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "The quantity should be higher than zero.",
                        code=CheckoutErrorCode.ZERO_QUANTITY,
                    )
                }
            )

        elif allow_zero_quantity and quantity < 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "The quantity should be higher or equal zero.",
                        code=CheckoutErrorCode.ZERO_QUANTITY,
                    )
                }
            )
    try:
        check_stock_and_preorder_quantity_bulk(
            variants,
            country,
            quantities,
            channel_slug,
            global_quantity_limit,
            existing_lines=existing_lines,
            replace=replace,
            check_reservations=check_reservations,
        )
    except InsufficientStock as e:
        errors = [
            ValidationError(
                f"Could not add items {item.variant}. "
                f"Only {max(item.available_quantity, 0)} remaining in stock.",
                code=e.code,
            )
            for item in e.items
        ]
        raise ValidationError({"quantity": errors})


def validate_variants_available_for_purchase(variants_id: set, channel_id: int):
    today = datetime.date.today()
    is_available_for_purchase = Q(
        available_for_purchase__lte=today,
        product__variants__id__in=variants_id,
        channel_id=channel_id,
    )
    available_variants = ProductChannelListing.objects.filter(
        is_available_for_purchase
    ).values_list("product__variants__id", flat=True)
    not_available_variants = variants_id.difference(set(available_variants))
    if not_available_variants:
        variant_ids = [
            graphene.Node.to_global_id("ProductVariant", pk)
            for pk in not_available_variants
        ]
        error_code = CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines for unavailable for purchase variants.",
                    code=error_code,
                    params={"variants": variant_ids},
                )
            }
        )


def validate_variants_are_published(variants_id: set, channel_id: int):
    published_variants = product_models.ProductChannelListing.objects.filter(
        channel_id=channel_id, product__variants__id__in=variants_id, is_published=True
    ).values_list("product__variants__id", flat=True)
    not_published_variants = variants_id.difference(set(published_variants))
    if not_published_variants:
        variant_ids = [
            graphene.Node.to_global_id("ProductVariant", pk)
            for pk in not_published_variants
        ]
        error_code = CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.value
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines for unpublished variants.",
                    code=error_code,
                    params={"variants": variant_ids},
                )
            }
        )


def get_checkout_by_token(token: uuid.UUID, qs=None):
    if qs is None:
        qs = models.Checkout.objects.select_related(
            "channel",
            "shipping_method",
            "collection_point",
            "billing_address",
            "shipping_address",
        )
    try:
        checkout = qs.get(token=token)
    except ObjectDoesNotExist:
        raise ValidationError(
            {
                "token": ValidationError(
                    f"Couldn't resolve to a node: {token}.",
                    code=CheckoutErrorCode.NOT_FOUND.value,
                )
            }
        )
    return checkout


def group_quantity_by_variants(lines: List[Dict[str, Any]]) -> List[int]:
    variant_quantity_map: Dict[str, int] = defaultdict(int)

    for quantity, variant_id in (line.values() for line in lines):
        variant_quantity_map[variant_id] += quantity

    return list(variant_quantity_map.values())


def validate_checkout_email(checkout: models.Checkout):
    if not checkout.email:
        raise ValidationError(
            "Checkout email must be set.",
            code=CheckoutErrorCode.EMAIL_NOT_SET.value,
        )


class CheckoutLineInput(graphene.InputObjectType):
    quantity = graphene.Int(required=True, description="The number of items purchased.")
    variant_id = graphene.ID(required=True, description="ID of the product variant.")


class CheckoutCreateInput(graphene.InputObjectType):
    channel = graphene.String(
        description="Slug of a channel in which to create a checkout."
    )
    lines = graphene.List(
        CheckoutLineInput,
        description=(
            "A list of checkout lines, each containing information about "
            "an item in the checkout."
        ),
        required=True,
    )
    email = graphene.String(description="The customer's email address.")
    shipping_address = AddressInput(
        description=(
            "The mailing address to where the checkout will be shipped. "
            "Note: the address will be ignored if the checkout "
            "doesn't contain shippable items."
        )
    )
    billing_address = AddressInput(description="Billing address of the customer.")
    language_code = graphene.Argument(
        LanguageCodeEnum, required=False, description="Checkout language code."
    )


class CheckoutCreate(ModelMutation, I18nMixin):
    created = graphene.Field(
        graphene.Boolean,
        description=(
            "Whether the checkout was created or the current active one was returned. "
            "Refer to checkoutLinesAdd and checkoutLinesUpdate to merge a cart "
            "with an active checkout."
        ),
        deprecation_reason=f"{DEPRECATED_IN_3X_FIELD} Always returns `True`.",
    )

    class Arguments:
        input = CheckoutCreateInput(
            required=True, description="Fields required to create checkout."
        )

    class Meta:
        description = "Create a new checkout."
        model = models.Checkout
        object_type = Checkout
        return_field_name = "checkout"
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def clean_checkout_lines(
        cls, info, lines, country, channel
    ) -> Tuple[List[product_models.ProductVariant], List[int]]:
        variant_ids = [line["variant_id"] for line in lines]
        variants = cls.get_nodes_or_error(
            variant_ids,
            "variant_id",
            ProductVariant,
            qs=product_models.ProductVariant.objects.prefetch_related(
                "product__product_type"
            ),
        )

        quantities = group_quantity_by_variants(lines)

        variant_db_ids = {variant.id for variant in variants}
        validate_variants_available_for_purchase(variant_db_ids, channel.id)
        validate_variants_available_in_channel(
            variant_db_ids, channel.id, CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL
        )
        validate_variants_are_published(variant_db_ids, channel.id)
        check_lines_quantity(
            variants,
            quantities,
            country,
            channel.slug,
            info.context.site.settings.limit_quantity_per_checkout,
            check_reservations=is_reservation_enabled(info.context.site.settings),
        )
        return variants, quantities

    @classmethod
    def retrieve_shipping_address(cls, user, data: dict) -> Optional["Address"]:
        if data.get("shipping_address") is not None:
            return cls.validate_address(
                data["shipping_address"], address_type=AddressType.SHIPPING
            )
        if user.is_authenticated:
            return user.default_shipping_address
        return None

    @classmethod
    def retrieve_billing_address(cls, user, data: dict) -> Optional["Address"]:
        if data.get("billing_address") is not None:
            return cls.validate_address(
                data["billing_address"], address_type=AddressType.BILLING
            )
        if user.is_authenticated:
            return user.default_billing_address
        return None

    @classmethod
    def clean_input(cls, info, instance: models.Checkout, data, input_cls=None):
        user = info.context.user
        channel = data.pop("channel")
        cleaned_input = super().clean_input(info, instance, data)

        cleaned_input["channel"] = channel
        cleaned_input["currency"] = channel.currency_code

        shipping_address = cls.retrieve_shipping_address(user, data)
        billing_address = cls.retrieve_billing_address(user, data)

        if shipping_address:
            country = shipping_address.country.code
        else:
            country = channel.default_country

        # Resolve and process the lines, retrieving the variants and quantities
        lines = data.pop("lines", None)
        if lines:
            (
                cleaned_input["variants"],
                cleaned_input["quantities"],
            ) = cls.clean_checkout_lines(
                info,
                lines,
                country,
                cleaned_input["channel"],
            )

        # Use authenticated user's email as default email
        if user.is_authenticated:
            email = data.pop("email", None)
            cleaned_input["email"] = email or user.email

        language_code = data.get("language_code", settings.LANGUAGE_CODE)
        cleaned_input["language_code"] = language_code

        cleaned_input["shipping_address"] = shipping_address
        cleaned_input["billing_address"] = billing_address
        cleaned_input["country"] = country
        return cleaned_input

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, instance: models.Checkout, cleaned_input):
        # Create the checkout object
        instance.save()

        # Set checkout country
        country = cleaned_input["country"]
        instance.set_country(country)
        # Create checkout lines
        channel = cleaned_input["channel"]
        variants = cleaned_input.get("variants")
        quantities = cleaned_input.get("quantities")
        if variants and quantities:
            add_variants_to_checkout(
                instance,
                variants,
                quantities,
                channel.slug,
                info.context.site.settings.limit_quantity_per_checkout,
                reservation_length=get_reservation_length(info.context),
            )

        # Save addresses
        shipping_address = cleaned_input.get("shipping_address")
        if shipping_address and instance.is_shipping_required():
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()

        billing_address = cleaned_input.get("billing_address")
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address.get_copy()

        instance.save()

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        user = info.context.user
        if user.is_authenticated:
            instance.user = user
        return instance

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        channel_input = data.get("input", {}).get("channel")
        channel = clean_channel(channel_input, error_class=CheckoutErrorCode)
        if channel:
            data["input"]["channel"] = channel
        response = super().perform_mutation(_root, info, **data)
        info.context.plugins.checkout_created(response.checkout)
        response.created = True
        return response


class CheckoutLinesAdd(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        lines = graphene.List(
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
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def validate_checkout_lines(
        cls,
        info,
        variants,
        quantities,
        country,
        channel_slug,
        lines=None,
    ):
        check_lines_quantity(
            variants,
            quantities,
            country,
            channel_slug,
            info.context.site.settings.limit_quantity_per_checkout,
            existing_lines=lines,
            check_reservations=is_reservation_enabled(info.context.site.settings),
        )

    @classmethod
    def clean_input(
        cls,
        info,
        checkout,
        variants,
        quantities,
        checkout_info,
        lines,
        manager,
        discounts,
        replace,
    ):
        channel_slug = checkout_info.channel.slug

        cls.validate_checkout_lines(
            info,
            variants,
            quantities,
            checkout.get_country(),
            channel_slug,
            lines=lines,
        )

        variants_ids_to_validate = {
            variant.id
            for variant, quantity in zip(variants, quantities)
            if quantity != 0
        }

        # validate variant only when line quantity is bigger than 0
        if variants_ids_to_validate:
            validate_variants_available_for_purchase(
                variants_ids_to_validate, checkout.channel_id
            )
            validate_variants_available_in_channel(
                variants_ids_to_validate,
                checkout.channel_id,
                CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL,
            )
            validate_variants_are_published(
                variants_ids_to_validate, checkout.channel_id
            )

        if variants and quantities:
            checkout = add_variants_to_checkout(
                checkout,
                variants,
                quantities,
                channel_slug,
                replace=replace,
                replace_reservations=True,
                reservation_length=get_reservation_length(info.context),
            )

        lines = fetch_checkout_lines(checkout)
        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        update_delivery_method_lists_for_checkout_info(
            checkout_info,
            checkout_info.checkout.shipping_method,
            checkout_info.checkout.collection_point,
            checkout_info.shipping_address,
            lines,
            discounts,
            manager,
            shipping_channel_listings,
        )
        return lines

    @classmethod
    def perform_mutation(
        cls, _root, info, lines, checkout_id=None, token=None, replace=False
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        discounts = info.context.discounts
        manager = info.context.plugins

        variant_ids = [line.get("variant_id") for line in lines]
        variants = cls.get_nodes_or_error(variant_ids, "variant_id", ProductVariant)
        input_quantities = group_quantity_by_variants(lines)

        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        checkout_info = fetch_checkout_info(
            checkout, [], discounts, manager, shipping_channel_listings
        )

        lines = fetch_checkout_lines(checkout)
        lines = cls.clean_input(
            info,
            checkout,
            variants,
            input_quantities,
            checkout_info,
            lines,
            manager,
            discounts,
            replace,
        )
        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        manager.checkout_updated(checkout)
        return CheckoutLinesAdd(checkout=checkout)


class CheckoutLinesUpdate(CheckoutLinesAdd):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Meta:
        description = "Updates checkout line in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def validate_checkout_lines(
        cls,
        info,
        variants,
        quantities,
        country,
        channel_slug,
        lines=None,
    ):
        check_lines_quantity(
            variants,
            quantities,
            country,
            channel_slug,
            info.context.site.settings.limit_quantity_per_checkout,
            allow_zero_quantity=True,
            existing_lines=lines,
            replace=True,
            check_reservations=is_reservation_enabled(info.context.site.settings),
        )

    @classmethod
    def perform_mutation(cls, root, info, lines, checkout_id=None, token=None):
        return super().perform_mutation(
            root, info, lines, checkout_id, token, replace=True
        )


class CheckoutLinesDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        token = UUID(description="Checkout token.", required=True)
        lines_ids = graphene.List(
            graphene.ID,
            required=True,
            description="A list of checkout lines.",
        )

    class Meta:
        description = "Deletes checkout lines."
        error_type_class = CheckoutError

    @classmethod
    def validate_lines(cls, checkout, lines_to_delete):
        lines = checkout.lines.all()
        all_lines_ids = [str(line.id) for line in lines]
        invalid_line_ids = list()
        for line_to_delete in lines_to_delete:
            if line_to_delete not in all_lines_ids:
                line_to_delete = graphene.Node.to_global_id(
                    "CheckoutLine", line_to_delete
                )
                invalid_line_ids.append(line_to_delete)

        if invalid_line_ids:
            raise ValidationError(
                {
                    "line_id": ValidationError(
                        "Provided line_ids aren't part of checkout.",
                        params={"lines": invalid_line_ids},
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, lines_ids, token=None):
        checkout = get_checkout_by_token(token)

        _, lines_to_delete = resolve_global_ids_to_primary_keys(
            lines_ids, graphene_type="CheckoutLine", raise_error=True
        )
        cls.validate_lines(checkout, lines_to_delete)
        checkout.lines.filter(id__in=lines_to_delete).delete()

        lines = fetch_checkout_lines(checkout)

        manager = info.context.plugins
        checkout_info = fetch_checkout_info(
            checkout, lines, info.context.discounts, manager
        )
        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        manager.checkout_updated(checkout)
        return CheckoutLinesDelete(checkout=checkout)


class CheckoutLineDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        line_id = graphene.ID(description="ID of the checkout line to delete.")

    class Meta:
        description = "Deletes a CheckoutLine."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, line_id, checkout_id=None, token=None):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        line = cls.get_node_or_error(
            info, line_id, only_type=CheckoutLine, field="line_id"
        )

        if line and line in checkout.lines.all():
            line.delete()

        manager = info.context.plugins
        lines = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(
            checkout, lines, info.context.discounts, manager
        )
        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        manager.checkout_updated(checkout)
        return CheckoutLineDelete(checkout=checkout)


class CheckoutCustomerAttach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
        )
        customer_id = graphene.ID(
            required=False,
            description=(
                "ID of customer to attach to checkout. Can be used to attach customer "
                "to checkout by staff or app. Requires IMPERSONATE_USER permission."
            ),
        )
        token = UUID(description="Checkout token.", required=False)

    class Meta:
        description = "Sets the customer as the owner of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated or context.app

    @classmethod
    def perform_mutation(
        cls, _root, info, checkout_id=None, token=None, customer_id=None
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        # Raise error when trying to attach a user to a checkout
        # that is already owned by another user.
        if checkout.user_id:
            raise PermissionDenied()

        if customer_id:
            requestor = get_user_or_app_from_context(info.context)
            if not requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
                raise PermissionDenied()
            customer = cls.get_node_or_error(info, customer_id, only_type="User")
        else:
            customer = info.context.user

        checkout.user = customer
        checkout.email = customer.email
        checkout.save(update_fields=["email", "user", "last_change"])

        info.context.plugins.checkout_updated(checkout)
        return CheckoutCustomerAttach(checkout=checkout)


class CheckoutCustomerDetach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)

    class Meta:
        description = "Removes the user assigned as the owner of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated or context.app

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id=None, token=None):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        requestor = get_user_or_app_from_context(info.context)
        if not requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
            # Raise error if the current user doesn't own the checkout of the given ID.
            if checkout.user and checkout.user != info.context.user:
                raise PermissionDenied()

        checkout.user = None
        checkout.save(update_fields=["user", "last_change"])

        info.context.plugins.checkout_updated(checkout)
        return CheckoutCustomerDetach(checkout=checkout)


class CheckoutShippingAddressUpdate(BaseMutation, I18nMixin):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
        )
        token = UUID(description="Checkout token.", required=False)
        shipping_address = AddressInput(
            required=True,
            description="The mailing address to where the checkout will be shipped.",
        )

    class Meta:
        description = "Update shipping address in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def process_checkout_lines(
        cls,
        info,
        lines: Iterable["CheckoutLineInfo"],
        country: str,
        channel_slug: str,
    ) -> None:
        variant_ids = [line_info.variant.id for line_info in lines]
        variants = list(
            product_models.ProductVariant.objects.filter(
                id__in=variant_ids
            ).prefetch_related("product__product_type")
        )  # FIXME: is this prefetch needed?
        quantities = [line_info.line.quantity for line_info in lines]
        check_lines_quantity(
            variants,
            quantities,
            country,
            channel_slug,
            info.context.site.settings.limit_quantity_per_checkout,
            # Set replace=True to avoid existing_lines and quantities from
            # being counted twice by the check_stock_quantity_bulk
            replace=True,
            existing_lines=lines,
            check_reservations=is_reservation_enabled(info.context.site.settings),
        )

    @classmethod
    def perform_mutation(
        cls, _root, info, shipping_address, checkout_id=None, token=None
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(
                token,
                qs=models.Checkout.objects.prefetch_related(
                    "lines__variant__product__product_type"
                ),
            )
        # DEPRECATED
        if checkout_id:
            pk = cls.get_global_id_or_error(
                checkout_id, only_type=Checkout, field="checkout_id"
            )
            try:
                checkout = models.Checkout.objects.prefetch_related(
                    "lines__variant__product__product_type"
                ).get(pk=pk)
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "checkout_id": ValidationError(
                            f"Couldn't resolve to a node: {checkout_id}",
                            code=CheckoutErrorCode.NOT_FOUND,
                        )
                    }
                )

        lines = fetch_checkout_lines(checkout)
        if not is_shipping_required(lines):
            raise ValidationError(
                {
                    "shipping_address": ValidationError(
                        ERROR_DOES_NOT_SHIP,
                        code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED,
                    )
                }
            )

        shipping_address = cls.validate_address(
            shipping_address,
            address_type=AddressType.SHIPPING,
            instance=checkout.shipping_address,
            info=info,
        )

        discounts = info.context.discounts
        manager = info.context.plugins
        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        checkout_info = fetch_checkout_info(
            checkout, lines, discounts, manager, shipping_channel_listings
        )

        country = shipping_address.country.code
        checkout.set_country(country, commit=True)

        # Resolve and process the lines, validating variants quantities
        if lines:
            cls.process_checkout_lines(info, lines, country, checkout_info.channel.slug)

        update_checkout_shipping_method_if_invalid(checkout_info, lines)

        with traced_atomic_transaction():
            shipping_address.save()
            change_shipping_address_in_checkout(
                checkout_info,
                shipping_address,
                lines,
                discounts,
                manager,
                shipping_channel_listings,
            )
        recalculate_checkout_discount(manager, checkout_info, lines, discounts)

        manager.checkout_updated(checkout)
        return CheckoutShippingAddressUpdate(checkout=checkout)


class CheckoutBillingAddressUpdate(CheckoutShippingAddressUpdate):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} "
                "Use token instead."
            ),
        )
        token = UUID(description="Checkout token.", required=False)
        billing_address = AddressInput(
            required=True, description="The billing address of the checkout."
        )

    class Meta:
        description = "Update billing address in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(
        cls, _root, info, billing_address, checkout_id=None, token=None
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        billing_address = cls.validate_address(
            billing_address,
            address_type=AddressType.BILLING,
            instance=checkout.billing_address,
            info=info,
        )
        with traced_atomic_transaction():
            billing_address.save()
            change_billing_address_in_checkout(checkout, billing_address)
            info.context.plugins.checkout_updated(checkout)
        return CheckoutBillingAddressUpdate(checkout=checkout)


class CheckoutLanguageCodeUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
        )
        token = UUID(description="Checkout token.", required=False)
        language_code = graphene.Argument(
            LanguageCodeEnum, required=True, description="New language code."
        )

    class Meta:
        description = "Update language code in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, language_code, checkout_id=None, token=None):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        checkout.language_code = language_code
        checkout.save(update_fields=["language_code", "last_change"])
        info.context.plugins.checkout_updated(checkout)
        return CheckoutLanguageCodeUpdate(checkout=checkout)


class CheckoutEmailUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        email = graphene.String(required=True, description="email.")

    class Meta:
        description = "Updates email address in the existing checkout object."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @staticmethod
    def clean_email(email):
        if not email:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "This field cannot be blank.",
                        code=CheckoutErrorCode.REQUIRED.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, email, checkout_id=None, token=None):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        cls.clean_email(email)

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        checkout.email = email
        cls.clean_instance(info, checkout)
        checkout.save(update_fields=["email", "last_change"])
        info.context.plugins.checkout_updated(checkout)
        return CheckoutEmailUpdate(checkout=checkout)


class CheckoutShippingMethodUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        shipping_method_id = graphene.ID(required=True, description="Shipping method.")

    class Meta:
        description = "Updates the shipping method of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @staticmethod
    def _resolve_delivery_method_type(id_) -> Optional[str]:
        if id_ is None:
            return None

        possible_types = ("ShippingMethod", "app")
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
    def perform_mutation(
        cls, _root, info, shipping_method_id, checkout_id=None, token=None
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        manager = info.context.plugins
        lines = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(
            checkout, lines, info.context.discounts, manager
        )
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
        cls, info, shipping_method_id, checkout_info, lines, checkout, manager
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
        delivery_method = convert_to_shipping_method_data(
            shipping_method,
            shipping_models.ShippingMethodChannelListing.objects.filter(
                shipping_method=shipping_method,
                channel=checkout_info.channel,
            ).first(),
        )

        cls._check_delivery_method(
            checkout_info, lines, delivery_method=delivery_method
        )

        delete_external_shipping_id(checkout=checkout)
        checkout.shipping_method = shipping_method
        checkout.save(
            update_fields=["private_metadata", "shipping_method", "last_change"]
        )

        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        manager.checkout_updated(checkout)
        return CheckoutShippingMethodUpdate(checkout=checkout)

    @classmethod
    def perform_on_external_shipping_method(
        cls, info, shipping_method_id, checkout_info, lines, checkout, manager
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
        checkout.save(
            update_fields=["private_metadata", "shipping_method", "last_change"]
        )

        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        manager.checkout_updated(checkout)
        return CheckoutShippingMethodUpdate(checkout=checkout)


class CheckoutDeliveryMethodUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        token = UUID(description="Checkout token.", required=False)
        delivery_method_id = graphene.ID(
            description="Delivery Method ID (`Warehouse` ID or `ShippingMethod` ID).",
            required=False,
        )

    class Meta:
        description = (
            f"{ADDED_IN_31} Updates the delivery method "
            "(shipping method or pick up point) of the checkout."
        )
        error_type_class = CheckoutError

    @classmethod
    def perform_on_shipping_method(
        cls, info, shipping_method_id, checkout_info, lines, checkout, manager
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

        delivery_method = convert_to_shipping_method_data(
            shipping_method,
            shipping_models.ShippingMethodChannelListing.objects.filter(
                shipping_method=shipping_method,
                channel=checkout_info.channel,
            ).first(),
        )
        cls._check_delivery_method(
            checkout_info, lines, shipping_method=delivery_method, collection_point=None
        )

        cls._update_delivery_method(
            manager,
            checkout,
            shipping_method=shipping_method,
            external_shipping_method=None,
            collection_point=None,
        )
        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        return CheckoutDeliveryMethodUpdate(checkout=checkout)

    @classmethod
    def perform_on_external_shipping_method(
        cls, info, shipping_method_id, checkout_info, lines, checkout, manager
    ):
        delivery_method = manager.get_shipping_method(
            checkout=checkout,
            channel_slug=checkout.channel.slug,
            shipping_method_id=shipping_method_id,
        )

        cls._check_delivery_method(
            checkout_info, lines, shipping_method=delivery_method, collection_point=None
        )

        cls._update_delivery_method(
            manager,
            checkout,
            shipping_method=None,
            external_shipping_method=delivery_method,
            collection_point=None,
        )
        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        return CheckoutDeliveryMethodUpdate(checkout=checkout)

    @classmethod
    def perform_on_collection_point(
        cls, info, collection_point_id, checkout_info, lines, checkout, manager
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
            checkout,
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
        collection_point: Optional[Warehouse]
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

    @staticmethod
    def _update_delivery_method(
        manager,
        checkout: Checkout,
        *,
        shipping_method: Optional[ShippingMethod],
        external_shipping_method: Optional[shipping_interface.ShippingMethodData],
        collection_point: Optional[Warehouse]
    ) -> None:
        if external_shipping_method:
            set_external_shipping_id(
                checkout=checkout, app_shipping_id=external_shipping_method.id
            )
        else:
            delete_external_shipping_id(checkout=checkout)
        checkout.shipping_method = shipping_method
        checkout.collection_point = collection_point
        checkout.save(
            update_fields=[
                "private_metadata",
                "shipping_method",
                "collection_point",
                "last_change",
            ]
        )
        manager.checkout_updated(checkout)

    @staticmethod
    def _resolve_delivery_method_type(id_) -> Optional[str]:
        if id_ is None:
            return None

        possible_types = ("Warehouse", "ShippingMethod", "app")
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
        _,
        info,
        token,
        delivery_method_id=None,
    ):

        checkout = get_checkout_by_token(token)

        manager = info.context.plugins
        lines = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(
            checkout, lines, info.context.discounts, manager
        )
        if not is_shipping_required(lines):
            raise ValidationError(
                {
                    "delivery_method": ValidationError(
                        ERROR_DOES_NOT_SHIP,
                        code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED,
                    )
                }
            )
        type_name = cls._resolve_delivery_method_type(delivery_method_id)

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


class CheckoutComplete(BaseMutation):
    order = graphene.Field(Order, description="Placed order.")
    confirmation_needed = graphene.Boolean(
        required=True,
        default_value=False,
        description=(
            "Set to true if payment needs to be confirmed"
            " before checkout is complete."
        ),
    )
    confirmation_data = graphene.JSONString(
        required=False,
        description=(
            "Confirmation data used to process additional authorization steps."
        ),
    )

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        store_source = graphene.Boolean(
            default_value=False,
            description=(
                "Determines whether to store the payment source for future usage. "
                f"{DEPRECATED_IN_3X_INPUT} Use checkoutPaymentCreate for this action."
            ),
        )
        redirect_url = graphene.String(
            required=False,
            description=(
                "URL of a view where users should be redirected to "
                "see the order details. URL in RFC 1808 format."
            ),
        )
        payment_data = graphene.JSONString(
            required=False,
            description=(
                "Client-side generated data required to finalize the payment."
            ),
        )

    class Meta:
        description = (
            "Completes the checkout. As a result a new order is created and "
            "a payment charge is made. This action requires a successful "
            "payment before it can be performed. "
            "In case additional confirmation step as 3D secure is required "
            "confirmationNeeded flag will be set to True and no order created "
            "until payment is confirmed with second call of this mutation."
        )
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(
        cls, _root, info, store_source, checkout_id=None, token=None, **data
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        tracking_code = analytics.get_client_id(info.context)
        with transaction_with_commit_on_errors():
            try:
                if token:
                    checkout = get_checkout_by_token(token)
                # DEPRECATED
                else:
                    checkout = cls.get_node_or_error(
                        info,
                        checkout_id or token,
                        only_type=Checkout,
                        field="checkout_id",
                    )
            except ValidationError as e:
                # DEPRECATED
                if checkout_id:
                    token = cls.get_global_id_or_error(
                        checkout_id, only_type=Checkout, field="checkout_id"
                    )

                order = order_models.Order.objects.get_by_checkout_token(token)
                if order:
                    if not order.channel.is_active:
                        raise ValidationError(
                            {
                                "channel": ValidationError(
                                    "Cannot complete checkout with inactive channel.",
                                    code=CheckoutErrorCode.CHANNEL_INACTIVE.value,
                                )
                            }
                        )
                    # The order is already created. We return it as a success
                    # checkoutComplete response. Order is anonymized for not logged in
                    # user
                    return CheckoutComplete(
                        order=order, confirmation_needed=False, confirmation_data={}
                    )
                raise e

            validate_checkout_email(checkout)

            manager = info.context.plugins
            lines = fetch_checkout_lines(checkout)
            validate_variants_in_checkout_lines(lines)
            checkout_info = fetch_checkout_info(
                checkout, lines, info.context.discounts, manager
            )

            requestor = get_user_or_app_from_context(info.context)
            if requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
                # Allow impersonating user and process a checkout by using user details
                # assigned to checkout.
                customer = checkout.user or AnonymousUser()
            else:
                customer = info.context.user

            order, action_required, action_data = complete_checkout(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                payment_data=data.get("payment_data", {}),
                store_source=store_source,
                discounts=info.context.discounts,
                user=customer,
                app=info.context.app,
                site_settings=info.context.site.settings,
                tracking_code=tracking_code,
                redirect_url=data.get("redirect_url"),
            )
        # If gateway returns information that additional steps are required we need
        # to inform the frontend and pass all required data
        return CheckoutComplete(
            order=order,
            confirmation_needed=action_required,
            confirmation_data=action_data,
        )


class CheckoutAddPromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the added gift card or voucher."
    )

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        promo_code = graphene.String(
            description="Gift card code or voucher code.", required=True
        )

    class Meta:
        description = "Adds a gift card or a voucher to a checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, promo_code, checkout_id=None, token=None):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        validate_checkout_email(checkout)

        manager = info.context.plugins
        discounts = info.context.discounts
        lines = fetch_checkout_lines(checkout)
        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        checkout_info = fetch_checkout_info(
            checkout, lines, discounts, manager, shipping_channel_listings
        )

        add_promo_code_to_checkout(
            manager,
            checkout_info,
            lines,
            promo_code,
            discounts,
        )

        update_delivery_method_lists_for_checkout_info(
            checkout_info,
            checkout_info.checkout.shipping_method,
            checkout_info.checkout.collection_point,
            checkout_info.shipping_address,
            lines,
            discounts,
            manager,
            shipping_channel_listings,
        )

        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        manager.checkout_updated(checkout)
        return CheckoutAddPromoCode(checkout=checkout)


class CheckoutRemovePromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the removed gift card or voucher."
    )

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        promo_code = graphene.String(
            description="Gift card code or voucher code.", required=False
        )
        promo_code_id = graphene.ID(
            description="Gift card or voucher ID.",
            required=False,
        )

    class Meta:
        description = "Remove a gift card or a voucher from a checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info,
        checkout_id=None,
        token=None,
        promo_code=None,
        promo_code_id=None,
    ):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "promo_code", promo_code, "promo_code_id", promo_code_id
        )

        object_type, promo_code_pk = cls.clean_promo_code_id(promo_code_id)

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        manager = info.context.plugins
        checkout_info = fetch_checkout_info(
            checkout, [], info.context.discounts, manager
        )
        if promo_code:
            remove_promo_code_from_checkout(checkout_info, promo_code)
        else:
            cls.remove_promo_code_by_id(info, checkout, object_type, promo_code_pk)

        manager.checkout_updated(checkout)
        return CheckoutRemovePromoCode(checkout=checkout)

    @staticmethod
    def clean_promo_code_id(promo_code_id: Optional[str]):
        if promo_code_id is None:
            return None, None
        try:
            object_type, promo_code_pk = from_global_id_or_error(
                promo_code_id, raise_error=True
            )
        except GraphQLError as e:
            raise ValidationError(
                {
                    "promo_code_id": ValidationError(
                        str(e), code=CheckoutErrorCode.GRAPHQL_ERROR.value
                    )
                }
            )

        if object_type not in (str(Voucher), str(GiftCard)):
            raise ValidationError(
                {
                    "promo_code_id": ValidationError(
                        "Must receive Voucher or GiftCard id.",
                        code=CheckoutErrorCode.NOT_FOUND.value,
                    )
                }
            )

        return object_type, promo_code_pk

    @classmethod
    def remove_promo_code_by_id(
        cls, info, checkout: models.Checkout, object_type: str, promo_code_pk: int
    ):
        if object_type == str(Voucher) and checkout.voucher_code is not None:
            node = cls._get_node_by_pk(info, graphene_type=Voucher, pk=promo_code_pk)
            if node is None:
                raise ValidationError(
                    {
                        "promo_code_id": ValidationError(
                            f"Couldn't resolve to a node: {promo_code_pk}",
                            code=CheckoutErrorCode.NOT_FOUND.value,
                        )
                    }
                )
            if checkout.voucher_code == node.code:
                remove_voucher_from_checkout(checkout)
        else:
            checkout.gift_cards.remove(promo_code_pk)
