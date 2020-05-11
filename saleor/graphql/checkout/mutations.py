from typing import List, Optional, Tuple

import graphene
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Prefetch
from graphql_jwt.exceptions import PermissionDenied

from ...account.error_codes import AccountErrorCode
from ...checkout import models
from ...checkout.error_codes import CheckoutErrorCode
from ...checkout.utils import (
    abort_order_data,
    add_promo_code_to_checkout,
    add_variant_to_checkout,
    change_billing_address_in_checkout,
    change_shipping_address_in_checkout,
    clean_checkout,
    create_order,
    get_user_checkout,
    get_valid_shipping_methods_for_checkout,
    prepare_order_data,
    recalculate_checkout_discount,
    remove_promo_code_from_checkout,
)
from ...core import analytics
from ...core.exceptions import InsufficientStock
from ...core.permissions import OrderPermissions
from ...core.taxes import TaxError
from ...core.utils.url import validate_storefront_url
from ...discount import models as voucher_model
from ...payment import PaymentError, gateway, models as payment_models
from ...payment.interface import AddressData
from ...payment.utils import store_customer_id
from ...product import models as product_models
from ...warehouse.availability import check_stock_quantity, get_available_quantity
from ..account.i18n import I18nMixin
from ..account.types import AddressInput
from ..core.mutations import BaseMutation, ModelMutation
from ..core.types.common import CheckoutError
from ..core.utils import from_global_id_strict_type
from ..meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
from ..order.types import Order
from ..product.types import ProductVariant
from ..shipping.types import ShippingMethod
from .types import Checkout, CheckoutLine

ERROR_DOES_NOT_SHIP = "This checkout doesn't need shipping"


def clean_shipping_method(
    checkout: models.Checkout,
    lines: List[models.CheckoutLine],
    method: Optional[models.ShippingMethod],
    discounts,
) -> bool:
    """Check if current shipping method is valid."""

    if not method:
        # no shipping method was provided, it is valid
        return True

    if not checkout.is_shipping_required():
        raise ValidationError(
            ERROR_DOES_NOT_SHIP, code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED.value
        )

    if not checkout.shipping_address:
        raise ValidationError(
            "Cannot choose a shipping method for a checkout without the "
            "shipping address.",
            code=CheckoutErrorCode.SHIPPING_ADDRESS_NOT_SET.value,
        )

    valid_methods = get_valid_shipping_methods_for_checkout(checkout, lines, discounts)
    return method in valid_methods


def update_checkout_shipping_method_if_invalid(
    checkout: models.Checkout, lines: List[models.CheckoutLine], discounts
):
    # remove shipping method when empty checkout
    if checkout.quantity == 0 or not checkout.is_shipping_required():
        checkout.shipping_method = None
        checkout.save(update_fields=["shipping_method", "last_change"])

    is_valid = clean_shipping_method(
        checkout=checkout,
        lines=lines,
        method=checkout.shipping_method,
        discounts=discounts,
    )

    if not is_valid:
        cheapest_alternative = get_valid_shipping_methods_for_checkout(
            checkout, lines, discounts
        ).first()
        checkout.shipping_method = cheapest_alternative
        checkout.save(update_fields=["shipping_method", "last_change"])


def check_lines_quantity(variants, quantities, country):
    """Check if stock is sufficient for each line in the list of dicts."""
    for variant, quantity in zip(variants, quantities):
        if quantity < 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "The quantity should be higher than zero.",
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
            check_stock_quantity(variant, country, quantity)
        except InsufficientStock as e:
            available_quantity = get_available_quantity(e.item, country)
            message = (
                "Could not add item "
                + "%(item_name)s. Only %(remaining)d remaining in stock."
                % {
                    "remaining": available_quantity,
                    "item_name": e.item.display_product(),
                }
            )
            raise ValidationError({"quantity": ValidationError(message, code=e.code)})


class CheckoutLineInput(graphene.InputObjectType):
    quantity = graphene.Int(required=True, description="The number of items purchased.")
    variant_id = graphene.ID(required=True, description="ID of the product variant.")


class CheckoutCreateInput(graphene.InputObjectType):
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


class CheckoutCreate(ModelMutation, I18nMixin):
    created = graphene.Field(
        graphene.Boolean,
        description=(
            "Whether the checkout was created or the current active one was returned. "
            "Refer to checkoutLinesAdd and checkoutLinesUpdate to merge a cart "
            "with an active checkout."
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
    def process_checkout_lines(
        cls, lines, country
    ) -> Tuple[List[product_models.ProductVariant], List[int]]:
        variant_ids = [line.get("variant_id") for line in lines]
        variants = cls.get_nodes_or_error(
            variant_ids,
            "variant_id",
            ProductVariant,
            qs=product_models.ProductVariant.objects.prefetch_related(
                "product__product_type"
            ),
        )
        quantities = [line.get("quantity") for line in lines]

        check_lines_quantity(variants, quantities, country)

        return variants, quantities

    @classmethod
    def retrieve_shipping_address(cls, user, data: dict) -> Optional[models.Address]:
        if data.get("shipping_address") is not None:
            return cls.validate_address(data["shipping_address"])
        if user.is_authenticated:
            return user.default_shipping_address
        return None

    @classmethod
    def retrieve_billing_address(cls, user, data: dict) -> Optional[models.Address]:
        if data.get("billing_address") is not None:
            return cls.validate_address(data["billing_address"])
        if user.is_authenticated:
            return user.default_billing_address
        return None

    @classmethod
    def clean_input(cls, info, instance: models.Checkout, data, input_cls=None):
        cleaned_input = super().clean_input(info, instance, data)
        user = info.context.user
        country = info.context.country.code

        # Resolve and process the lines, retrieving the variants and quantities
        lines = data.pop("lines", None)
        if lines:
            (
                cleaned_input["variants"],
                cleaned_input["quantities"],
            ) = cls.process_checkout_lines(lines, country)

        cleaned_input["shipping_address"] = cls.retrieve_shipping_address(user, data)
        cleaned_input["billing_address"] = cls.retrieve_billing_address(user, data)

        # Use authenticated user's email as default email
        if user.is_authenticated:
            email = data.pop("email", None)
            cleaned_input["email"] = email or user.email

        return cleaned_input

    @classmethod
    def save_addresses(cls, instance: models.Checkout, cleaned_input: dict):
        shipping_address = cleaned_input.get("shipping_address")
        billing_address = cleaned_input.get("billing_address")

        updated_fields = ["last_change"]

        if shipping_address and instance.is_shipping_required():
            shipping_address.save()
            instance.shipping_address = shipping_address.get_copy()
            updated_fields.append("shipping_address")
        if billing_address:
            billing_address.save()
            instance.billing_address = billing_address.get_copy()
            updated_fields.append("billing_address")

        # Note django will simply return if the list is empty
        instance.save(update_fields=updated_fields)

    @classmethod
    @transaction.atomic()
    def save(cls, info, instance: models.Checkout, cleaned_input):
        # Create the checkout object
        instance.save()
        country = info.context.country
        instance.set_country(country.code, commit=True)

        # Retrieve the lines to create
        variants = cleaned_input.get("variants")
        quantities = cleaned_input.get("quantities")

        # Create the checkout lines
        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                try:
                    add_variant_to_checkout(instance, variant, quantity)
                except InsufficientStock as exc:
                    raise ValidationError(
                        f"Insufficient product stock: {exc.item}", code=exc.code
                    )

        # Save provided addresses and associate them to the checkout
        cls.save_addresses(instance, cleaned_input)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        user = info.context.user

        # `perform_mutation` is overridden to properly get or create a checkout
        # instance here and abort mutation if needed.
        if user.is_authenticated:
            checkout, _ = get_user_checkout(user)

            if checkout is not None:
                # If user has an active checkout, return it without any
                # modifications.
                return CheckoutCreate(checkout=checkout, created=False)

            checkout = models.Checkout(user=user)
        else:
            checkout = models.Checkout()

        cleaned_input = cls.clean_input(info, checkout, data.get("input"))
        checkout = cls.construct_instance(checkout, cleaned_input)
        cls.clean_instance(info, checkout)
        cls.save(info, checkout, cleaned_input)
        cls._save_m2m(info, checkout, cleaned_input)
        return CheckoutCreate(checkout=checkout, created=True)


class CheckoutLinesAdd(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(description="The ID of the checkout.", required=True)
        lines = graphene.List(
            CheckoutLineInput,
            required=True,
            description=(
                "A list of checkout lines, each containing information about "
                "an item in the checkout."
            ),
        )

    class Meta:
        description = "Adds a checkout line to the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, lines, replace=False):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        variant_ids = [line.get("variant_id") for line in lines]
        variants = cls.get_nodes_or_error(variant_ids, "variant_id", ProductVariant)
        quantities = [line.get("quantity") for line in lines]

        check_lines_quantity(variants, quantities, checkout.get_country())

        if variants and quantities:
            for variant, quantity in zip(variants, quantities):
                try:
                    add_variant_to_checkout(
                        checkout, variant, quantity, replace=replace
                    )
                except InsufficientStock as exc:
                    raise ValidationError(
                        f"Insufficient product stock: {exc.item}", code=exc.code
                    )

        lines = list(checkout)

        update_checkout_shipping_method_if_invalid(
            checkout, lines, info.context.discounts
        )
        recalculate_checkout_discount(checkout, lines, info.context.discounts)

        return CheckoutLinesAdd(checkout=checkout)


class CheckoutLinesUpdate(CheckoutLinesAdd):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Meta:
        description = "Updates checkout line in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, root, info, checkout_id, lines):
        return super().perform_mutation(root, info, checkout_id, lines, replace=True)


class CheckoutLineDelete(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(description="The ID of the checkout.", required=True)
        line_id = graphene.ID(description="ID of the checkout line to delete.")

    class Meta:
        description = "Deletes a CheckoutLine."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, line_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        line = cls.get_node_or_error(
            info, line_id, only_type=CheckoutLine, field="line_id"
        )

        if line and line in checkout.lines.all():
            line.delete()

        lines = list(checkout)

        update_checkout_shipping_method_if_invalid(
            checkout, lines, info.context.discounts
        )
        recalculate_checkout_discount(checkout, lines, info.context.discounts)

        return CheckoutLineDelete(checkout=checkout)


class CheckoutCustomerAttach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(required=True, description="ID of the checkout.")
        customer_id = graphene.ID(
            required=False,
            description=(
                "[Deprecated] The ID of the customer. To identify a customer you "
                "should authenticate with JWT. This field will be removed after "
                "2020-07-31."
            ),
        )

    class Meta:
        description = "Sets the customer as the owner of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, customer_id=None):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        # Check if provided customer_id matches with the authenticated user and raise
        # error if it doesn't. This part can be removed when `customer_id` field is
        # removed.
        if customer_id:
            current_user_id = graphene.Node.to_global_id("User", info.context.user.id)
            if current_user_id != customer_id:
                raise PermissionDenied()

        checkout.user = info.context.user
        checkout.save(update_fields=["user", "last_change"])
        return CheckoutCustomerAttach(checkout=checkout)


class CheckoutCustomerDetach(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID.", required=True)

    class Meta:
        description = "Removes the user assigned as the owner of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.is_authenticated

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        # Raise error if the current user doesn't own the checkout of the given ID.
        if checkout.user and checkout.user != info.context.user:
            raise PermissionDenied()

        checkout.user = None
        checkout.save(update_fields=["user", "last_change"])
        return CheckoutCustomerDetach(checkout=checkout)


class CheckoutShippingAddressUpdate(BaseMutation, I18nMixin):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(required=True, description="ID of the checkout.")
        shipping_address = AddressInput(
            required=True,
            description="The mailing address to where the checkout will be shipped.",
        )

    class Meta:
        description = "Update shipping address in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, shipping_address):
        pk = from_global_id_strict_type(checkout_id, Checkout, field="checkout_id")

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

        if not checkout.is_shipping_required():
            raise ValidationError(
                {
                    "shipping_address": ValidationError(
                        ERROR_DOES_NOT_SHIP,
                        code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED,
                    )
                }
            )

        shipping_address = cls.validate_address(
            shipping_address, instance=checkout.shipping_address, info=info
        )

        lines = list(checkout)

        update_checkout_shipping_method_if_invalid(
            checkout, lines, info.context.discounts
        )

        with transaction.atomic():
            shipping_address.save()
            change_shipping_address_in_checkout(checkout, shipping_address)
        recalculate_checkout_discount(checkout, lines, info.context.discounts)

        return CheckoutShippingAddressUpdate(checkout=checkout)


class CheckoutBillingAddressUpdate(CheckoutShippingAddressUpdate):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(required=True, description="ID of the checkout.")
        billing_address = AddressInput(
            required=True, description="The billing address of the checkout."
        )

    class Meta:
        description = "Update billing address in the existing checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, billing_address):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        billing_address = cls.validate_address(
            billing_address, instance=checkout.billing_address, info=info
        )
        with transaction.atomic():
            billing_address.save()
            change_billing_address_in_checkout(checkout, billing_address)
        return CheckoutBillingAddressUpdate(checkout=checkout)


class CheckoutEmailUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID.")
        email = graphene.String(required=True, description="email.")

    class Meta:
        description = "Updates email address in the existing checkout object."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, email):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )

        checkout.email = email
        cls.clean_instance(info, checkout)
        checkout.save(update_fields=["email", "last_change"])
        return CheckoutEmailUpdate(checkout=checkout)


class CheckoutShippingMethodUpdate(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID.")
        shipping_method_id = graphene.ID(required=True, description="Shipping method.")

    class Meta:
        description = "Updates the shipping address of the checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, shipping_method_id):
        pk = from_global_id_strict_type(
            checkout_id, only_type=Checkout, field="checkout_id"
        )

        try:
            checkout = models.Checkout.objects.prefetch_related(
                "lines__variant__product__collections",
                "lines__variant__product__product_type",
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

        if not checkout.is_shipping_required():
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
        )

        lines = list(checkout)
        shipping_method_is_valid = clean_shipping_method(
            checkout=checkout,
            lines=lines,
            method=shipping_method,
            discounts=info.context.discounts,
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
        recalculate_checkout_discount(checkout, lines, info.context.discounts)

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

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID.", required=True)
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
    def perform_mutation(cls, _root, info, checkout_id, store_source, **data):
        checkout = cls.get_node_or_error(
            info,
            checkout_id,
            only_type=Checkout,
            field="checkout_id",
            qs=models.Checkout.objects.prefetch_related(
                "gift_cards",
                "lines",
                Prefetch(
                    "payments",
                    queryset=payment_models.Payment.objects.prefetch_related(
                        "order", "order__lines"
                    ),
                ),
            ).select_related("shipping_method", "shipping_method__shipping_zone"),
        )
        lines = list(checkout)

        discounts = info.context.discounts
        user = info.context.user
        clean_checkout(checkout, list(checkout), discounts)

        payment = checkout.get_last_active_payment()

        with transaction.atomic():
            try:
                order_data = prepare_order_data(
                    checkout=checkout,
                    lines=lines,
                    tracking_code=analytics.get_client_id(info.context),
                    discounts=discounts,
                )
            except InsufficientStock as e:
                raise ValidationError(
                    f"Insufficient product stock: {e.item}", code=e.code
                )
            except voucher_model.NotApplicable:
                raise ValidationError(
                    "Voucher not applicable",
                    code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE,
                )
            except TaxError as tax_error:
                raise ValidationError(
                    "Unable to calculate taxes - %s" % str(tax_error),
                    code=CheckoutErrorCode.TAX_ERROR,
                )

        billing_address = order_data["billing_address"]
        shipping_address = order_data.get("shipping_address", None)

        billing_address = AddressData(**billing_address.as_data())

        if shipping_address is not None:
            shipping_address = AddressData(**shipping_address.as_data())

        payment_confirmation = payment.to_confirm
        try:
            if payment_confirmation:
                txn = gateway.confirm(payment)
            else:
                txn = gateway.process_payment(
                    payment=payment, token=payment.token, store_source=store_source
                )

            if not txn.is_success:
                raise PaymentError(txn.error)

        except PaymentError as e:
            abort_order_data(order_data)
            raise ValidationError(str(e), code=CheckoutErrorCode.PAYMENT_ERROR)

        if txn.customer_id and user.is_authenticated:
            store_customer_id(user, payment.gateway, txn.customer_id)

        redirect_url = data.get("redirect_url", "")
        if redirect_url:
            try:
                validate_storefront_url(redirect_url)
            except ValidationError as error:
                raise ValidationError(
                    {"redirect_url": error}, code=AccountErrorCode.INVALID
                )

        order = None
        if not txn.action_required:
            # create the order into the database
            order = create_order(
                checkout=checkout,
                order_data=order_data,
                user=user,
                redirect_url=redirect_url,
            )

            # remove checkout after order is successfully paid
            checkout.delete()

            # return the success response with the newly created order data
            return CheckoutComplete(order=order, confirmation_needed=False)

        return CheckoutComplete(order=None, confirmation_needed=True)


class CheckoutAddPromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the added gift card or voucher."
    )

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID.", required=True)
        promo_code = graphene.String(
            description="Gift card code or voucher code.", required=True
        )

    class Meta:
        description = "Adds a gift card or a voucher to a checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, promo_code):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        lines = list(checkout)
        add_promo_code_to_checkout(checkout, lines, promo_code, info.context.discounts)
        return CheckoutAddPromoCode(checkout=checkout)


class CheckoutRemovePromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the removed gift card or voucher."
    )

    class Arguments:
        checkout_id = graphene.ID(description="Checkout ID.", required=True)
        promo_code = graphene.String(
            description="Gift card code or voucher code.", required=True
        )

    class Meta:
        description = "Remove a gift card or a voucher from a checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id, promo_code):
        checkout = cls.get_node_or_error(
            info, checkout_id, only_type=Checkout, field="checkout_id"
        )
        remove_promo_code_from_checkout(checkout, promo_code)
        return CheckoutRemovePromoCode(checkout=checkout)


class CheckoutUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates metadata for checkout."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        model = models.Checkout
        public = True
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"


class CheckoutUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates private metadata for checkout."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        model = models.Checkout
        public = False
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"


class CheckoutClearMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clear metadata for checkout."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        model = models.Checkout
        public = True
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"


class CheckoutClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clear private metadata for checkout."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        model = models.Checkout
        public = False
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
