import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Dict, List, Optional, Union, cast

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Model, QuerySet
from django.utils import timezone
from graphql import GraphQLError

from ...app.models import App
from ...channel import TransactionFlowStrategy
from ...channel.models import Channel
from ...checkout import models as checkout_models
from ...checkout.actions import transaction_amounts_for_checkout_updated
from ...checkout.calculations import (
    calculate_checkout_total_with_gift_cards,
    fetch_checkout_data,
)
from ...checkout.checkout_cleaner import clean_billing_address, clean_checkout_shipping
from ...checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ...checkout.utils import cancel_active_payments
from ...core.error_codes import MetadataErrorCode
from ...core.exceptions import PermissionDenied
from ...core.tracing import traced_atomic_transaction
from ...core.utils import get_client_ip
from ...core.utils.url import validate_storefront_url
from ...order import OrderStatus
from ...order import models as order_models
from ...order.actions import order_refunded, order_transaction_updated
from ...order.events import transaction_event as order_transaction_event
from ...order.fetch import fetch_order_info
from ...order.models import Order
from ...order.search import update_order_search_vector
from ...order.utils import updates_amounts_for_order
from ...payment import (
    PaymentError,
    StorePaymentMethod,
    TransactionAction,
    TransactionEventType,
    TransactionItemIdempotencyUniqueError,
    TransactionKind,
    gateway,
)
from ...payment import models as payment_models
from ...payment.error_codes import (
    PaymentErrorCode,
    TransactionCreateErrorCode,
    TransactionProcessErrorCode,
    TransactionRequestActionErrorCode,
    TransactionUpdateErrorCode,
)
from ...payment.gateway import (
    request_cancelation_action,
    request_charge_action,
    request_refund_action,
)
from ...payment.interface import PaymentGatewayData
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
    get_final_session_statuses,
    handle_transaction_initialize_session,
    handle_transaction_process_session,
    is_currency_supported,
)
from ...permission.auth_filters import AuthorizationFilters
from ...permission.enums import OrderPermissions, PaymentPermissions
from ..account.i18n import I18nMixin
from ..app.dataloaders import get_app_promise
from ..channel.enums import TransactionFlowStrategyEnum
from ..channel.utils import validate_channel
from ..checkout.mutations.utils import get_checkout
from ..checkout.types import Checkout
from ..core import ResolveInfo
from ..core.descriptions import (
    ADDED_IN_31,
    ADDED_IN_34,
    ADDED_IN_313,
    ADDED_IN_314,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
    PREVIEW_FEATURE_DEPRECATED_IN_313_INPUT,
)
from ..core.doc_category import DOC_CATEGORY_CHECKOUT, DOC_CATEGORY_PAYMENTS
from ..core.enums import (
    PaymentGatewayInitializeErrorCode,
    TransactionEventReportErrorCode,
    TransactionInitializeErrorCode,
)
from ..core.fields import JSONString
from ..core.mutations import BaseMutation, ModelMutation
from ..core.scalars import JSON, UUID, PositiveDecimal
from ..core.types import BaseInputObjectType, BaseObjectType
from ..core.types import common as common_types
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_mutation
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
    from ...plugins.manager import PluginsManager


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
        channel = payment.order.channel if payment.order else payment.checkout.channel
        cls.check_channel_permissions(info, [channel.id])
        channel_slug = channel.slug
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
        app = get_app_promise(info.context).get()
        user = info.context.user
        manager = get_plugin_manager_promise(info.context).get()

        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel = payment.order.channel if payment.order else payment.checkout.channel
        cls.check_channel_permissions(info, [channel.id])
        channel_slug = channel.slug
        manager = get_plugin_manager_promise(info.context).get()
        payment_transaction = None
        try:
            payment_transaction = gateway.refund(
                payment,
                manager,
                amount=amount,
                channel_slug=channel_slug,
            )
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR.value)
        if (
            payment.order_id
            and payment_transaction
            and payment_transaction.kind == TransactionKind.REFUND
        ):
            order = cast(order_models.Order, payment.order)
            order_refunded(
                order=order,
                user=user,
                app=app,
                amount=amount,
                payment=payment,
                manager=manager,
            )
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
        channel = payment.order.channel if payment.order else payment.checkout.channel
        cls.check_channel_permissions(info, [channel.id])
        channel_slug = channel.slug
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
        if not metadata_list:
            return
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
        cls, instance: Union[checkout_models.Checkout, order_models.Order], transaction
    ) -> Union[checkout_models.Checkout, order_models.Order]:
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
        if available_actions := transaction.get("available_actions"):
            if "void" in available_actions:
                available_actions.remove("void")
                if "cancel" not in available_actions:
                    available_actions.append("cancel")
                transaction["available_actions"] = available_actions
        elif "available_actions" in transaction:
            # null available_actions is provided, removing it from keys
            transaction.pop("available_actions")
        return instance

    @classmethod
    def create_transaction(
        cls, transaction_input: dict, user, app, save: bool = True
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

        transaction_input["available_actions"] = list(
            set(transaction_input.get("available_actions", []))
        )
        transaction = payment_models.TransactionItem(
            token=uuid.uuid4(),
            use_old_id=True,
            **transaction_input,
            user=user if user and user.is_authenticated else None,
            app_identifier=app_identifier,
            app=app,
        )
        if save:
            transaction.save()
        return transaction

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
    def update_order(
        cls,
        order: order_models.Order,
        money_data: dict,
        update_search_vector: bool = True,
    ) -> None:
        update_fields = []
        if money_data:
            updates_amounts_for_order(order, save=False)
            update_fields.extend(
                [
                    "total_authorized_amount",
                    "total_charged_amount",
                    "authorize_status",
                    "charge_status",
                ]
            )
        if (
            order.channel.automatically_confirm_all_new_orders
            and order.status == OrderStatus.UNCONFIRMED
        ):
            order.status = OrderStatus.UNFULFILLED
            update_fields.append("status")

        if update_search_vector:
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
        transaction: Dict,
        transaction_event=None,
    ):
        order_or_checkout_instance = cls.get_node_or_error(info, id)
        order_or_checkout_instance = cls.validate_instance(
            order_or_checkout_instance, id
        )
        order_or_checkout_instance = cls.validate_input(
            order_or_checkout_instance, transaction=transaction
        )
        transaction_data = {**transaction}
        transaction_data["currency"] = order_or_checkout_instance.currency
        app = get_app_promise(info.context).get()
        user = info.context.user
        manager = get_plugin_manager_promise(info.context).get()

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
            cls.update_order(order, money_data, update_search_vector=True)

            order_info = fetch_order_info(order)
            order_transaction_updated(
                order_info=order_info,
                transaction_item=new_transaction,
                manager=manager,
                user=user,
                app=app,
                previous_authorized_value=Decimal(0),
                previous_charged_value=Decimal(0),
                previous_refunded_value=Decimal(0),
            )
        if transaction_data.get("checkout_id") and money_data:
            transaction_amounts_for_checkout_updated(new_transaction, manager)

        if transaction_event:
            cls.create_transaction_event(transaction_event, new_transaction, user, app)
        return TransactionCreate(transaction=new_transaction)


def get_transaction_item(id, token) -> payment_models.TransactionItem:
    """Get transaction based on token or global ID.

    The transactions created before 3.13 were using the `id` field as a graphql ID.
    From 3.13, the `token` is used as a graphql ID. All transactionItems created
    before 3.13 will use an `int` id as an identification.
    """
    if token:
        db_id = str(token)
    else:
        _, db_id = from_global_id_or_error(
            global_id=id, only_type=TransactionItem, raise_error=True
        )
    if db_id.isdigit():
        query_params = {"id": db_id, "use_old_id": True}
    else:
        query_params = {"token": db_id}
    instance = payment_models.TransactionItem.objects.filter(**query_params).first()
    if not instance:
        raise ValidationError(
            {
                "id": ValidationError(
                    f"Couldn't resolve to a node: {id}",
                    code=TransactionUpdateErrorCode.NOT_FOUND.value,
                )
            }
        )
    return instance


class TransactionUpdate(TransactionCreate):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description=(
                "The ID of the transaction. One of field id or token is required."
            ),
            required=False,
        )
        token = UUID(
            description=(
                "The token of the transaction. One of field id or token is required."
            )
            + ADDED_IN_314,
            required=False,
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
            "Update transaction."
            + ADDED_IN_34
            + PREVIEW_FEATURE
            + "\n\nRequires the following permissions: "
            + f"{AuthorizationFilters.OWNER.name} "
            + f"and {PaymentPermissions.HANDLE_PAYMENTS.name} for apps, "
            f"{PaymentPermissions.HANDLE_PAYMENTS.name} for staff users. "
            f"Staff user cannot update a transaction that is owned by the app."
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
        if transaction_data.get("available_actions") is not None:
            transaction_data["available_actions"] = list(
                set(transaction_data.get("available_actions", []))
            )
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
        if available_actions := transaction_data.get("available_actions"):
            if "void" in available_actions:
                available_actions.remove("void")
                if "cancel" not in available_actions:
                    available_actions.append("cancel")
                transaction_data["available_actions"] = available_actions

    @classmethod
    def update_transaction(
        cls,
        instance: payment_models.TransactionItem,
        transaction_data: dict,
        money_data: dict,
        user: Optional["User"],
        app: Optional["App"],
    ):
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

    @classmethod
    def assign_app_to_transaction_data_if_missing(
        cls,
        transaction: payment_models.TransactionItem,
        transaction_data: dict,
        app: Optional["App"],
    ):
        """Assign app to transaction if missing.

        TransactionItem created before 3.13, doesn't have a relation to the owner app.
        When app updates a transaction, we need to assign the app to the transaction.
        """
        transaction_has_assigned_app = transaction.app_id or transaction.app_identifier
        if app and not transaction.user_id and not transaction_has_assigned_app:
            transaction_data["app"] = app
            transaction_data["app_identifier"] = app.identifier

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        token=None,
        id=None,
        transaction=None,
        transaction_event=None,
    ):
        validate_one_of_args_is_in_mutation("id", id, "token", token)
        instance = get_transaction_item(id, token)
        user = info.context.user
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()

        cls.check_can_update(
            transaction=instance,
            user=user if user and user.is_authenticated else None,
            app=app,
        )
        money_data = {}
        previous_transaction_psp_reference = instance.psp_reference
        previous_authorized_value = instance.authorized_value
        previous_charged_value = instance.charged_value
        previous_refunded_value = instance.refunded_value

        if transaction:
            cls.validate_transaction_input(instance, transaction)
            cls.assign_app_to_transaction_data_if_missing(instance, transaction, app)
            cls.cleanup_metadata_data(transaction)
            money_data = cls.get_money_data_from_input(transaction)
            cls.update_transaction(instance, transaction, money_data, user, app)

        event = None
        if transaction_event:
            event = cls.create_transaction_event(transaction_event, instance, user, app)
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
        if instance.order_id:
            order = cast(order_models.Order, instance.order)
            should_update_search_vector = bool(
                (instance.psp_reference != previous_transaction_psp_reference)
                or (event and event.psp_reference)
            )
            cls.update_order(
                order, money_data, update_search_vector=should_update_search_vector
            )
            order_info = fetch_order_info(order)
            order_transaction_updated(
                order_info=order_info,
                transaction_item=instance,
                manager=manager,
                user=user,
                app=app,
                previous_authorized_value=previous_authorized_value,
                previous_charged_value=previous_charged_value,
                previous_refunded_value=previous_refunded_value,
            )
        if instance.checkout_id and money_data:
            manager = get_plugin_manager_promise(info.context).get()
            transaction_amounts_for_checkout_updated(instance, manager)

        return TransactionUpdate(transaction=instance)


class TransactionRequestAction(BaseMutation):
    transaction = graphene.Field(TransactionItem)

    class Arguments:
        id = graphene.ID(
            description=(
                "The ID of the transaction. One of field id or token is required."
            ),
            required=False,
        )
        token = UUID(
            description=(
                "The token of the transaction. One of field id or token is required."
            )
            + ADDED_IN_314,
            required=False,
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
        cls,
        action,
        action_kwargs,
        action_value: Optional[Decimal],
        user: Optional["User"],
        app: Optional[App],
    ):
        if action == TransactionAction.VOID or action == TransactionAction.CANCEL:
            transaction = action_kwargs["transaction"]
            request_event = cls.create_transaction_event_requested(
                transaction, 0, action, user=user, app=app
            )
            request_cancelation_action(
                **action_kwargs,
                cancel_value=None,
                request_event=request_event,
                action=action,
            )
        elif action == TransactionAction.CHARGE:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.authorized_value
            action_value = min(action_value, transaction.authorized_value)
            request_event = cls.create_transaction_event_requested(
                transaction, action_value, TransactionAction.CHARGE, user=user, app=app
            )
            request_charge_action(
                **action_kwargs, charge_value=action_value, request_event=request_event
            )
        elif action == TransactionAction.REFUND:
            transaction = action_kwargs["transaction"]
            action_value = action_value or transaction.charged_value
            action_value = min(action_value, transaction.charged_value)
            request_event = cls.create_transaction_event_requested(
                transaction, action_value, TransactionAction.REFUND, user=user, app=app
            )
            request_refund_action(
                **action_kwargs, refund_value=action_value, request_event=request_event
            )

    @classmethod
    def create_transaction_event_requested(
        cls, transaction, action_value, action, user=None, app=None
    ):
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
            user=user,
            app=app,
            app_identifier=app.identifier if app else None,
            idempotency_key=str(uuid.uuid4()),
        )

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        id = data.get("id")
        token = data.get("token")
        action_type = data["action_type"]
        action_value = data.get("amount")
        validate_one_of_args_is_in_mutation("id", id, "token", token)
        transaction = get_transaction_item(id, token)
        if transaction.order_id:
            order = cast(Order, transaction.order)
            channel = order.channel
        else:
            checkout = cast(Checkout, transaction.checkout)
            channel = checkout.channel
        cls.check_channel_permissions(info, [channel.id])
        channel_slug = channel.slug
        user = info.context.user
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        action_kwargs = {
            "channel_slug": channel_slug,
            "user": user,
            "app": app,
            "transaction": transaction,
            "manager": manager,
        }

        try:
            cls.handle_transaction_action(
                action_type, action_kwargs, action_value, user, app
            )
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
            description=(
                "The ID of the transaction. One of field id or token is required."
            ),
            required=False,
        )
        token = UUID(
            description=(
                "The token of the transaction. One of field id or token is required."
            )
            + ADDED_IN_314,
            required=False,
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
            + f"and {PaymentPermissions.HANDLE_PAYMENTS.name} for apps, "
            f"{PaymentPermissions.HANDLE_PAYMENTS.name} for staff users. "
            f"Staff user cannot update a transaction that is owned by the app."
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
    def update_transaction(
        cls,
        transaction: payment_models.TransactionItem,
        transaction_event: payment_models.TransactionEvent,
        available_actions: Optional[list[str]] = None,
        app: Optional["App"] = None,
    ):
        fields_to_update = [
            "authorized_value",
            "charged_value",
            "refunded_value",
            "canceled_value",
            "authorize_pending_value",
            "charge_pending_value",
            "refund_pending_value",
            "cancel_pending_value",
            "modified_at",
        ]

        if (
            transaction_event.type
            in [
                TransactionEventType.AUTHORIZATION_REQUEST,
                TransactionEventType.AUTHORIZATION_SUCCESS,
                TransactionEventType.CHARGE_REQUEST,
                TransactionEventType.CHARGE_SUCCESS,
            ]
            and not transaction.psp_reference
        ):
            transaction.psp_reference = transaction_event.psp_reference
            fields_to_update.append("psp_reference")

        if available_actions is not None:
            if "void" in available_actions:
                available_actions.remove("void")
                if "cancel" not in available_actions:
                    available_actions.append("cancel")
            transaction.available_actions = available_actions
            fields_to_update.append("available_actions")

        recalculate_transaction_amounts(transaction, save=False)
        transaction_has_assigned_app = transaction.app_id or transaction.app_identifier
        if app and not transaction.user_id and not transaction_has_assigned_app:
            transaction.app_id = app.pk
            transaction.app_identifier = app.identifier
            fields_to_update.append("app")
            fields_to_update.append("app_identifier")
        transaction.save(update_fields=fields_to_update)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        root,
        info: ResolveInfo,
        /,
        *,
        psp_reference,
        type,
        amount,
        token=None,
        id=None,
        time=None,
        external_url=None,
        message=None,
        available_actions=None,
    ):
        validate_one_of_args_is_in_mutation("id", id, "token", token)
        transaction = get_transaction_item(id, token)
        user = info.context.user
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()

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

        if available_actions is not None:
            available_actions = list(set(available_actions))

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
            previous_authorized_value = transaction.authorized_value
            previous_charged_value = transaction.charged_value
            previous_refunded_value = transaction.refunded_value
            cls.update_transaction(
                transaction,
                transaction_event,
                available_actions=available_actions,
                app=app,
            )
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
                order_info = fetch_order_info(order)
                order_transaction_updated(
                    order_info=order_info,
                    transaction_item=transaction,
                    manager=manager,
                    user=user,
                    app=app,
                    previous_authorized_value=previous_authorized_value,
                    previous_charged_value=previous_charged_value,
                    previous_refunded_value=previous_refunded_value,
                )
            if transaction.checkout_id:
                manager = get_plugin_manager_promise(info.context).get()
                transaction_amounts_for_checkout_updated(transaction, manager)
        elif available_actions is not None and set(
            transaction.available_actions
        ) != set(available_actions):
            transaction.available_actions = available_actions
            transaction.save(update_fields=["available_actions"])

        return cls(
            already_processed=already_processed,
            transaction=transaction,
            transaction_event=transaction_event,
            errors=[],
        )


class PaymentGatewayConfig(BaseObjectType):
    id = graphene.String(required=True, description="The app identifier.")
    data = graphene.Field(
        JSON, description="The JSON data required to initialize the payment gateway."
    )
    errors = common_types.NonNullList(common_types.PaymentGatewayConfigError)

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class PaymentGatewayToInitialize(BaseInputObjectType):
    id = graphene.String(
        required=True,
        description="The identifier of the payment gateway app to initialize.",
    )
    data = graphene.Field(
        JSON, description="The data that will be passed to the payment gateway."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionSessionBase(BaseMutation):
    class Meta:
        abstract = True

    TRANSACTION_ITEMS_LIMIT = 100

    @classmethod
    def clean_source_object(
        cls,
        info,
        id,
        incorrect_type_error_code: str,
        not_found_error: str,
        manager: "PluginsManager",
    ) -> Union[checkout_models.Checkout, order_models.Order]:
        source_object_type, source_object_id = from_global_id_or_error(
            id, raise_error=False
        )
        if not source_object_type or not source_object_id:
            raise GraphQLError(f"Couldn't resolve id: {id}.")

        if source_object_type not in ["Checkout", "Order"]:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Must receive a `Checkout` or `Order` id.",
                        code=incorrect_type_error_code,
                    )
                }
            )
        source_object: Optional[Union[checkout_models.Checkout, order_models.Order]]
        if source_object_type == "Checkout":
            source_object = (
                checkout_models.Checkout.objects.select_related("channel")
                .prefetch_related("payment_transactions")
                .filter(pk=source_object_id)
                .first()
            )
            if source_object:
                lines, _ = fetch_checkout_lines(source_object)
                checkout_info = fetch_checkout_info(source_object, lines, manager)
                checkout_info, _ = fetch_checkout_data(checkout_info, manager, lines)
                source_object = checkout_info.checkout
        else:
            source_object = (
                order_models.Order.objects.select_related("channel")
                .prefetch_related("payment_transactions")
                .filter(pk=source_object_id)
                .first()
            )

        if not source_object:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "`Order` or `Checkout` not found.",
                        code=not_found_error,
                    )
                }
            )

        if (
            source_object.payment_transactions.count()
            >= settings.TRANSACTION_ITEMS_LIMIT
        ):
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"{source_object_type} transactions limit of "
                        f"{settings.TRANSACTION_ITEMS_LIMIT} reached.",
                        code=TransactionInitializeErrorCode.INVALID.value,
                    )
                }
            )

        return source_object

    @classmethod
    def get_amount(
        cls,
        source_object: Union[checkout_models.Checkout, order_models.Order],
        input_amount: Optional[Decimal],
    ) -> Decimal:
        if input_amount is not None:
            return input_amount
        amount: Decimal = source_object.total_gross_amount
        transactions = source_object.payment_transactions.all()
        for transaction_item in transactions:
            amount_to_reduce = transaction_item.authorized_value
            if amount_to_reduce < transaction_item.charged_value:
                amount_to_reduce = transaction_item.charged_value
            amount -= amount_to_reduce
            amount -= transaction_item.authorize_pending_value
            amount -= transaction_item.charge_pending_value

        return amount if amount >= Decimal(0) else Decimal(0)


class PaymentGatewayInitialize(TransactionSessionBase):
    gateway_configs = common_types.NonNullList(PaymentGatewayConfig)

    class Arguments:
        id = graphene.ID(
            description="The ID of the checkout or order.",
            required=True,
        )
        amount = graphene.Argument(
            PositiveDecimal,
            description=(
                "The amount requested for initializing the payment gateway. "
                "If not provided, the difference between checkout.total - "
                "transactions that are already processed will be send."
            ),
        )
        payment_gateways = graphene.List(
            graphene.NonNull(PaymentGatewayToInitialize),
            description="List of payment gateways to initialize.",
            required=False,
        )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        description = (
            "Initializes a payment gateway session. It triggers the webhook "
            "`PAYMENT_GATEWAY_INITIALIZE_SESSION`, to the requested `paymentGateways`. "
            "If `paymentGateways` is not provided, the webhook will be send to all "
            "subscribed payment gateways. There is a limit of "
            f"{settings.TRANSACTION_ITEMS_LIMIT} transaction items per checkout / "
            "order." + ADDED_IN_313 + PREVIEW_FEATURE
        )
        error_type_class = common_types.PaymentGatewayInitializeError

    @classmethod
    def prepare_response(
        cls,
        payment_gateways_input: list[PaymentGatewayData],
        payment_gateways_response: list[PaymentGatewayData],
    ) -> list[PaymentGatewayConfig]:
        response = []
        payment_gateways_response_dict = {
            gateway.app_identifier: gateway for gateway in payment_gateways_response
        }

        payment_gateways_input_dict = (
            {gateway.app_identifier: gateway for gateway in payment_gateways_input}
            if payment_gateways_input
            else payment_gateways_response_dict
        )
        for identifier in payment_gateways_input_dict:
            app_identifier = identifier
            payment_gateway_response = payment_gateways_response_dict.get(identifier)
            if payment_gateway_response:
                response_data = payment_gateway_response.data
                errors = []
                if payment_gateway_response.error:
                    code = common_types.PaymentGatewayConfigErrorCode.INVALID.value
                    errors = [
                        {
                            "field": "id",
                            "message": payment_gateway_response.error,
                            "code": code,
                        }
                    ]

            else:
                response_data = None
                code = common_types.PaymentGatewayConfigErrorCode.NOT_FOUND.value
                msg = (
                    "Active app with `HANDLE_PAYMENT` permissions or "
                    "app webhook not found."
                )
                errors = [
                    {
                        "field": "id",
                        "message": msg,
                        "code": code,
                    }
                ]
            data_to_return = response_data.get("data") if response_data else None
            response.append(
                PaymentGatewayConfig(
                    id=app_identifier, data=data_to_return, errors=errors
                )
            )
        return response

    @classmethod
    def perform_mutation(cls, root, info, *, id, amount=None, payment_gateways=None):
        manager = get_plugin_manager_promise(info.context).get()
        source_object = cls.clean_source_object(
            info,
            id,
            PaymentGatewayInitializeErrorCode.INVALID.value,
            PaymentGatewayInitializeErrorCode.NOT_FOUND.value,
            manager=manager,
        )
        payment_gateways_data = []
        if payment_gateways:
            payment_gateways_data = [
                PaymentGatewayData(
                    app_identifier=gateway["id"], data=gateway.get("data")
                )
                for gateway in payment_gateways
            ]
        amount = cls.get_amount(source_object, amount)
        response_data = manager.payment_gateway_initialize_session(
            amount, payment_gateways_data, source_object
        )
        return cls(
            gateway_configs=cls.prepare_response(payment_gateways_data, response_data),
            errors=[],
        )


class TransactionInitialize(TransactionSessionBase):
    transaction = graphene.Field(
        TransactionItem, description="The initialized transaction."
    )
    transaction_event = graphene.Field(
        TransactionEvent,
        description="The event created for the initialized transaction.",
    )
    data = graphene.Field(
        JSON, description="The JSON data required to finalize the payment."
    )

    class Arguments:
        id = graphene.ID(
            description="The ID of the checkout or order.",
            required=True,
        )
        idempotency_key = graphene.String(
            description=(
                "The idempotency key assigned to the action. It will be passed to the "
                "payment app to discover potential duplicate actions. If not provided, "
                "the default one will be generated. If empty string provided, INVALID "
                "error code will be raised." + ADDED_IN_314
            )
        )
        amount = graphene.Argument(
            PositiveDecimal,
            description=(
                "The amount requested for initializing the payment gateway. "
                "If not provided, the difference between checkout.total - "
                "transactions that are already processed will be send."
            ),
        )
        action = graphene.Argument(
            TransactionFlowStrategyEnum,
            description=(
                "The expected action called for the transaction. By default, the "
                "`channel.defaultTransactionFlowStrategy` will be used. The field "
                "can be used only by app that has `HANDLE_PAYMENTS` permission."
            ),
        )
        payment_gateway = graphene.Argument(
            PaymentGatewayToInitialize,
            description="Payment gateway used to initialize the transaction.",
            required=True,
        )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        description = (
            "Initializes a transaction session. It triggers the webhook "
            "`TRANSACTION_INITIALIZE_SESSION`, to the requested `paymentGateways`. "
            f"There is a limit of {settings.TRANSACTION_ITEMS_LIMIT} transaction "
            "items per checkout / order." + ADDED_IN_313 + PREVIEW_FEATURE
        )
        error_type_class = common_types.TransactionInitializeError

    @classmethod
    def clean_action(cls, info, action: Optional[str], channel: "Channel"):
        if not action:
            return channel.default_transaction_flow_strategy
        app = get_app_promise(info.context).get()
        if not app or not app.has_perm(PaymentPermissions.HANDLE_PAYMENTS):
            raise PermissionDenied(permissions=[PaymentPermissions.HANDLE_PAYMENTS])
        return action

    @classmethod
    def clean_app_from_payment_gateway(cls, payment_gateway: PaymentGatewayData) -> App:
        app = App.objects.filter(
            identifier=payment_gateway.app_identifier,
            removed_at__isnull=True,
            is_active=True,
        ).first()
        if not app:
            raise ValidationError(
                {
                    "payment_gateway": ValidationError(
                        message="App with provided identifier not found.",
                        code=TransactionInitializeErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return app

    @classmethod
    def clean_idempotency_key(cls, idempotency_key: Optional[str]):
        if not idempotency_key and isinstance(idempotency_key, str):
            raise ValidationError(
                {
                    "idempotency_key": ValidationError(
                        message="Cannot be provided as an empty string.",
                        code=TransactionInitializeErrorCode.INVALID.value,
                    )
                }
            )

        if not idempotency_key:
            idempotency_key = str(uuid.uuid4())
        return idempotency_key

    @classmethod
    def perform_mutation(
        cls,
        root,
        info,
        *,
        id,
        payment_gateway,
        amount=None,
        action=None,
        idempotency_key=None
    ):
        manager = get_plugin_manager_promise(info.context).get()
        payment_gateway_data = PaymentGatewayData(
            app_identifier=payment_gateway["id"], data=payment_gateway.get("data")
        )
        idempotency_key = cls.clean_idempotency_key(idempotency_key)

        source_object = cls.clean_source_object(
            info,
            id,
            TransactionInitializeErrorCode.INVALID.value,
            TransactionInitializeErrorCode.NOT_FOUND.value,
            manager=manager,
        )
        action = cls.clean_action(info, action, source_object.channel)

        amount = cls.get_amount(
            source_object,
            amount,
        )
        app = cls.clean_app_from_payment_gateway(payment_gateway_data)

        try:
            transaction, event, data = handle_transaction_initialize_session(
                source_object=source_object,
                payment_gateway=payment_gateway_data,
                amount=amount,
                action=action,
                app=app,
                manager=manager,
                idempotency_key=idempotency_key,
            )
        except TransactionItemIdempotencyUniqueError:
            raise ValidationError(
                {
                    "idempotency_key": ValidationError(
                        message=(
                            "Different transaction with provided idempotency key "
                            "already exists."
                        ),
                        code=TransactionInitializeErrorCode.UNIQUE.value,
                    )
                }
            )

        return cls(transaction=transaction, transaction_event=event, data=data)


class TransactionProcess(BaseMutation):
    transaction = graphene.Field(
        TransactionItem, description="The processed transaction."
    )
    transaction_event = graphene.Field(
        TransactionEvent,
        description="The event created for the processed transaction.",
    )
    data = graphene.Field(
        JSON, description="The json data required to finalize the payment."
    )

    class Arguments:
        id = graphene.ID(
            description=(
                "The ID of the transaction to process. "
                "One of field id or token is required."
            ),
            required=False,
        )
        token = UUID(
            description=(
                "The token of the transaction to process. "
                "One of field id or token is required."
            )
            + ADDED_IN_314,
            required=False,
        )
        data = graphene.Argument(
            JSON, description="The data that will be passed to the payment gateway."
        )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        description = (
            "Processes a transaction session. It triggers the webhook "
            "`TRANSACTION_PROCESS_SESSION`, to the assigned `paymentGateways`. "
            + ADDED_IN_313
            + PREVIEW_FEATURE
        )
        error_type_class = common_types.TransactionProcessError

    @classmethod
    def get_action(cls, event: payment_models.TransactionEvent, channel: "Channel"):
        if event.type == TransactionEventType.AUTHORIZATION_REQUEST:
            return TransactionFlowStrategy.AUTHORIZATION
        elif event.type == TransactionEventType.CHARGE_REQUEST:
            return TransactionFlowStrategy.CHARGE

        return channel.default_transaction_flow_strategy

    @classmethod
    def get_source_object(
        cls, transaction_item: payment_models.TransactionItem
    ) -> Union[checkout_models.Checkout, order_models.Order]:
        if transaction_item.checkout_id:
            checkout = cast(checkout_models.Checkout, transaction_item.checkout)
            return checkout
        if transaction_item.order_id:
            order = cast(order_models.Order, transaction_item.order)
            return order
        raise ValidationError(
            {
                "id": ValidationError(
                    "Transaction doesn't have attached order or checkout.",
                    code=TransactionProcessErrorCode.INVALID.value,
                )
            }
        )

    @classmethod
    def get_request_event(cls, events: QuerySet) -> payment_models.TransactionEvent:
        """Get event with details of requested action.

        This searches for a request event with the appropriate type and
        include_in_calculations set to false. Request events created from
        transactionInitialize have their include_in_calculation set to false by default.
        """
        for event in events:
            if (
                event.type
                in [
                    TransactionEventType.AUTHORIZATION_REQUEST,
                    TransactionEventType.CHARGE_REQUEST,
                ]
                and not event.include_in_calculations
            ):
                return event
        raise ValidationError(
            {
                "id": ValidationError(
                    "Missing call of `transactionInitialize` mutation.",
                    code=TransactionProcessErrorCode.INVALID.value,
                )
            }
        )

    @classmethod
    def get_already_processed_event(cls, events) -> Optional[TransactionEvent]:
        for event in events:
            if (
                event.type in get_final_session_statuses()
                and event.include_in_calculations
            ):
                return event
        return None

    @classmethod
    def clean_payment_app(cls, transaction_item: payment_models.TransactionItem) -> App:
        if not transaction_item.app_identifier:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Transaction doesn't have attached app that could process the "
                        "request.",
                        code=TransactionProcessErrorCode.MISSING_PAYMENT_APP_RELATION.value,
                    )
                }
            )
        app = App.objects.filter(
            identifier=transaction_item.app_identifier,
            removed_at__isnull=True,
            is_active=True,
        ).first()
        if not app:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Payment app attached to the transaction, doesn't exist.",
                        code=TransactionProcessErrorCode.MISSING_PAYMENT_APP.value,
                    )
                }
            )
        return app

    @classmethod
    def perform_mutation(cls, root, info, *, token=None, id=None, data=None):
        validate_one_of_args_is_in_mutation("id", id, "token", token)
        transaction_item = get_transaction_item(id, token)
        events = transaction_item.events.all()
        if processed_event := cls.get_already_processed_event(events):
            return cls(
                transaction=transaction_item,
                transaction_event=processed_event,
                data=None,
            )
        request_event = cls.get_request_event(events)
        source_object = cls.get_source_object(transaction_item)
        app = cls.clean_payment_app(transaction_item)
        app_identifier = app.identifier
        app_identifier = cast(str, app_identifier)
        action = cls.get_action(request_event, source_object.channel)
        manager = get_plugin_manager_promise(info.context).get()
        event, data = handle_transaction_process_session(
            transaction_item=transaction_item,
            source_object=source_object,
            payment_gateway=PaymentGatewayData(
                app_identifier=app_identifier, data=data
            ),
            app=app,
            action=action,
            manager=manager,
            request_event=request_event,
        )

        transaction_item.refresh_from_db()
        return cls(transaction=transaction_item, transaction_event=event, data=data)
