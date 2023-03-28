from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List, Optional, Union, cast

import graphene
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Model
from django.utils import timezone

from ...channel.models import Channel
from ...checkout import models as checkout_models
from ...checkout.calculations import calculate_checkout_total_with_gift_cards
from ...checkout.checkout_cleaner import clean_billing_address, clean_checkout_shipping
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.utils import cancel_active_payments
from ...core.error_codes import MetadataErrorCode
from ...core.exceptions import PermissionDenied
from ...core.tracing import traced_atomic_transaction
from ...core.utils import get_client_ip
from ...core.utils.url import validate_storefront_url
from ...order import models as order_models
from ...order.events import transaction_event as order_transaction_event
from ...order.search import update_order_search_vector
from ...order.utils import updates_amounts_for_order
from ...payment import (
    PaymentError,
    StorePaymentMethod,
    TransactionAction,
    TransactionEventType,
    gateway,
)
from ...payment import models as payment_models
from ...payment.error_codes import (
    PaymentErrorCode,
    TransactionCreateErrorCode,
    TransactionEventReportErrorCode,
    TransactionRequestActionErrorCode,
    TransactionUpdateErrorCode,
)
from ...payment.gateway import (
    request_cancelation_action,
    request_charge_action,
    request_refund_action,
)
from ...payment.transaction_item_calculations import (
    calculate_transaction_amount_based_on_events,
    recalculate_transaction_amounts,
)
from ...payment.utils import (
    authorization_success_already_exists,
    create_failed_transaction_event,
    create_manual_adjustment_events,
    create_payment,
    get_already_existing_event,
    is_currency_supported,
)
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import OrderPermissions, PaymentPermissions
from ..account.i18n import I18nMixin
from ..app.dataloaders import get_app_promise
from ..channel.utils import validate_channel
from ..checkout.mutations.utils import get_checkout
from ..checkout.types import Checkout
from ..core import ResolveInfo
from ..core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    ADDED_IN_313,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
    PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT,
)
from ..core.doc_category import DOC_CATEGORY_CHECKOUT, DOC_CATEGORY_PAYMENTS
from ..core.fields import JSONString
from ..core.mutations import BaseMutation, ModelMutation
from ..core.scalars import UUID, PositiveDecimal
from ..core.types import BaseInputObjectType
from ..core.types import common as common_types
from ..discount.dataloaders import load_discounts
from ..meta.mutations import MetadataInput
from ..plugins.dataloaders import get_plugin_manager_promise
from ..utils import get_user_or_app_from_context
from .enums import (
    StorePaymentMethodEnum,
    TransactionActionEnum,
    TransactionEventStatusEnum,
    TransactionEventTypeEnum,
)
from .types import Payment, PaymentInitialized, TransactionEvent, TransactionItem
from .utils import check_if_requestor_has_access, metadata_contains_empty_key

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App
    from ...order.models import Order


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
        token=None
    ):
        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        cls.validate_checkout_email(checkout)

        gateway = input["gateway"]

        manager = get_plugin_manager_promise(info.context).get()
        cls.validate_gateway(manager, gateway, checkout)
        cls.validate_return_url(input)

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
            discounts=discounts,
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


class PaymentCapture(BaseMutation):
    payment = graphene.Field(Payment, description="Updated payment.")

    class Arguments:
        payment_id = graphene.ID(required=True, description="Payment ID.")
        amount = PositiveDecimal(description="Transaction amount.")

    class Meta:
        description = "Captures the authorized payment amount."
        doc_category = DOC_CATEGORY_PAYMENTS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, amount=None, payment_id
    ):
        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel_slug = (
            payment.order.channel.slug
            if payment.order
            else payment.checkout.channel.slug
        )
        manager = get_plugin_manager_promise(info.context).get()
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
        doc_category = DOC_CATEGORY_PAYMENTS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, amount=None, payment_id
    ):
        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel_slug = (
            payment.order.channel.slug
            if payment.order
            else payment.checkout.channel.slug
        )
        manager = get_plugin_manager_promise(info.context).get()
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
        doc_category = DOC_CATEGORY_PAYMENTS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, payment_id
    ):
        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel_slug = (
            payment.order.channel.slug
            if payment.order
            else payment.checkout.channel.slug
        )
        manager = get_plugin_manager_promise(info.context).get()
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
        doc_category = DOC_CATEGORY_PAYMENTS
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
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, channel, gateway, payment_data
    ):
        cls.validate_channel(channel_slug=channel)
        manager = get_plugin_manager_promise(info.context).get()
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


class PaymentCheckBalanceInput(BaseInputObjectType):
    gateway_id = graphene.types.String(
        description="An ID of a payment gateway to check.", required=True
    )
    method = graphene.types.String(description="Payment method name.", required=True)
    channel = graphene.String(
        description="Slug of a channel for which the data should be returned.",
        required=True,
    )
    card = CardInput(description="Information about card.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentCheckBalance(BaseMutation):
    data = JSONString(description="Response from the gateway.")

    class Arguments:
        input = PaymentCheckBalanceInput(
            description="Fields required to check payment balance.", required=True
        )

    class Meta:
        description = "Check payment balance."
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        manager = get_plugin_manager_promise(info.context).get()
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


class TransactionUpdateInput(BaseInputObjectType):
    status = graphene.String(
        description=(
            "Status of the transaction."
            + PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT
            + " The `status` is not needed. The amounts can be used to define "
            "the current status of transactions."
        ),
    )
    type = graphene.String(
        description="Payment type used for this transaction."
        + PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT
        + " Use `name` and `message` instead.",
    )
    name = graphene.String(
        description="Payment name of the transaction." + ADDED_IN_313
    )
    message = graphene.String(
        description="The message of the transaction." + ADDED_IN_313
    )

    reference = graphene.String(
        description=(
            "Reference of the transaction. "
            + PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT
            + " Use `pspReference` instead."
        )
    )
    psp_reference = graphene.String(
        description=("PSP Reference of the transaction. " + ADDED_IN_313)
    )
    available_actions = graphene.List(
        graphene.NonNull(TransactionActionEnum),
        description="List of all possible actions for the transaction",
    )
    amount_authorized = MoneyInput(description="Amount authorized by this transaction.")
    amount_charged = MoneyInput(description="Amount charged by this transaction.")
    amount_refunded = MoneyInput(description="Amount refunded by this transaction.")
    amount_voided = MoneyInput(
        description="Amount voided by this transaction."
        + PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT
        + " Use `amountCanceled` instead."
    )
    amount_canceled = MoneyInput(
        description="Amount canceled by this transaction." + ADDED_IN_313
    )

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
    external_url = graphene.String(
        description=(
            "The url that will allow to redirect user to "
            "payment provider page with transaction event details." + ADDED_IN_313
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionCreateInput(TransactionUpdateInput):
    ...

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionEventInput(BaseInputObjectType):
    status = graphene.Field(
        TransactionEventStatusEnum,
        required=False,
        description="Current status of the payment transaction."
        + PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT
        + " Status will be calculated by Saleor.",
    )
    reference = graphene.String(
        description=(
            "Reference of the transaction. "
            + PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT
            + " Use `pspReference` instead."
        )
    )

    psp_reference = graphene.String(
        description=("PSP Reference related to this action." + ADDED_IN_313)
    )
    name = graphene.String(
        description="Name of the transaction."
        + PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT
        + " Use `message` instead. `name` field will be added to `message`."
    )
    message = graphene.String(
        description="The message related to the event." + ADDED_IN_313
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


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
        description = (
            "Create transaction for checkout or order." + ADDED_IN_34 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionCreateError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)

    @classmethod
    def validate_external_url(cls, external_url: Optional[str], error_code: str):
        if external_url is None:
            return
        validator = URLValidator()
        try:
            validator(external_url)
        except ValidationError:
            raise ValidationError(
                {
                    "transaction": ValidationError(
                        "Invalid format of `externalUrl`.", code=error_code
                    )
                }
            )

    @classmethod
    def validate_metadata_keys(  # type: ignore[override]
        cls, metadata_list: List[dict], field_name, error_code
    ):
        if metadata_contains_empty_key(metadata_list):
            raise ValidationError(
                {
                    "transaction": ValidationError(
                        f"{field_name} key cannot be empty.",
                        code=error_code,
                    )
                }
            )

    @classmethod
    def get_money_data_from_input(cls, cleaned_data: dict) -> Dict[str, Decimal]:
        money_data = {}
        if amount_authorized := cleaned_data.pop("amount_authorized", None):
            money_data["authorized_value"] = amount_authorized["amount"]
        if amount_charged := cleaned_data.pop("amount_charged", None):
            money_data["charged_value"] = amount_charged["amount"]
        if amount_refunded := cleaned_data.pop("amount_refunded", None):
            money_data["refunded_value"] = amount_refunded["amount"]

        if amount_canceled := cleaned_data.pop("amount_canceled", None):
            money_data["canceled_value"] = amount_canceled["amount"]
        elif amount_voided := cleaned_data.pop("amount_voided", None):
            money_data["canceled_value"] = amount_voided["amount"]
        return money_data

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
        cls, instance: Model, instance_id
    ) -> Union[checkout_models.Checkout, order_models.Order]:
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
        return instance

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
            "amount_canceled",
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
        cls, instance: Model, *, id, transaction
    ) -> Union[checkout_models.Checkout, order_models.Order]:
        instance = cls.validate_instance(instance, id)
        currency = instance.currency

        cls.validate_money_input(
            transaction,
            currency,
            TransactionCreateErrorCode.INCORRECT_CURRENCY.value,
        )
        cls.validate_metadata_keys(
            transaction.get("metadata", []),
            field_name="metadata",
            error_code=TransactionCreateErrorCode.METADATA_KEY_REQUIRED.value,
        )
        cls.validate_metadata_keys(
            transaction.get("private_metadata", []),
            field_name="privateMetadata",
            error_code=TransactionCreateErrorCode.METADATA_KEY_REQUIRED.value,
        )
        cls.validate_external_url(
            transaction.get("external_url"),
            error_code=TransactionCreateErrorCode.INVALID.value,
        )
        return instance

    @classmethod
    def create_transaction(
        cls, transaction_input: dict, user, app
    ) -> payment_models.TransactionItem:
        cls.cleanup_metadata_data(transaction_input)

        transaction_type = transaction_input.pop("type", None)
        transaction_input["name"] = transaction_input.get("name", transaction_type)
        reference = transaction_input.pop("reference", None)
        transaction_input["psp_reference"] = transaction_input.get(
            "psp_reference", reference
        )
        app_identifier = None
        if app and app.identifier:
            app_identifier = app.identifier
        return payment_models.TransactionItem.objects.create(
            **transaction_input,
            user=user if user and user.is_authenticated else None,
            app_identifier=app_identifier,
            app=app,
        )

    @classmethod
    def create_transaction_event(
        cls,
        transaction_event_input: dict,
        transaction: payment_models.TransactionItem,
        user,
        app,
    ) -> payment_models.TransactionEvent:
        reference = transaction_event_input.pop("reference", None)
        psp_reference = transaction_event_input.get("psp_reference", reference)
        app_identifier = None
        if app and app.identifier:
            app_identifier = app.identifier
        return transaction.events.create(
            status=transaction_event_input.get("status"),
            psp_reference=psp_reference,
            message=cls.create_event_message(transaction_event_input),
            transaction=transaction,
            user=user if user and user.is_authenticated else None,
            app_identifier=app_identifier,
            app=app,
            type=TransactionEventType.INFO,
            currency=transaction.currency,
        )

    @classmethod
    def create_event_message(cls, transaction_event: dict) -> str:
        message = transaction_event.get("message")
        name = transaction_event.get("name")
        if message and name:
            return message + " " + name
        elif message:
            return message
        elif name:
            return name
        return ""

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id: str,
        transaction: Dict,
        transaction_event=None
    ):
        order_or_checkout_instance = cls.get_node_or_error(info, id)

        order_or_checkout_instance = cls.validate_input(
            order_or_checkout_instance, id=id, transaction=transaction
        )
        transaction_data = {**transaction}
        transaction_data["currency"] = order_or_checkout_instance.currency
        app = get_app_promise(info.context).get()
        user = info.context.user

        if isinstance(order_or_checkout_instance, checkout_models.Checkout):
            transaction_data["checkout_id"] = order_or_checkout_instance.pk
        else:
            transaction_data["order_id"] = order_or_checkout_instance.pk
            if transaction_event:
                reference = transaction_event.get("reference", None)
                psp_reference = transaction_event.get("psp_reference", reference)
                order_transaction_event(
                    order=order_or_checkout_instance,
                    user=user,
                    app=app,
                    reference=psp_reference,
                    status=transaction_event.get("status"),
                    message=cls.create_event_message(transaction_event),
                )
        money_data = cls.get_money_data_from_input(transaction_data)
        new_transaction = cls.create_transaction(transaction_data, user=user, app=app)
        if money_data:
            create_manual_adjustment_events(
                transaction=new_transaction, money_data=money_data, user=user, app=app
            )
            recalculate_transaction_amounts(new_transaction)
        if transaction_data.get("order_id") and money_data:
            order = cast(order_models.Order, new_transaction.order)
            update_order_search_vector(order, save=False)
            updates_amounts_for_order(order, save=False)
            order.save(
                update_fields=[
                    "total_charged_amount",
                    "charge_status",
                    "updated_at",
                    "total_authorized_amount",
                    "authorize_status",
                    "search_vector",
                ]
            )

        if transaction_event:
            cls.create_transaction_event(transaction_event, new_transaction, user, app)
        return TransactionCreate(transaction=new_transaction)


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
            "Create transaction for checkout or order."
            + ADDED_IN_34
            + PREVIEW_FEATURE
            + "\n\nRequires the following permissions: "
            + f"{AuthorizationFilters.OWNER.name} "
            + f"and {PaymentPermissions.HANDLE_PAYMENTS.name}."
        )
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionUpdateError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)
        object_type = TransactionItem

    @classmethod
    def check_can_update(
        cls,
        transaction: payment_models.TransactionItem,
        user: Optional["User"],
        app: Optional["App"],
    ):
        if not check_if_requestor_has_access(
            transaction=transaction, user=user, app=app
        ):
            raise PermissionDenied(
                permissions=[
                    AuthorizationFilters.OWNER,
                    PaymentPermissions.HANDLE_PAYMENTS,
                ]
            )

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
        cls.validate_external_url(
            transaction_data.get("external_url"),
            error_code=TransactionCreateErrorCode.INVALID.value,
        )

    @classmethod
    def update_transaction(
        cls,
        instance: payment_models.TransactionItem,
        transaction_data: dict,
        user: Optional["User"],
        app: Optional["App"],
    ):
        money_data = cls.get_money_data_from_input(transaction_data)
        psp_reference = transaction_data.get(
            "psp_reference", transaction_data.pop("reference", None)
        )
        if psp_reference and instance.psp_reference != psp_reference:
            if payment_models.TransactionItem.objects.filter(
                psp_reference=psp_reference
            ).exists():
                raise ValidationError(
                    {
                        "transaction": ValidationError(
                            "Transaction with provided `pspReference` already exists.",
                            code=TransactionUpdateErrorCode.UNIQUE.value,
                        )
                    }
                )
        transaction_data["name"] = transaction_data.get(
            "name", transaction_data.pop("type", None)
        )
        transaction_data["psp_reference"] = psp_reference
        instance = cls.construct_instance(instance, transaction_data)
        instance.save()
        if money_data:
            calculate_transaction_amount_based_on_events(transaction=instance)
            create_manual_adjustment_events(
                transaction=instance, money_data=money_data, user=user, app=app
            )
            recalculate_transaction_amounts(instance)
        if instance.order_id:
            order = cast(order_models.Order, instance.order)
            cls.update_order(order, money_data, psp_reference)

    @classmethod
    def update_order(
        cls, order: "Order", money_data: dict, psp_reference: Optional[str]
    ) -> None:
        update_fields = []
        if money_data:
            updates_amounts_for_order(order)
            update_fields.extend(
                [
                    "total_charged_amount",
                    "charge_status",
                    "total_authorized_amount",
                    "authorize_status",
                ]
            )
        if psp_reference:
            update_order_search_vector(order, save=False)
            update_fields.append(
                "search_vector",
            )
        if update_fields:
            update_fields.append("updated_at")
            order.save(update_fields=update_fields)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id: str,
        transaction=None,
        transaction_event=None
    ):
        app = get_app_promise(info.context).get()
        user = info.context.user
        instance = cls.get_node_or_error(info, id, only_type=TransactionItem)

        cls.check_can_update(
            transaction=instance,
            user=user if user and user.is_authenticated else None,
            app=app,
        )

        if transaction:
            cls.validate_transaction_input(instance, transaction)
            cls.cleanup_metadata_data(transaction)
            cls.update_transaction(instance, transaction, user, app)

        if transaction_event:
            cls.create_transaction_event(transaction_event, instance, user, app)
            if instance.order:
                reference = transaction_event.pop("reference", None)
                psp_reference = transaction_event.get("psp_reference", reference)
                order_transaction_event(
                    order=instance.order,
                    user=user,
                    app=app,
                    reference=psp_reference or "",
                    status=transaction_event["status"],
                    message=cls.create_event_message(transaction_event),
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
        doc_category = DOC_CATEGORY_PAYMENTS
        error_type_class = common_types.TransactionRequestActionError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)

    @classmethod
    def check_permissions(cls, context, permissions=None, **data):
        required_permissions = permissions or cls._meta.permissions
        requestor = get_user_or_app_from_context(context)
        for required_permission in required_permissions:
            # We want to allow to call this mutation for requestor with one of following
            # permission: manage_orders, handle_payments
            if requestor and requestor.has_perm(required_permission):
                return True
        return False

    @classmethod
    def handle_transaction_action(
        cls, action, action_kwargs, action_value: Optional[Decimal]
    ):
        if action == TransactionAction.VOID or action == TransactionAction.CANCEL:
            transaction = action_kwargs["transaction"]
            request_event = cls.create_transaction_event_requested(
                transaction, 0, action
            )
            request_cancelation_action(
                **action_kwargs,
                cancel_value=action_value,
                request_event=request_event,
                action=action,
            )
        elif action == TransactionAction.CHARGE:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.authorized_value
            action_value = min(action_value, transaction.authorized_value)
            request_event = cls.create_transaction_event_requested(
                transaction, action_value, TransactionAction.CHARGE
            )
            request_charge_action(
                **action_kwargs, charge_value=action_value, request_event=request_event
            )
        elif action == TransactionAction.REFUND:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.charged_value
            action_value = min(action_value, transaction.charged_value)
            request_event = cls.create_transaction_event_requested(
                transaction, action_value, TransactionAction.REFUND
            )
            request_refund_action(
                **action_kwargs, refund_value=action_value, request_event=request_event
            )

    @classmethod
    def create_transaction_event_requested(cls, transaction, action_value, action):
        if action in (TransactionAction.CANCEL, TransactionAction.VOID):
            type = TransactionEventType.CANCEL_REQUEST
        elif action == TransactionAction.CHARGE:
            type = TransactionEventType.CHARGE_REQUEST
        elif action == TransactionAction.REFUND:
            type = TransactionEventType.REFUND_REQUEST
        else:
            raise ValidationError(
                {
                    "actionType": ValidationError(
                        "Incorrect action.",
                        code=TransactionRequestActionErrorCode.INVALID.value,
                    )
                }
            )
        return transaction.events.create(
            amount_value=action_value,
            currency=transaction.currency,
            type=type,
        )

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        id = data["id"]
        action_type = data["action_type"]
        action_value = data.get("amount")
        transaction = cls.get_node_or_error(info, id, only_type=TransactionItem)
        channel_slug = (
            transaction.order.channel.slug
            if transaction.order_id
            else transaction.checkout.channel.slug
        )
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
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


class TransactionEventReport(ModelMutation):
    already_processed = graphene.Boolean(
        description="Defines if the reported event hasn't been processed earlier."
    )
    transaction = graphene.Field(
        TransactionItem, description="The transaction related to the reported event."
    )
    transaction_event = graphene.Field(
        TransactionEvent,
        description=(
            "The event assigned to this report. if `alreadyProcessed` is set to `true`,"
            " the previously processed event will be returned."
        ),
    )

    class Arguments:
        id = graphene.ID(
            description="The ID of the transaction.",
            required=True,
        )
        psp_reference = graphene.String(
            description="PSP Reference of the event to report.", required=True
        )
        type = graphene.Argument(
            TransactionEventTypeEnum,
            required=True,
            description="Current status of the event to report.",
        )
        amount = PositiveDecimal(
            description="The amount of the event to report.", required=True
        )
        time = graphene.DateTime(
            description=(
                "The time of the event to report. If not provide, "
                "the current time will be used."
            )
        )
        external_url = graphene.String(
            description=(
                "The url that will allow to redirect user to "
                "payment provider page with event details."
            )
        )
        message = graphene.String(description="The message related to the event.")
        available_actions = graphene.List(
            graphene.NonNull(TransactionActionEnum),
            description="List of all possible actions for the transaction",
        )

    class Meta:
        description = (
            "Report the event for the transaction."
            + ADDED_IN_313
            + PREVIEW_FEATURE
            + "\n\nRequires the following permissions: "
            + f"{AuthorizationFilters.OWNER.name} "
            + f"and {PaymentPermissions.HANDLE_PAYMENTS.name}."
        )
        error_type_class = common_types.TransactionEventReportError
        permissions = (PaymentPermissions.HANDLE_PAYMENTS,)
        doc_category = DOC_CATEGORY_PAYMENTS
        model = payment_models.TransactionEvent
        object_type = TransactionEvent
        auto_permission_message = False

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        root,
        info: ResolveInfo,
        /,
        *,
        id,
        psp_reference,
        type,
        amount,
        time=None,
        external_url=None,
        message=None,
        available_actions=None
    ):
        user = info.context.user
        app = get_app_promise(info.context).get()
        transaction = cls.get_node_or_error(info, id, only_type="TransactionItem")
        transaction = cast(payment_models.TransactionItem, transaction)

        if not check_if_requestor_has_access(
            transaction=transaction, user=user, app=app
        ):
            raise PermissionDenied(
                permissions=[
                    AuthorizationFilters.OWNER,
                    PaymentPermissions.HANDLE_PAYMENTS,
                ]
            )

        app_identifier = None
        if app and app.identifier:
            app_identifier = app.identifier

        transaction_event_data = {
            "psp_reference": psp_reference,
            "type": type,
            "amount_value": amount,
            "currency": transaction.currency,
            "created_at": time or timezone.now(),
            "external_url": external_url or "",
            "message": message or "",
            "transaction": transaction,
            "app_identifier": app_identifier,
            "app": app,
            "user": user,
            "include_in_calculations": True,
        }
        transaction_event = cls.get_instance(info, **transaction_event_data)
        transaction_event = cast(payment_models.TransactionEvent, transaction_event)
        transaction_event = cls.construct_instance(
            transaction_event, transaction_event_data
        )

        cls.clean_instance(info, transaction_event)
        already_processed = False
        error_code = None
        error_msg = None
        error_field = None
        with traced_atomic_transaction():
            # The mutation can be called multiple times by the app. That can cause a
            # thread race. We need to be sure, that we will always create a single event
            # on our side for specific action.
            existing_event = get_already_existing_event(transaction_event)
            if existing_event and existing_event.amount != transaction_event.amount:
                error_code = TransactionEventReportErrorCode.INCORRECT_DETAILS.value
                error_msg = (
                    "The transaction with provided `pspReference` and "
                    "`type` already exists with different amount."
                )
                error_field = "pspReference"
            elif existing_event:
                already_processed = True
                transaction_event = existing_event
            elif (
                transaction_event.type == TransactionEventType.AUTHORIZATION_SUCCESS
                and authorization_success_already_exists(transaction.pk)
            ):
                error_code = TransactionEventReportErrorCode.ALREADY_EXISTS.value
                error_msg = (
                    "Event with `AUTHORIZATION_SUCCESS` already "
                    "reported for the transaction. Use "
                    "`AUTHORIZATION_ADJUSTMENT` to change the "
                    "authorization amount."
                )
                error_field = "type"
            else:
                transaction_event.save()

        if error_msg and error_code and error_field:
            create_failed_transaction_event(transaction_event, cause=error_msg)
            raise ValidationError({error_field: ValidationError(error_msg, error_code)})
        if not already_processed:
            if available_actions is not None:
                transaction.available_actions = available_actions
                transaction.save(update_fields=["available_actions"])
            recalculate_transaction_amounts(transaction)
            if transaction.order_id:
                order = cast(order_models.Order, transaction.order)
                update_order_search_vector(order, save=False)
                updates_amounts_for_order(order, save=False)
                order.save(
                    update_fields=[
                        "total_charged_amount",
                        "charge_status",
                        "updated_at",
                        "total_authorized_amount",
                        "authorize_status",
                        "search_vector",
                    ]
                )

        return cls(
            already_processed=already_processed,
            transaction=transaction,
            transaction_event=transaction_event,
            errors=[],
        )
