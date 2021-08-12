import graphene
from django.core.exceptions import ValidationError

from ...channel.models import Channel
from ...checkout.calculations import calculate_checkout_total_with_gift_cards
from ...checkout.checkout_cleaner import clean_billing_address, clean_checkout_shipping
from ...checkout.complete_checkout import complete_checkout_payment
from ...checkout.error_codes import CheckoutErrorCode
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.utils import validate_variants_in_checkout_lines
from ...core import analytics
from ...core.permissions import OrderPermissions
from ...core.transactions import transaction_with_commit_on_errors
from ...core.utils import get_client_ip
from ...core.utils.url import validate_storefront_url
from ...order import models as order_models
from ...payment import PaymentError, gateway, models
from ...payment.error_codes import PaymentErrorCode
from ...payment.utils import create_payment, is_currency_supported
from ..account.i18n import I18nMixin
from ..checkout.mutations import get_checkout_by_token
from ..checkout.types import Checkout
from ..core.mutations import BaseMutation
from ..core.scalars import UUID, PositiveDecimal
from ..core.types import common as common_types
from ..core.types.common import CheckoutError
from ..core.validators import validate_one_of_args_is_in_mutation
from .types import Payment, PaymentInitialized


class PaymentInput(graphene.InputObjectType):
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


class CheckoutPaymentCreate(BaseMutation, I18nMixin):
    checkout = graphene.Field(Checkout, description="Related checkout object.")
    payment = graphene.Field(Payment, description="A newly created payment.")

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                "Checkout ID."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        input = PaymentInput(
            description="Data required to create a new payment.", required=True
        )

    class Meta:
        description = "Create a new payment for given checkout."
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def clean_payment_amount(cls, info, checkout, checkout_total, amount):
        remaining = checkout_total.gross - checkout.get_covered_balance()

        if amount > remaining.amount:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Amount should not exceed checkout's total.",
                        code=PaymentErrorCode.PARTIAL_PAYMENT_TOTAL_EXCEEDED,
                    )
                }
            )

    @classmethod
    def validate_gateway(cls, manager, gateway_id, currency):
        """Validate if given gateway can be used for this checkout.

        Check if provided gateway_id is on the list of available payment gateways.
        Gateway will be rejected if gateway_id is invalid or a gateway doesn't support
        checkout's currency.
        """
        if not is_currency_supported(currency, gateway_id, manager):
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
                {"redirect_url": error}, code=PaymentErrorCode.INVALID
            )

    @classmethod
    def perform_mutation(cls, _root, info, checkout_id=None, token=None, **data):
        # DEPRECATED
        validate_one_of_args_is_in_mutation(
            PaymentErrorCode, "checkout_id", checkout_id, "token", token
        )

        if token:
            checkout = get_checkout_by_token(token)
        # DEPRECATED
        else:
            checkout = cls.get_node_or_error(
                info, checkout_id or token, only_type=Checkout, field="checkout_id"
            )

        data = data["input"]
        gateway = data["gateway"]

        manager = info.context.plugins
        cls.validate_gateway(manager, gateway, checkout.currency)
        cls.validate_return_url(data)

        lines = fetch_checkout_lines(checkout)
        checkout_info = fetch_checkout_info(
            checkout, lines, info.context.discounts, manager
        )

        cls.validate_token(
            manager, gateway, data, channel_slug=checkout_info.channel.slug
        )

        address = (
            checkout.shipping_address or checkout.billing_address
        )  # FIXME: check which address we need here
        checkout_total = calculate_checkout_total_with_gift_cards(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            address=address,
            discounts=info.context.discounts,
        )
        amount = data.get("amount", checkout_total.gross.amount)
        clean_checkout_shipping(checkout_info, lines, PaymentErrorCode)
        clean_billing_address(checkout_info, PaymentErrorCode)
        cls.clean_payment_amount(info, checkout, checkout_total, amount)
        extra_data = {
            "customer_user_agent": info.context.META.get("HTTP_USER_AGENT"),
        }

        payment = create_payment(
            gateway=gateway,
            payment_token=data.get("token", ""),
            total=amount,
            currency=checkout.currency,
            email=checkout.get_customer_email(),
            extra_data=extra_data,
            # FIXME this is not a customer IP address. It is a client storefront ip
            customer_ip_address=get_client_ip(info.context),
            checkout=checkout,
            return_url=data.get("return_url"),
        )
        return CheckoutPaymentCreate(payment=payment, checkout=checkout)


class CheckoutPaymentComplete(BaseMutation, I18nMixin):
    checkout = graphene.Field(Checkout, description="Related checkout object.")
    payment = graphene.Field(Payment, description="Related payment object.")
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
        token = UUID(description="Checkout token.", required=False)
        payment_id = graphene.ID(required=True, description="Payment ID.")
        payment_data = graphene.JSONString(
            required=False,
            description=(
                "Client-side generated data required to finalize the payment."
            ),
        )
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
        description = "Complete a payment for given checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

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
    def perform_mutation(cls, _root, info, store_source, token, payment_id, **data):
        tracking_code = analytics.get_client_id(info.context)
        with transaction_with_commit_on_errors():
            try:
                checkout = get_checkout_by_token(token)
                qs = models.Payment.objects.filter(checkout=checkout)
                payment = cls.get_node_or_error(
                    info, payment_id, field="payment_id", only_type=Payment, qs=qs
                )

            except ValidationError as e:
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
                    return CheckoutPaymentComplete(
                        order=order, confirmation_needed=False, confirmation_data={}
                    )
                raise e

            manager = info.context.plugins
            lines = fetch_checkout_lines(checkout)
            validate_variants_in_checkout_lines(lines)
            checkout_info = fetch_checkout_info(
                checkout, lines, info.context.discounts, manager
            )
            action_required, action_data = complete_checkout_payment(
                payment=payment,
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                payment_data=data.get("payment_data", {}),
                store_source=store_source,
                discounts=info.context.discounts,
                user=info.context.user,
                tracking_code=tracking_code,
                redirect_url=data.get("redirect_url"),
            )
        # If gateway returns information that additional steps are required we need
        # to inform the frontend and pass all required data
        return CheckoutPaymentComplete(
            checkout=checkout,
            payment=payment,
            confirmation_needed=action_required,
            confirmation_data=action_data,
        )


class PaymentCapture(BaseMutation):
    payment = graphene.Field(Payment, description="Updated payment.")

    class Arguments:
        payment_id = graphene.ID(required=True, description="Payment ID.")
        amount = PositiveDecimal(description="Transaction amount.")

    class Meta:
        description = "Captures the authorized payment amount."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(cls, _root, info, payment_id, amount=None):
        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel_slug = (
            payment.order.channel.slug
            if payment.order
            else payment.checkout.channel.slug
        )
        try:
            gateway.capture(
                payment, info.context.plugins, amount=amount, channel_slug=channel_slug
            )
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR)
        return PaymentCapture(payment=payment)


class PaymentRefund(PaymentCapture):
    class Meta:
        description = "Refunds the captured payment amount."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(cls, _root, info, payment_id, amount=None):
        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel_slug = (
            payment.order.channel.slug
            if payment.order
            else payment.checkout.channel.slug
        )
        try:
            gateway.refund(
                payment, info.context.plugins, amount=amount, channel_slug=channel_slug
            )
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR)
        return PaymentRefund(payment=payment)


class PaymentVoid(BaseMutation):
    payment = graphene.Field(Payment, description="Updated payment.")

    class Arguments:
        payment_id = graphene.ID(required=True, description="Payment ID.")

    class Meta:
        description = "Voids the authorized payment."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(cls, _root, info, payment_id):
        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel_slug = (
            payment.order.channel.slug
            if payment.order
            else payment.checkout.channel.slug
        )
        try:
            gateway.void(payment, info.context.plugins, channel_slug=channel_slug)
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR)
        return PaymentVoid(payment=payment)


class PaymentInitialize(BaseMutation):
    initialized_payment = graphene.Field(PaymentInitialized, required=False)

    class Arguments:
        gateway = graphene.String(
            description="A gateway name used to initialize the payment.",
            required=True,
        )
        channel = graphene.String(
            description="Slug of a channel for which the data should be returned.",
        )
        payment_data = graphene.JSONString(
            required=False,
            description=(
                "Client-side generated data required to initialize the payment."
            ),
        )

    class Meta:
        description = "Initializes payment process when it is required by gateway."
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def validate_channel(cls, channel_slug):
        try:
            channel = Channel.objects.get(slug=channel_slug)
        except Channel.DoesNotExist:
            raise ValidationError(
                {
                    "channel": ValidationError(
                        f"Channel with '{channel_slug}' slug does not exist.",
                        code=PaymentErrorCode.NOT_FOUND.value,
                    )
                }
            )
        if not channel.is_active:
            raise ValidationError(
                {
                    "channel": ValidationError(
                        f"Channel with '{channel_slug}' is inactive.",
                        code=PaymentErrorCode.CHANNEL_INACTIVE.value,
                    )
                }
            )
        return channel

    @classmethod
    def perform_mutation(cls, _root, info, gateway, channel, payment_data):
        cls.validate_channel(channel_slug=channel)

        try:
            response = info.context.plugins.initialize_payment(
                gateway, payment_data, channel_slug=channel
            )
        except PaymentError as e:
            raise ValidationError(
                {
                    "payment_data": ValidationError(
                        str(e), code=PaymentErrorCode.INVALID.value
                    )
                }
            )
        return PaymentInitialize(initialized_payment=response)
