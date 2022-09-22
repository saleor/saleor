import uuid
from decimal import Decimal
from typing import List, Optional, Union

import graphene
from django.core.exceptions import ValidationError
from django.db.models import F

from ...channel.models import Channel
from ...checkout import models as checkout_models
from ...checkout.calculations import calculate_checkout_total_with_gift_cards
from ...checkout.checkout_cleaner import clean_billing_address, clean_checkout_shipping
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.utils import cancel_active_payments
from ...core.error_codes import MetadataErrorCode
from ...core.permissions import OrderPermissions, PaymentPermissions
from ...core.utils import get_client_ip
from ...core.utils.url import validate_storefront_url
from ...order import models as order_models
from ...order.events import transaction_event
from ...order.models import Order
from ...payment import PaymentError, StorePaymentMethod, TransactionAction, gateway
from ...payment import models as payment_models
from ...payment.error_codes import (
    PaymentErrorCode,
    TransactionCreateErrorCode,
    TransactionRequestActionErrorCode,
    TransactionUpdateErrorCode,
)
from ...payment.gateway import (
    request_charge_action,
    request_refund_action,
    request_void_action,
)
from ...payment.utils import create_payment, is_currency_supported
from ..account.i18n import I18nMixin
from ..app.dataloaders import load_app
from ..channel.utils import validate_channel
from ..checkout.mutations.utils import get_checkout
from ..checkout.types import Checkout
from ..core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
)
from ..core.fields import JSONString
from ..core.mutations import BaseMutation
from ..core.scalars import UUID, PositiveDecimal
from ..core.types import common as common_types
from ..discount.dataloaders import load_discounts
from ..meta.mutations import MetadataInput
from ..plugins.dataloaders import load_plugin_manager
from ..utils import get_user_or_app_from_context
from .enums import StorePaymentMethodEnum, TransactionActionEnum, TransactionStatusEnum
from .types import Payment, PaymentInitialized, TransactionItem
from .utils import metadata_contains_empty_key


def add_to_order_total_authorized_and_total_charged(
    order_id: uuid.UUID,
    authorized_amount_to_add: Decimal,
    charged_amount_to_add: Decimal,
):
    Order.objects.filter(id=order_id).update(
        total_authorized_amount=F("total_authorized_amount") + authorized_amount_to_add,
        total_charged_amount=F("total_charged_amount") + charged_amount_to_add,
    )


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
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def clean_payment_amount(cls, info, checkout_total, amount):
        if amount != checkout_total.gross.amount:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Partial payments are not allowed, amount should be "
                        "equal checkout's total.",
                        code=PaymentErrorCode.PARTIAL_PAYMENT_NOT_ALLOWED,
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
                {"redirect_url": error}, code=PaymentErrorCode.INVALID
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
    def perform_mutation(
        cls, _root, info, checkout_id=None, token=None, id=None, **data
    ):
        checkout = get_checkout(
            cls,
            info,
            checkout_id=checkout_id,
            token=token,
            id=id,
            error_class=PaymentErrorCode,
        )

        cls.validate_checkout_email(checkout)

        data = data["input"]
        gateway = data["gateway"]

        manager = load_plugin_manager(info.context)
        cls.validate_gateway(manager, gateway, checkout)
        cls.validate_return_url(data)

        lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        if unavailable_variant_pks:
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
        discounts = load_discounts(info.context)
        checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)

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
            discounts=discounts,
        )
        amount = data.get("amount", checkout_total.gross.amount)
        clean_checkout_shipping(checkout_info, lines, PaymentErrorCode)
        clean_billing_address(checkout_info, PaymentErrorCode)
        cls.clean_payment_amount(info, checkout_total, amount)
        extra_data = {
            "customer_user_agent": info.context.META.get("HTTP_USER_AGENT"),
        }

        cancel_active_payments(checkout)

        metadata = data.get("metadata")

        if metadata is not None:
            cls.validate_metadata_keys(metadata)
            metadata = {data.key: data.value for data in metadata}

        payment = None
        if amount != 0:
            store_payment_method = (
                data.get("store_payment_method") or StorePaymentMethod.NONE
            )
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
                store_payment_method=store_payment_method,
                metadata=metadata,
            )

        return CheckoutPaymentCreate(payment=payment, checkout=checkout)


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
        manager = load_plugin_manager(info.context)
        try:
            gateway.capture(
                payment,
                manager,
                amount=amount,
                channel_slug=channel_slug,
            )
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR.value)
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
        manager = load_plugin_manager(info.context)
        try:
            gateway.refund(
                payment,
                manager,
                amount=amount,
                channel_slug=channel_slug,
            )
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR.value)
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
        manager = load_plugin_manager(info.context)
        try:
            gateway.void(payment, manager, channel_slug=channel_slug)
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR.value)
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
        payment_data = JSONString(
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
        manager = load_plugin_manager(info.context)
        try:
            response = manager.initialize_payment(
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


class MoneyInput(graphene.InputObjectType):
    currency = graphene.String(description="Currency code.", required=True)
    amount = PositiveDecimal(description="Amount of money.", required=True)


class CardInput(graphene.InputObjectType):
    code = graphene.String(
        description=(
            "Payment method nonce, a token returned "
            "by the appropriate provider's SDK."
        ),
        required=True,
    )
    cvc = graphene.String(description="Card security code.", required=False)
    money = MoneyInput(
        description="Information about currency and amount.", required=True
    )


class PaymentCheckBalanceInput(graphene.InputObjectType):
    gateway_id = graphene.types.String(
        description="An ID of a payment gateway to check.", required=True
    )
    method = graphene.types.String(description="Payment method name.", required=True)
    channel = graphene.String(
        description="Slug of a channel for which the data should be returned.",
        required=True,
    )
    card = CardInput(description="Information about card.", required=True)


class PaymentCheckBalance(BaseMutation):
    data = JSONString(description="Response from the gateway.")

    class Arguments:
        input = PaymentCheckBalanceInput(
            description="Fields required to check payment balance.", required=True
        )

    class Meta:
        description = "Check payment balance."
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        manager = load_plugin_manager(info.context)
        gateway_id = data["input"]["gateway_id"]
        money = data["input"]["card"].get("money", {})

        cls.validate_gateway(gateway_id, manager)
        cls.validate_currency(money.currency, gateway_id, manager)

        channel = data["input"].pop("channel")
        validate_channel(channel, PaymentErrorCode)

        try:
            data = manager.check_payment_balance(data["input"], channel)
        except PaymentError as e:
            raise ValidationError(
                str(e), code=PaymentErrorCode.BALANCE_CHECK_ERROR.value
            )

        return PaymentCheckBalance(data=data)

    @classmethod
    def validate_gateway(cls, gateway_id, manager):
        gateways_id = [gateway.id for gateway in manager.list_payment_gateways()]

        if gateway_id not in gateways_id:
            raise ValidationError(
                {
                    "gateway_id": ValidationError(
                        f"The gateway_id {gateway_id} is not available.",
                        code=PaymentErrorCode.NOT_SUPPORTED_GATEWAY.value,
                    )
                }
            )

    @classmethod
    def validate_currency(cls, currency, gateway_id, manager):
        if not is_currency_supported(currency, gateway_id, manager):
            raise ValidationError(
                {
                    "currency": ValidationError(
                        f"The currency {currency} is not available for {gateway_id}.",
                        code=PaymentErrorCode.NOT_SUPPORTED_GATEWAY.value,
                    )
                }
            )


class TransactionUpdateInput(graphene.InputObjectType):
    status = graphene.String(
        description="Status of the transaction.",
    )
    type = graphene.String(
        description="Payment type used for this transaction.",
    )
    reference = graphene.String(description="Reference of the transaction.")
    available_actions = graphene.List(
        graphene.NonNull(TransactionActionEnum),
        description="List of all possible actions for the transaction",
    )
    amount_authorized = MoneyInput(description="Amount authorized by this transaction.")
    amount_charged = MoneyInput(description="Amount charged by this transaction.")
    amount_refunded = MoneyInput(description="Amount refunded by this transaction.")
    amount_voided = MoneyInput(description="Amount voided by this transaction.")

    metadata = graphene.List(
        graphene.NonNull(MetadataInput),
        description="Payment public metadata.",
        required=False,
    )
    private_metadata = graphene.List(
        graphene.NonNull(MetadataInput),
        description="Payment private metadata.",
        required=False,
    )


class TransactionCreateInput(TransactionUpdateInput):
    status = graphene.String(description="Status of the transaction.", required=True)
    type = graphene.String(
        description="Payment type used for this transaction.", required=True
    )


class TransactionEventInput(graphene.InputObjectType):
    status = graphene.Field(
        TransactionStatusEnum,
        required=True,
        description="Current status of the payment transaction.",
    )
    reference = graphene.String(description="Reference of the transaction.")
    name = graphene.String(description="Name of the transaction.")


class TransactionCreate(BaseMutation):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description="The ID of the checkout or order.",
            required=True,
        )
        transaction = TransactionCreateInput(
            required=True,
            description="Input data required to create a new transaction object.",
        )
        transaction_event = TransactionEventInput(
            description="Data that defines a transaction event."
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Create transaction for checkout or order. Requires the "
            "following permissions: AUTHENTICATED_APP and HANDLE_PAYMENTS."
            + ADDED_IN_34
            + PREVIEW_FEATURE
        )
        error_type_class = common_types.TransactionCreateError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)

    @classmethod
    def check_permissions(cls, context, permissions=None):
        """Determine whether app has rights to perform this mutation."""
        permissions = permissions or cls._meta.permissions
        if app := getattr(context, "app", None):
            return app.has_perms(permissions)
        return False

    @classmethod
    def validate_metadata_keys(cls, metadata_list: List[dict], field_name, error_code):
        if metadata_contains_empty_key(metadata_list):
            raise ValidationError(
                {
                    "transaction": ValidationError(
                        {
                            field_name: ValidationError(
                                "Metadata key cannot be empty.",
                                code=error_code,
                            )
                        }
                    )
                }
            )

    @classmethod
    def cleanup_money_data(cls, cleaned_data: dict):
        if amount_authorized := cleaned_data.pop("amount_authorized", None):
            cleaned_data["authorized_value"] = amount_authorized["amount"]
        if amount_charged := cleaned_data.pop("amount_charged", None):
            cleaned_data["charged_value"] = amount_charged["amount"]
        if amount_refunded := cleaned_data.pop("amount_refunded", None):
            cleaned_data["refunded_value"] = amount_refunded["amount"]
        if amount_voided := cleaned_data.pop("amount_voided", None):
            cleaned_data["voided_value"] = amount_voided["amount"]

    @classmethod
    def cleanup_metadata_data(cls, cleaned_data: dict):
        if metadata := cleaned_data.pop("metadata", None):
            cleaned_data["metadata"] = {data.key: data.value for data in metadata}
        if private_metadata := cleaned_data.pop("private_metadata", None):
            cleaned_data["private_metadata"] = {
                data.key: data.value for data in private_metadata
            }

    @classmethod
    def validate_instance(
        cls, instance: Union[checkout_models.Checkout, order_models.Order], instance_id
    ):
        """Validate if provided instance is an order or checkout type."""
        if not isinstance(instance, (checkout_models.Checkout, order_models.Order)):
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"Couldn't resolve to Checkout or Order: {instance_id}",
                        code=TransactionCreateErrorCode.NOT_FOUND.value,
                    )
                }
            )

    @classmethod
    def validate_money_input(
        cls, transaction_data: dict, currency: str, error_code: str
    ):
        if not transaction_data:
            return
        money_input_fields = [
            "amount_authorized",
            "amount_charged",
            "amount_refunded",
            "amount_voided",
        ]
        errors = {}
        for money_field_name in money_input_fields:
            field = transaction_data.get(money_field_name)
            if not field:
                continue
            if field["currency"] != currency:
                errors[money_field_name] = ValidationError(
                    f"Currency needs to be the same as for order: {currency}",
                    code=error_code,
                )
        if errors:
            raise ValidationError(errors)

    @classmethod
    def validate_input(
        cls, instance: Union[checkout_models.Checkout, order_models.Order], input_data
    ):
        cls.validate_instance(instance, input_data.get("id"))
        currency = instance.currency
        transaction_data = input_data["transaction"]

        cls.validate_money_input(
            input_data["transaction"],
            currency,
            TransactionCreateErrorCode.INCORRECT_CURRENCY.value,
        )
        cls.validate_metadata_keys(
            transaction_data.get("metadata", []),
            field_name="metadata",
            error_code=TransactionCreateErrorCode.METADATA_KEY_REQUIRED.value,
        )
        cls.validate_metadata_keys(
            transaction_data.get("private_metadata", []),
            field_name="privateMetadata",
            error_code=TransactionCreateErrorCode.METADATA_KEY_REQUIRED.value,
        )

    @classmethod
    def create_transaction(
        cls, transaction_input: dict
    ) -> payment_models.TransactionItem:
        cls.cleanup_money_data(transaction_input)
        cls.cleanup_metadata_data(transaction_input)
        return payment_models.TransactionItem.objects.create(
            **transaction_input,
        )

    @classmethod
    def create_transaction_event(
        cls, transaction_event_input: dict, transaction: payment_models.TransactionItem
    ) -> payment_models.TransactionEvent:
        return transaction.events.create(
            status=transaction_event_input["status"],
            reference=transaction_event_input.get("reference", ""),
            name=transaction_event_input.get("name", ""),
            transaction=transaction,
        )

    @classmethod
    def add_amounts_to_order(cls, order_id: uuid.UUID, transaction_data: dict):
        authorized_amount = transaction_data.get("authorized_value", 0)
        charged_amount = transaction_data.get("charged_value", 0)
        if not authorized_amount and not charged_amount:
            return
        add_to_order_total_authorized_and_total_charged(
            order_id=order_id,
            authorized_amount_to_add=authorized_amount,
            charged_amount_to_add=charged_amount,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance_id = data.get("id")
        order_or_checkout_instance = cls.get_node_or_error(info, instance_id)

        cls.validate_input(order_or_checkout_instance, data)
        transaction_data = {**data["transaction"]}
        transaction_data["currency"] = order_or_checkout_instance.currency
        transaction_event_data = data.get("transaction_event")
        if isinstance(order_or_checkout_instance, checkout_models.Checkout):
            transaction_data["checkout_id"] = order_or_checkout_instance.pk
        else:
            transaction_data["order_id"] = order_or_checkout_instance.pk
            if transaction_event_data:
                app = load_app(info.context)
                transaction_event(
                    order=order_or_checkout_instance,
                    user=info.context.user,
                    app=app,
                    reference=transaction_event_data.get("reference", ""),
                    status=transaction_event_data["status"],
                    name=transaction_event_data.get("name", ""),
                )
        transaction = cls.create_transaction(transaction_data)
        if order_id := transaction_data.get("order_id"):
            cls.add_amounts_to_order(order_id, transaction_data)

        if transaction_event_data:
            cls.create_transaction_event(transaction_event_data, transaction)
        return TransactionCreate(transaction=transaction)


class TransactionUpdate(TransactionCreate):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description="The ID of the transaction.",
            required=True,
        )
        transaction = TransactionUpdateInput(
            description="Input data required to create a new transaction object.",
        )
        transaction_event = TransactionEventInput(
            description="Data that defines a transaction transaction."
        )

    class Meta:
        auto_permission_message = False
        description = (
            "Create transaction for checkout or order. Requires the "
            "following permissions: AUTHENTICATED_APP and HANDLE_PAYMENTS."
            + ADDED_IN_34
            + PREVIEW_FEATURE
        )
        error_type_class = common_types.TransactionUpdateError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)
        object_type = TransactionItem

    @classmethod
    def validate_transaction_input(
        cls, instance: payment_models.TransactionItem, transaction_data
    ):
        currency = instance.currency
        cls.validate_money_input(
            transaction_data,
            currency,
            TransactionUpdateErrorCode.INCORRECT_CURRENCY.value,
        )
        cls.validate_metadata_keys(
            transaction_data.get("metadata", []),
            field_name="metadata",
            error_code=TransactionUpdateErrorCode.METADATA_KEY_REQUIRED.value,
        )
        cls.validate_metadata_keys(
            transaction_data.get("private_metadata", []),
            field_name="privateMetadata",
            error_code=TransactionUpdateErrorCode.METADATA_KEY_REQUIRED.value,
        )

    @classmethod
    def update_amounts_for_order(
        cls,
        transaction: payment_models.TransactionItem,
        order_id: uuid.UUID,
        transaction_data: dict,
    ):
        current_authorized_amount = transaction.authorized_value
        updated_authorized_amount = transaction_data.get(
            "authorized_value", current_authorized_amount
        )
        authorized_amount_to_add = updated_authorized_amount - current_authorized_amount

        current_charged_amount = transaction.charged_value
        updated_charged_amount = transaction_data.get(
            "charged_value", current_charged_amount
        )
        charged_amount_to_add = updated_charged_amount - current_charged_amount

        if not authorized_amount_to_add and not charged_amount_to_add:
            return
        add_to_order_total_authorized_and_total_charged(
            order_id=order_id,
            authorized_amount_to_add=authorized_amount_to_add,
            charged_amount_to_add=charged_amount_to_add,
        )

    @classmethod
    def perform_mutation(cls, root, info, **data):
        instance_id = data.get("id")
        instance = cls.get_node_or_error(info, instance_id, only_type=TransactionItem)
        transaction_data = data.get("transaction")
        if transaction_data:
            cls.validate_transaction_input(instance, transaction_data)
            cls.cleanup_money_data(transaction_data)
            cls.cleanup_metadata_data(transaction_data)
            if instance.order_id:
                cls.update_amounts_for_order(
                    instance, instance.order_id, transaction_data
                )
            instance = cls.construct_instance(instance, transaction_data)
            instance.save()

        if transaction_event_data := data.get("transaction_event"):
            cls.create_transaction_event(transaction_event_data, instance)
            if instance.order_id:
                app = load_app(info.context)
                transaction_event(
                    order=instance.order,
                    user=info.context.user,
                    app=app,
                    reference=transaction_event_data.get("reference", ""),
                    status=transaction_event_data["status"],
                    name=transaction_event_data.get("name", ""),
                )
        return TransactionUpdate(transaction=instance)


class TransactionRequestAction(BaseMutation):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description="The ID of the transaction.",
            required=True,
        )
        action_type = graphene.Argument(
            TransactionActionEnum,
            required=True,
            description="Determines the action type.",
        )
        amount = PositiveDecimal(
            description=(
                "Transaction request amount. If empty for refund or capture, maximal "
                "possible amount will be used."
            )
        )

    class Meta:
        description = (
            "Request an action for payment transaction." + ADDED_IN_34 + PREVIEW_FEATURE
        )
        error_type_class = common_types.TransactionRequestActionError
        permissions = (
            PaymentPermissions.HANDLE_PAYMENTS,
            OrderPermissions.MANAGE_ORDERS,
        )

    @classmethod
    def check_permissions(cls, context, permissions=None):
        required_permissions = permissions or cls._meta.permissions
        requestor = get_user_or_app_from_context(context)
        for required_permission in required_permissions:
            # We want to allow to call this mutation for requestor with one of following
            # permission: manage_orders, handle_payments
            if requestor.has_perm(required_permission):
                return True
        return False

    @classmethod
    def handle_transaction_action(
        cls, action, action_kwargs, action_value: Optional[Decimal]
    ):
        if action == TransactionAction.VOID:
            request_void_action(**action_kwargs)
        elif action == TransactionAction.CHARGE:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.authorized_value
            action_value = min(action_value, transaction.authorized_value)
            request_charge_action(**action_kwargs, charge_value=action_value)
        elif action == TransactionAction.REFUND:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.charged_value
            action_value = min(action_value, transaction.charged_value)
            request_refund_action(**action_kwargs, refund_value=action_value)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        id = data["id"]
        action_type = data["action_type"]
        action_value = data.get("amount")
        transaction = cls.get_node_or_error(info, id, only_type=TransactionItem)
        channel_slug = (
            transaction.order.channel.slug
            if transaction.order_id
            else transaction.checkout.channel.slug
        )
        app = load_app(info.context)
        manager = load_plugin_manager(info.context)
        action_kwargs = {
            "channel_slug": channel_slug,
            "user": info.context.user,
            "app": app,
            "transaction": transaction,
            "manager": manager,
        }

        try:
            cls.handle_transaction_action(action_type, action_kwargs, action_value)
        except PaymentError as e:
            error_enum = TransactionRequestActionErrorCode
            code = error_enum.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.value
            raise ValidationError(str(e), code=code)
        return TransactionRequestAction(transaction=transaction)
