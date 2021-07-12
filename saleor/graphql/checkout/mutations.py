import datetime
import uuid
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

import graphene
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q

from ...checkout import AddressType, models
from ...checkout.complete_checkout import complete_checkout
from ...checkout.error_codes import CheckoutErrorCode
from ...checkout.fetch import (
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
    get_valid_shipping_method_list_for_checkout_info,
    update_checkout_info_shipping_method,
)
from ...checkout.utils import (
    add_promo_code_to_checkout,
    add_variants_to_checkout,
    calculate_checkout_quantity,
    change_billing_address_in_checkout,
    change_shipping_address_in_checkout,
    is_shipping_required,
    recalculate_checkout_discount,
    remove_promo_code_from_checkout,
    validate_variants_in_checkout_lines,
)
from ...core import analytics
from ...core.exceptions import InsufficientStock, PermissionDenied, ProductNotPublished
from ...core.tracing import traced_atomic_transaction
from ...core.transactions import transaction_with_commit_on_errors
from ...order import models as order_models
from ...product import models as product_models
from ...product.models import ProductChannelListing
from ...shipping import models as shipping_models
from ...warehouse.availability import check_stock_quantity_bulk
from ..account.i18n import I18nMixin
from ..account.types import AddressInput
from ..channel.utils import clean_channel
from ..core.enums import LanguageCodeEnum
from ..core.mutations import BaseMutation, ModelMutation
from ..core.scalars import UUID
from ..core.types.common import CheckoutError
from ..core.validators import (
    validate_one_of_args_is_in_mutation,
    validate_variants_available_in_channel,
)
from ..order.types import Order
from ..product.types import ProductVariant
from ..shipping.types import ShippingMethod
from ..utils import get_user_country_context
from .types import Checkout, CheckoutLine
from .utils import prepare_insufficient_stock_checkout_validation_error

ERROR_DOES_NOT_SHIP = "This checkout doesn't need shipping"


if TYPE_CHECKING:
    from ...account.models import Address
    from ...checkout.fetch import CheckoutInfo


def clean_shipping_method(
    checkout_info: "CheckoutInfo",
    lines: Iterable[CheckoutLineInfo],
    method: Optional[models.ShippingMethod],
) -> bool:
    """Check if current shipping method is valid."""

    if not method:
        # no shipping method was provided, it is valid
        return True

    if not is_shipping_required(lines):
        raise ValidationError(
            ERROR_DOES_NOT_SHIP, code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED.value
        )

    if not checkout_info.shipping_address:
        raise ValidationError(
            "Cannot choose a shipping method for a checkout without the "
            "shipping address.",
            code=CheckoutErrorCode.SHIPPING_ADDRESS_NOT_SET.value,
        )

    valid_methods = checkout_info.valid_shipping_methods
    return method in valid_methods


def update_checkout_shipping_method_if_invalid(
    checkout_info: "CheckoutInfo", lines: Iterable[CheckoutLineInfo]
):
    checkout = checkout_info.checkout
    quantity = calculate_checkout_quantity(lines)
    # remove shipping method when empty checkout
    if quantity == 0 or not is_shipping_required(lines):
        checkout.shipping_method = None
        checkout_info.shipping_method = None
        checkout_info.shipping_method_channel_listings = None
        checkout.save(update_fields=["shipping_method", "last_change"])

    is_valid = clean_shipping_method(
        checkout_info=checkout_info,
        lines=lines,
        method=checkout_info.shipping_method,
    )

    if not is_valid:
        cheapest_alternative = checkout_info.valid_shipping_methods
        new_shipping_method = cheapest_alternative[0] if cheapest_alternative else None
        checkout.shipping_method = new_shipping_method
        update_checkout_info_shipping_method(checkout_info, new_shipping_method)
        checkout.save(update_fields=["shipping_method", "last_change"])


def check_lines_quantity(
    variants, quantities, country, channel_slug, allow_zero_quantity=False
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

        if quantity > settings.MAX_CHECKOUT_LINE_QUANTITY:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "Cannot add more than %d times this item."
                        "" % settings.MAX_CHECKOUT_LINE_QUANTITY,
                        code=CheckoutErrorCode.QUANTITY_GREATER_THAN_LIMIT,
                    )
                }
            )
    try:
        check_stock_quantity_bulk(variants, country, quantities, channel_slug)
    except InsufficientStock as e:
        errors = [
            ValidationError(
                f"Could not add items {item.variant}. "
                f"Only {item.available_quantity} remaining in stock.",
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
        error_code = CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines for unavailable for purchase variants.",
                    code=error_code,  # type: ignore
                    params={"variants": variant_ids},
                )
            }
        )


def get_checkout_by_token(token: uuid.UUID, prefetch_lookups: Iterable[str] = []):
    try:
        checkout = models.Checkout.objects.prefetch_related(*prefetch_lookups).get(
            token=token
        )
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
            "DEPRECATED: Will be removed in Saleor 4.0. Always returns True."
        ),
    )

    class Arguments:
        input = CheckoutCreateInput(
            required=True, description="Fields required to create checkout."
        )

    class Meta:
        description = "Create a new checkout."
        model = models.Checkout
        return_field_name = "checkout"
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def clean_checkout_lines(
        cls, lines, country, channel
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

        quantities = [line["quantity"] for line in lines]
        variant_db_ids = {variant.id for variant in variants}
        validate_variants_available_for_purchase(variant_db_ids, channel.id)
        validate_variants_available_in_channel(
            variant_db_ids, channel.id, CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL
        )
        check_lines_quantity(variants, quantities, country, channel.slug)
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
        country = get_user_country_context(
            destination_address=shipping_address,
            company_address=info.context.site.settings.company_address,
        )

        # Resolve and process the lines, retrieving the variants and quantities
        lines = data.pop("lines", None)
        if lines:
            (
                cleaned_input["variants"],
                cleaned_input["quantities"],
            ) = cls.clean_checkout_lines(lines, country, cleaned_input["channel"])

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
        channel = cleaned_input["channel"]
        # Create the checkout object
        instance.save()

        # Set checkout country
        country = cleaned_input["country"]
        instance.set_country(country)

        # Create checkout lines
        variants = cleaned_input.get("variants")
        quantities = cleaned_input.get("quantities")
        if variants and quantities:
            try:
                add_variants_to_checkout(instance, variants, quantities, channel.slug)
            except InsufficientStock as exc:
                error = prepare_insufficient_stock_checkout_validation_error(exc)
                raise ValidationError({"lines": error})
            except ProductNotPublished as exc:
                raise ValidationError(
                    "Can't create checkout with unpublished product.",
                    code=exc.code,
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
                "The ID of the checkout."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
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
    def validate_checkout_lines(cls, variants, quantities, country, channel_slug):
        check_lines_quantity(variants, quantities, country, channel_slug)

    @classmethod
    def clean_input(
        cls, checkout, variants, quantities, checkout_info, manager, discounts, replace
    ):
        channel_slug = checkout_info.channel.slug
        cls.validate_checkout_lines(
            variants, quantities, checkout.get_country(), channel_slug
        )
        variants_db_ids = {variant.id for variant in variants}
        validate_variants_available_for_purchase(variants_db_ids, checkout.channel_id)
        validate_variants_available_in_channel(
            variants_db_ids,
            checkout.channel_id,
            CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL,
        )

        if variants and quantities:
            try:
                checkout = add_variants_to_checkout(
                    checkout,
                    variants,
                    quantities,
                    channel_slug,
                    skip_stock_check=True,  # already checked by validate_checkout_lines
                    replace=replace,
                )
            except ProductNotPublished as exc:
                raise ValidationError(
                    "Can't add unpublished product.",
                    code=exc.code,
                )

        lines = fetch_checkout_lines(checkout)
        checkout_info.valid_shipping_methods = (
            get_valid_shipping_method_list_for_checkout_info(
                checkout_info, checkout_info.shipping_address, lines, discounts, manager
            )
        )

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
        quantities = [line.get("quantity") for line in lines]

        checkout_info = fetch_checkout_info(checkout, [], discounts, manager)
        cls.clean_input(
            checkout, variants, quantities, checkout_info, manager, discounts, replace
        )

        lines = fetch_checkout_lines(checkout)
        checkout_info.valid_shipping_methods = (
            get_valid_shipping_method_list_for_checkout_info(
                checkout_info, checkout_info.shipping_address, lines, discounts, manager
            )
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
    def validate_checkout_lines(cls, variants, quantities, country, channel_slug):
        check_lines_quantity(
            variants, quantities, country, channel_slug, allow_zero_quantity=True
        )

    @classmethod
    def perform_mutation(cls, root, info, lines, checkout_id=None, token=None):
        return super().perform_mutation(
            root, info, lines, checkout_id, token, replace=True
        )


class CheckoutLineDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                "The ID of the checkout."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
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
                "ID of the checkout."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
            ),
        )
        token = UUID(description="Checkout token.", required=False)

    class Meta:
        description = "Sets the customer as the owner of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

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

        checkout.user = info.context.user
        checkout.email = info.context.user.email
        checkout.save(update_fields=["email", "user", "last_change"])

        info.context.plugins.checkout_updated(checkout)
        return CheckoutCustomerAttach(checkout=checkout)


class CheckoutCustomerDetach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                "Checkout ID."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
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
        return context.user.is_authenticated

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
                "ID of the checkout."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
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
        cls, lines: Iterable["CheckoutLineInfo"], country: str, channel_slug: str
    ) -> None:
        variant_ids = [line_info.variant.id for line_info in lines]
        variants = list(
            product_models.ProductVariant.objects.filter(
                id__in=variant_ids
            ).prefetch_related("product__product_type")
        )  # FIXME: is this prefetch needed?
        quantities = [line_info.line.quantity for line_info in lines]
        check_lines_quantity(variants, quantities, country, channel_slug)

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
                token, prefetch_lookups=["lines__variant__product__product_type"]
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
        checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)

        country = get_user_country_context(
            destination_address=shipping_address,
            company_address=info.context.site.settings.company_address,
        )
        checkout.set_country(country, commit=True)

        # Resolve and process the lines, validating variants quantities
        if lines:
            cls.process_checkout_lines(lines, country, checkout_info.channel.slug)

        update_checkout_shipping_method_if_invalid(checkout_info, lines)

        with traced_atomic_transaction():
            shipping_address.save()
            change_shipping_address_in_checkout(
                checkout_info, shipping_address, lines, discounts, manager
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
                "ID of the checkout."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
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
                "ID of the checkout."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
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
                "Checkout ID."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        email = graphene.String(required=True, description="email.")

    class Meta:
        description = "Updates email address in the existing checkout object."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, email, checkout_id=None, token=None):
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
                "Checkout ID."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        shipping_method_id = graphene.ID(required=True, description="Shipping method.")

    class Meta:
        description = "Updates the shipping address of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

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
                        code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED,
                    )
                }
            )

        shipping_method = cls.get_node_or_error(
            info,
            shipping_method_id,
            only_type=ShippingMethod,
            field="shipping_method_id",
            qs=shipping_models.ShippingMethod.objects.prefetch_related(
                "postal_code_rules"
            ),
        )

        shipping_method_is_valid = clean_shipping_method(
            checkout_info=checkout_info,
            lines=lines,
            method=shipping_method,
        )
        if not shipping_method_is_valid:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "This shipping method is not applicable.",
                        code=CheckoutErrorCode.SHIPPING_METHOD_NOT_APPLICABLE,
                    )
                }
            )

        checkout.shipping_method = shipping_method
        checkout.save(update_fields=["shipping_method", "last_change"])
        recalculate_checkout_discount(
            manager, checkout_info, lines, info.context.discounts
        )
        manager.checkout_updated(checkout)
        return CheckoutShippingMethodUpdate(checkout=checkout)


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
                "Checkout ID."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        store_source = graphene.Boolean(
            default_value=False,
            description=(
                "Determines whether to store the payment source for future usage."
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

            manager = info.context.plugins
            lines = fetch_checkout_lines(checkout)
            validate_variants_in_checkout_lines(lines)
            checkout_info = fetch_checkout_info(
                checkout, lines, info.context.discounts, manager
            )
            order, action_required, action_data = complete_checkout(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                payment_data=data.get("payment_data", {}),
                store_source=store_source,
                discounts=info.context.discounts,
                user=info.context.user,
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
                "Checkout ID. "
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
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

        manager = info.context.plugins
        lines = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(
            checkout, lines, info.context.discounts, manager
        )

        if info.context.user and checkout.user == info.context.user:
            # reassign user from request to make sure that we will take into account
            # that user can have granted staff permissions from external resources.
            # Which is required to determine if user has access to 'staff discount'
            checkout_info.user = info.context.user

        add_promo_code_to_checkout(
            manager,
            checkout_info,
            lines,
            promo_code,
            info.context.discounts,
        )
        manager.checkout_updated(checkout)
        return CheckoutAddPromoCode(checkout=checkout)


class CheckoutRemovePromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the removed gift card or voucher."
    )

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                "Checkout ID."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        promo_code = graphene.String(
            description="Gift card code or voucher code.", required=True
        )

    class Meta:
        description = "Remove a gift card or a voucher from a checkout."
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

        manager = info.context.plugins
        checkout_info = fetch_checkout_info(
            checkout, [], info.context.discounts, manager
        )
        remove_promo_code_from_checkout(checkout_info, promo_code)
        manager.checkout_updated(checkout)
        return CheckoutRemovePromoCode(checkout=checkout)
