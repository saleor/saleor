from typing import List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from .....checkout import models as checkout_models
from .....checkout.calculations import calculate_checkout_total_with_gift_cards
from .....checkout.checkout_cleaner import (
    clean_billing_address,
    clean_checkout_shipping,
)
from .....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from .....checkout.utils import cancel_active_payments
from .....core.error_codes import MetadataErrorCode
from .....core.utils import get_client_ip
from .....core.utils.url import validate_storefront_url
from .....payment import StorePaymentMethod
from .....payment.error_codes import PaymentErrorCode
from .....payment.utils import create_payment, is_currency_supported
from ....account.i18n import I18nMixin
from ....checkout.mutations.utils import get_checkout
from ....checkout.types import Checkout
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_31, ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ....core.doc_category import DOC_CATEGORY_CHECKOUT, DOC_CATEGORY_PAYMENTS
from ....core.mutations import BaseMutation
from ....core.scalars import UUID, PositiveDecimal
from ....core.types import BaseInputObjectType
from ....core.types import common as common_types
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ...enums import StorePaymentMethodEnum
from ...types import Payment
from ...utils import metadata_contains_empty_key


class PaymentInput(BaseInputObjectType):
    gateway = graphene.Field(
        graphene.String,
        description="A gateway to use with that payment.",
        required=True,
    )
    token = graphene.String(
        required=False,
        description=(
            "Client-side generated payment token, representing customer's "
            "billing data in a secure manner."
        ),
    )
    amount = PositiveDecimal(
        required=False,
        description=(
            "Total amount of the transaction, including "
            "all taxes and discounts. If no amount is provided, "
            "the checkout total will be used."
        ),
    )
    return_url = graphene.String(
        required=False,
        description=(
            "URL of a storefront view where user should be redirected after "
            "requiring additional actions. Payment with additional actions will not be "
            "finished if this field is not provided."
        ),
    )
    store_payment_method = StorePaymentMethodEnum(
        description="Payment store type." + ADDED_IN_31,
        required=False,
        default_value=StorePaymentMethodEnum.NONE.name,
    )
    metadata = common_types.NonNullList(
        MetadataInput,
        description="User public metadata." + ADDED_IN_31,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class CheckoutPaymentCreate(BaseMutation, I18nMixin):
    checkout = graphene.Field(Checkout, description="Related checkout object.")
    payment = graphene.Field(Payment, description="A newly created payment.")

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
        input = PaymentInput(
            description="Data required to create a new payment.", required=True
        )

    class Meta:
        description = "Create a new payment for given checkout."
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def clean_payment_amount(cls, info: ResolveInfo, checkout_total, amount):
        if amount != checkout_total.gross.amount:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Partial payments are not allowed, amount should be "
                        "equal checkout's total.",
                        code=PaymentErrorCode.PARTIAL_PAYMENT_NOT_ALLOWED.value,
                    )
                }
            )

    @classmethod
    def validate_gateway(cls, manager, gateway_id, checkout):
        """Validate if given gateway can be used for this checkout.

        Check if provided gateway is active and CONFIGURATION_PER_CHANNEL is True.
        If CONFIGURATION_PER_CHANNEL is False then check if gateway has
        defined currency.
        """
        payment_gateway = manager.get_plugin(gateway_id, checkout.channel.slug)

        if not payment_gateway or not payment_gateway.active:
            cls.raise_not_supported_gateway_error(gateway_id)

        if not payment_gateway.CONFIGURATION_PER_CHANNEL:
            if not is_currency_supported(checkout.currency, gateway_id, manager):
                cls.raise_not_supported_gateway_error(gateway_id)

    @classmethod
    def raise_not_supported_gateway_error(cls, gateway_id: str):
        raise ValidationError(
            {
                "gateway": ValidationError(
                    f"The gateway {gateway_id} is not available for this checkout.",
                    code=PaymentErrorCode.NOT_SUPPORTED_GATEWAY.value,
                )
            }
        )

    @classmethod
    def validate_token(cls, manager, gateway: str, input_data: dict, channel_slug: str):
        token = input_data.get("token")
        is_required = manager.token_is_required_as_payment_input(gateway, channel_slug)
        if not token and is_required:
            raise ValidationError(
                {
                    "token": ValidationError(
                        f"Token is required for {gateway}.",
                        code=PaymentErrorCode.REQUIRED.value,
                    ),
                }
            )

    @classmethod
    def validate_return_url(cls, input_data):
        return_url = input_data.get("return_url")
        if not return_url:
            return
        try:
            validate_storefront_url(return_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=PaymentErrorCode.INVALID.value
            )

    @classmethod
    def validate_metadata_keys(cls, metadata_list: List[dict]):
        if metadata_contains_empty_key(metadata_list):
            raise ValidationError(
                {
                    "input": ValidationError(
                        {
                            "metadata": ValidationError(
                                "Metadata key cannot be empty.",
                                code=MetadataErrorCode.REQUIRED.value,
                            )
                        }
                    )
                }
            )

    @staticmethod
    def validate_checkout_email(checkout: "checkout_models.Checkout"):
        if not checkout.email:
            raise ValidationError(
                "Checkout email must be set.",
                code=PaymentErrorCode.CHECKOUT_EMAIL_NOT_SET.value,
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        checkout_id=None,
        id=None,
        input,
        token=None,
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        use_legacy_error_flow_for_checkout = (
            checkout.channel.use_legacy_error_flow_for_checkout
        )

        cls.validate_checkout_email(checkout)

        gateway = input["gateway"]

        manager = get_plugin_manager_promise(info.context).get()
        cls.validate_gateway(manager, gateway, checkout)
        cls.validate_return_url(input)

        lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        if use_legacy_error_flow_for_checkout and unavailable_variant_pks:
            not_available_variants_ids = {
                graphene.Node.to_global_id("ProductVariant", pk)
                for pk in unavailable_variant_pks
            }
            raise ValidationError(
                {
                    "token": ValidationError(
                        "Some of the checkout lines variants are unavailable.",
                        code=PaymentErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value,
                        params={"variants": not_available_variants_ids},
                    )
                }
            )
        if not lines:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Cannot create payment for checkout without lines.",
                        code=PaymentErrorCode.NO_CHECKOUT_LINES.value,
                    )
                }
            )
        checkout_info = fetch_checkout_info(checkout, lines, manager)

        cls.validate_token(
            manager, gateway, input, channel_slug=checkout_info.channel.slug
        )

        address = (
            checkout.shipping_address or checkout.billing_address
        )  # FIXME: check which address we need here
        checkout_total = calculate_checkout_total_with_gift_cards(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=address,
        )
        amount = input.get("amount", checkout_total.gross.amount)
        clean_checkout_shipping(checkout_info, lines, PaymentErrorCode)
        clean_billing_address(checkout_info, PaymentErrorCode)
        cls.clean_payment_amount(info, checkout_total, amount)
        extra_data = {
            "customer_user_agent": info.context.META.get("HTTP_USER_AGENT"),
        }

        metadata = input.get("metadata")

        if metadata is not None:
            cls.validate_metadata_keys(metadata)
            metadata = {data.key: data.value for data in metadata}

        # The payment creation and deactivation of old payments should happened in the
        # transaction to avoid creating multiple active payments.
        with transaction.atomic():
            # The checkout lock is used to prevent processing checkout completion
            # and new payment creation. This kind of case could result in the missing
            # payments, that were created for the checkout that was already converted
            # to an order.
            checkout = (
                checkout_models.Checkout.objects.select_for_update()
                .filter(pk=checkout_info.checkout.pk)
                .first()
            )

            if not checkout:
                raise ValidationError(
                    "Checkout doesn't exist anymore.",
                    code=PaymentErrorCode.NOT_FOUND.value,
                )

            cancel_active_payments(checkout)

            payment = None
            if amount != 0:
                store_payment_method = (
                    input.get("store_payment_method") or StorePaymentMethod.NONE
                )

                payment = create_payment(
                    gateway=gateway,
                    payment_token=input.get("token", ""),
                    total=amount,
                    currency=checkout.currency,
                    email=checkout.get_customer_email(),
                    extra_data=extra_data,
                    # FIXME this is not a customer IP address.
                    # It is a client storefront ip
                    customer_ip_address=get_client_ip(info.context),
                    checkout=checkout,
                    return_url=input.get("return_url"),
                    store_payment_method=store_payment_method,
                    metadata=metadata,
                )

        return CheckoutPaymentCreate(payment=payment, checkout=checkout)
