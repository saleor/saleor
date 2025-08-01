import json
import logging
from decimal import Decimal
from typing import Any, Optional, cast, get_args, overload
from uuid import UUID

import graphene
from babel.numbers import get_currency_precision
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from pydantic import ValidationError

from ..account.models import User
from ..app.models import App
from ..channel import TransactionFlowStrategy
from ..checkout import calculations
from ..checkout.actions import (
    transaction_amounts_for_checkout_updated,
    transaction_amounts_for_checkout_updated_without_price_recalculation,
    update_last_transaction_modified_at_for_checkout,
)
from ..checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ..checkout.models import Checkout
from ..checkout.payment_utils import update_refundable_for_checkout
from ..core.db.connection import allow_writer
from ..core.prices import quantize_price
from ..core.tracing import traced_atomic_transaction
from ..graphql.core.utils import str_to_enum
from ..order import OrderStatus
from ..order.actions import order_transaction_updated
from ..order.fetch import fetch_order_info
from ..order.models import Order, OrderGrantedRefund
from ..order.search import update_order_search_vector
from ..order.utils import (
    calculate_order_granted_refund_status,
    refresh_order_status,
    update_order_authorize_data,
    updates_amounts_for_order,
)
from ..plugins.manager import PluginsManager, get_plugins_manager
from ..webhook.response_schemas import transaction as transaction_schemas
from ..webhook.response_schemas.utils.helpers import parse_validation_error
from . import (
    ChargeStatus,
    GatewayError,
    PaymentError,
    StorePaymentMethod,
    TransactionAction,
    TransactionEventType,
    TransactionItemIdempotencyUniqueError,
    TransactionKind,
)
from .error_codes import PaymentErrorCode
from .interface import (
    AddressData,
    GatewayResponse,
    PaymentData,
    PaymentGatewayData,
    PaymentLineData,
    PaymentLinesData,
    PaymentMethodDetails,
    PaymentMethodInfo,
    RefundData,
    StorePaymentMethodEnum,
    TransactionData,
    TransactionProcessActionData,
    TransactionRequestEventResponse,
    TransactionRequestResponse,
    TransactionSessionData,
    TransactionSessionResponse,
)
from .lock_objects import (
    get_checkout_and_transaction_item_locked_for_update,
    get_order_and_transaction_item_locked_for_update,
)
from .models import Payment, Transaction, TransactionEvent, TransactionItem
from .transaction_item_calculations import recalculate_transaction_amounts

logger = logging.getLogger(__name__)

GENERIC_TRANSACTION_ERROR = "Transaction was unsuccessful"
ALLOWED_GATEWAY_KINDS = {choices[0] for choices in TransactionKind.CHOICES}
TRANSACTION_EVENT_MSG_MAX_LENGTH: int = TransactionEvent._meta.get_field(  # type: ignore[assignment]
    "message"
).max_length
SESSION_REQUEST_EVENT_TYPE = "session-request"


def _recalculate_last_refund_success_for_transaction(
    transaction_item: TransactionItem,
    request_event: TransactionEvent,
    response_event: TransactionEvent | None = None,
) -> bool:
    """Recalculate last_refund_success for transaction.

    Based on the request and response events, we can determine if the last refund was
    successful or not.
    If response event is none, the request event can store the details updated based
    on the response from the gateway (in case of async flow).
    If the request event doesn't have these details, we can assume that the last
    refund failed.
    As a response we return the boolean flag which determines if the transaction's last
    refund success was changed.
    """
    last_refund_success_changed = False
    last_refund_success = transaction_item.last_refund_success
    if response_event:
        if response_event.type in [
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.CANCEL_SUCCESS,
        ]:
            last_refund_success_changed = last_refund_success is not True
            transaction_item.last_refund_success = True

        if response_event.type in [
            TransactionEventType.REFUND_FAILURE,
            TransactionEventType.CANCEL_FAILURE,
        ]:
            last_refund_success_changed = last_refund_success is not False
            transaction_item.last_refund_success = False
    elif request_event.type in [
        TransactionEventType.REFUND_REQUEST,
        TransactionEventType.CANCEL_REQUEST,
    ]:
        if request_event.include_in_calculations:
            last_refund_success_changed = last_refund_success is not True
            transaction_item.last_refund_success = True
        else:
            last_refund_success_changed = last_refund_success is not False
            transaction_item.last_refund_success = False
    return last_refund_success_changed


def recalculate_refundable_for_checkout(
    transaction_item: TransactionItem,
    request_event: TransactionEvent,
    response_event: TransactionEvent | None = None,
):
    last_refund_success_changed = _recalculate_last_refund_success_for_transaction(
        transaction_item,
        request_event,
        response_event,
    )
    if last_refund_success_changed:
        transaction_item.save(update_fields=["last_refund_success"])

    if transaction_item.checkout_id:
        update_refundable_for_checkout(transaction_item.checkout_id)


def create_payment_lines_information(
    payment: Payment,
    manager: PluginsManager,
) -> PaymentLinesData:
    checkout = payment.checkout
    order = payment.order

    if checkout:
        return create_checkout_payment_lines_information(checkout, manager)
    if order:
        return create_order_payment_lines_information(order)

    return PaymentLinesData(
        shipping_amount=Decimal("0.00"),
        voucher_amount=Decimal("0.00"),
        lines=[],
    )


def create_checkout_payment_lines_information(
    checkout: Checkout, manager: PluginsManager
) -> PaymentLinesData:
    line_items = []
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    address = checkout_info.shipping_address or checkout_info.billing_address

    for line_info in lines:
        unit_price = calculations.checkout_line_unit_price(
            manager=manager,
            checkout_info=checkout_info,
            lines=lines,
            checkout_line_info=line_info,
        )
        unit_gross = unit_price.gross.amount

        quantity = line_info.line.quantity
        product_name = f"{line_info.variant.product.name}, {line_info.variant.name}"
        product_sku = line_info.variant.sku
        line_items.append(
            PaymentLineData(
                quantity=quantity,
                product_name=product_name,
                product_sku=product_sku,
                variant_id=line_info.variant.id,
                amount=unit_gross,
            )
        )
    shipping_amount = calculations.checkout_shipping_price(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=address,
    ).gross.amount
    voucher_amount = -checkout.discount_amount

    return PaymentLinesData(
        shipping_amount=shipping_amount,
        voucher_amount=voucher_amount,
        lines=line_items,
    )


def create_order_payment_lines_information(order: Order) -> PaymentLinesData:
    line_items = []
    for order_line in order.lines.all():
        product_name = f"{order_line.product_name}, {order_line.variant_name}"

        variant_id = order_line.variant_id
        if variant_id is None:
            continue

        line_items.append(
            PaymentLineData(
                quantity=order_line.quantity,
                product_name=product_name,
                product_sku=order_line.product_sku,
                variant_id=variant_id,
                amount=order_line.unit_price_gross_amount,
            )
        )

    shipping_amount = order.shipping_price_gross_amount
    voucher_amount = order.total_gross_amount - order.undiscounted_total_gross_amount

    return PaymentLinesData(
        shipping_amount=shipping_amount,
        voucher_amount=voucher_amount,
        lines=line_items,
    )


def generate_transactions_data(payment: Payment) -> list[TransactionData]:
    return [
        TransactionData(
            token=t.token,
            is_success=t.is_success,
            kind=t.kind,
            gateway_response=t.gateway_response,
            amount={
                "amount": str(quantize_price(t.amount, t.currency)),
                "currency": t.currency,
            },
        )
        for t in payment.transactions.all()
    ]


def create_payment_information(
    payment: Payment,
    payment_token: str | None = None,
    amount: Decimal | None = None,
    customer_id: str | None = None,
    store_source: bool = False,
    refund_data: RefundData | None = None,
    additional_data: dict | None = None,
    manager: PluginsManager | None = None,
) -> PaymentData:
    """Extract order information along with payment details.

    Returns information required to process payment and additional
    billing/shipping addresses for optional fraud-prevention mechanisms.
    """
    if checkout := payment.checkout:
        billing = checkout.billing_address
        shipping = checkout.shipping_address
        email = cast(str, checkout.get_customer_email())
        user_id = checkout.user_id
        checkout_token = str(checkout.token)
        from ..checkout.utils import get_checkout_metadata

        checkout_metadata = None
        checkout_metadata_storage = get_checkout_metadata(checkout)
        if checkout_metadata_storage:
            checkout_metadata = checkout_metadata_storage.metadata
    elif order := payment.order:
        billing = order.billing_address
        shipping = order.shipping_address
        email = order.user_email
        user_id = order.user_id
        checkout_token = order.checkout_token
        checkout_metadata = None
    else:
        billing = None
        shipping = None
        email = payment.billing_email
        user_id = None
        checkout_token = ""
        checkout_metadata = None

    billing_address = AddressData(**billing.as_data()) if billing else None
    shipping_address = AddressData(**shipping.as_data()) if shipping else None

    order = payment.order
    order_id = order.pk if order else None
    channel_slug = order.channel.slug if order and order.channel else None
    graphql_payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    graphql_customer_id = None
    if user_id:
        graphql_customer_id = graphene.Node.to_global_id("User", user_id)

    return PaymentData(
        gateway=payment.gateway,
        token=payment_token,
        amount=amount or payment.total,
        currency=payment.currency,
        billing=billing_address,
        shipping=shipping_address,
        order_id=str(order_id),
        order_channel_slug=channel_slug,
        payment_id=payment.pk,
        graphql_payment_id=graphql_payment_id,
        customer_ip_address=payment.customer_ip_address,
        customer_id=customer_id,
        customer_email=email,
        reuse_source=store_source,
        data=additional_data or {},
        graphql_customer_id=graphql_customer_id,
        store_payment_method=StorePaymentMethodEnum[
            payment.store_payment_method.upper()
        ],
        checkout_token=checkout_token,
        checkout_metadata=checkout_metadata,
        payment_metadata=payment.metadata,
        psp_reference=payment.psp_reference,
        refund_data=refund_data,
        transactions=generate_transactions_data(payment),
        _resolve_lines_data=lambda: create_payment_lines_information(
            payment, manager or get_plugins_manager(allow_replica=False)
        ),
    )


def create_payment(
    gateway: str,
    total: Decimal,
    currency: str,
    email: str,
    customer_ip_address: str | None = None,
    payment_token: str | None = None,
    extra_data: dict | None = None,
    checkout: Checkout | None = None,
    order: Order | None = None,
    return_url: str | None = None,
    external_reference: str | None = None,
    store_payment_method: str = StorePaymentMethod.NONE,
    metadata: dict[str, str] | None = None,
) -> Payment:
    """Create a payment instance.

    This method is responsible for creating payment instances that works for
    both Django views and GraphQL mutations.
    """

    if extra_data is None:
        extra_data = {}

    data = {
        "is_active": True,
        "customer_ip_address": customer_ip_address or "",
        "extra_data": json.dumps(extra_data),
        "token": payment_token or "",
    }

    if checkout:
        data["checkout"] = checkout
        billing_address = checkout.billing_address
    elif order:
        data["order"] = order
        billing_address = order.billing_address
    else:
        raise TypeError("Must provide checkout or order to create a payment.")

    if not billing_address:
        raise PaymentError(
            "Order does not have a billing address.",
            code=PaymentErrorCode.BILLING_ADDRESS_NOT_SET.value,
        )

    defaults = {
        "billing_email": email,
        "billing_first_name": billing_address.first_name,
        "billing_last_name": billing_address.last_name,
        "billing_company_name": billing_address.company_name,
        "billing_address_1": billing_address.street_address_1,
        "billing_address_2": billing_address.street_address_2,
        "billing_city": billing_address.city,
        "billing_postal_code": billing_address.postal_code,
        "billing_country_code": billing_address.country.code,
        "billing_country_area": billing_address.country_area,
        "currency": currency,
        "gateway": gateway,
        "total": total,
        "return_url": return_url,
        "partial": False,
        "psp_reference": external_reference or "",
        "store_payment_method": store_payment_method,
        "metadata": {} if metadata is None else metadata,
    }

    with allow_writer():
        payment, _ = Payment.objects.get_or_create(defaults=defaults, **data)
    return payment


def get_already_processed_transaction(
    payment: "Payment", gateway_response: GatewayResponse
):
    transaction = payment.transactions.filter(
        is_success=gateway_response.is_success,
        action_required=gateway_response.action_required,
        token=gateway_response.transaction_id,
        kind=gateway_response.kind,
        amount=gateway_response.amount,
        currency=gateway_response.currency,
    ).last()
    return transaction


@overload
def create_transaction(
    payment: Payment,
    *,
    kind: str,
    payment_information: PaymentData,
    action_required: bool = False,
    gateway_response: GatewayResponse | None = None,
    error_msg=None,
    is_success=False,
) -> Transaction: ...


@overload
def create_transaction(
    payment: Payment,
    *,
    kind: str,
    payment_information: PaymentData | None,
    action_required: bool = False,
    gateway_response: GatewayResponse,
    error_msg=None,
    is_success=False,
) -> Transaction: ...


def create_transaction(
    payment: Payment,
    *,
    kind: str,
    payment_information: PaymentData | None,
    action_required: bool = False,
    gateway_response: GatewayResponse | None = None,
    error_msg=None,
    is_success=False,
) -> Transaction:
    """Create a transaction based on transaction kind and gateway response."""
    # Default values for token, amount, currency are only used in cases where
    # response from gateway was invalid or an exception occurred
    if not gateway_response:
        if not payment_information:
            raise ValueError("Payment information is required to create a transaction.")
        gateway_response = GatewayResponse(
            kind=kind,
            action_required=False,
            transaction_id=payment_information.token or "",
            is_success=is_success,
            amount=payment_information.amount,
            currency=payment_information.currency,
            error=error_msg,
            raw_response={},
        )

    txn = Transaction.objects.create(
        payment=payment,
        action_required=action_required,
        kind=gateway_response.kind,
        token=gateway_response.transaction_id,
        is_success=gateway_response.is_success,
        amount=gateway_response.amount,
        currency=gateway_response.currency,
        error=gateway_response.error,
        customer_id=gateway_response.customer_id,
        gateway_response=gateway_response.raw_response or {},
        action_required_data=gateway_response.action_required_data or {},
        legacy_adyen_plugin_result_code=gateway_response.legacy_adyen_plugin_result_code,
        legacy_adyen_plugin_payment_method=gateway_response.legacy_adyen_plugin_payment_method,
    )
    return txn


def get_already_processed_transaction_or_create_new_transaction(
    payment: Payment,
    kind: str,
    payment_information: PaymentData,
    action_required: bool = False,
    gateway_response: GatewayResponse | None = None,
    error_msg=None,
) -> Transaction:
    if gateway_response and gateway_response.transaction_already_processed:
        txn = get_already_processed_transaction(payment, gateway_response)
        if txn:
            return txn
    return create_transaction(
        payment,
        kind=kind,
        payment_information=payment_information,
        action_required=action_required,
        gateway_response=gateway_response,
        error_msg=error_msg,
    )


def clean_capture(payment: Payment, amount: Decimal):
    """Check if payment can be captured."""
    if amount <= 0:
        raise PaymentError("Amount should be a positive number.")
    if not payment.can_capture():
        raise PaymentError("This payment cannot be captured.")
    if amount > payment.total or amount > (payment.total - payment.captured_amount):
        raise PaymentError("Unable to charge more than un-captured amount.")


def clean_authorize(payment: Payment):
    """Check if payment can be authorized."""
    if not payment.can_authorize():
        raise PaymentError("Charged transactions cannot be authorized again.")


def validate_gateway_response(response: GatewayResponse):
    """Validate response to be a correct format for Saleor to process."""
    if not isinstance(response, GatewayResponse):
        raise GatewayError("Gateway needs to return a GatewayResponse obj")

    if response.kind not in ALLOWED_GATEWAY_KINDS:
        raise GatewayError(
            f"Gateway response kind must be one of {sorted(ALLOWED_GATEWAY_KINDS)}"
        )

    try:
        json.dumps(response.raw_response, cls=DjangoJSONEncoder)
    except (TypeError, ValueError) as e:
        raise GatewayError("Gateway response needs to be json serializable") from e


@traced_atomic_transaction()
def gateway_postprocess(transaction, payment: Payment):
    changed_fields: list[str] = []

    if not transaction.is_success or transaction.already_processed:
        if changed_fields:
            # FIXME: verify that we actually want to save the payment here
            # as with empty changed_fields it won't be saved
            payment.save(update_fields=changed_fields)
        return

    if transaction.action_required:
        payment.to_confirm = True
        changed_fields.append("to_confirm")
        payment.save(update_fields=changed_fields)
        return

    # to_confirm is defined by the transaction.action_required. Payment doesn't
    # require confirmation when we got action_required == False
    if payment.to_confirm:
        payment.to_confirm = False
        changed_fields.append("to_confirm")

    update_payment_charge_status(payment, transaction, changed_fields)


def update_payment_charge_status(payment, transaction, changed_fields=None):
    changed_fields = changed_fields or []

    transaction_kind = transaction.kind
    if transaction_kind in {
        TransactionKind.CAPTURE,
        TransactionKind.REFUND_REVERSED,
    }:
        payment.captured_amount += transaction.amount
        payment.is_active = True
        # Set payment charge status to fully charged
        # only if there is no more amount needs to charge
        payment.charge_status = ChargeStatus.PARTIALLY_CHARGED
        if payment.get_charge_amount() <= 0:
            payment.charge_status = ChargeStatus.FULLY_CHARGED
        changed_fields += ["charge_status", "captured_amount", "modified_at"]

    elif transaction_kind == TransactionKind.VOID:
        payment.is_active = False
        changed_fields += ["is_active", "modified_at"]

    elif transaction_kind == TransactionKind.REFUND:
        changed_fields += ["captured_amount", "modified_at"]
        payment.captured_amount -= transaction.amount
        payment.charge_status = ChargeStatus.PARTIALLY_REFUNDED
        if payment.captured_amount <= 0:
            payment.captured_amount = Decimal("0.0")
            payment.charge_status = ChargeStatus.FULLY_REFUNDED
            payment.is_active = False
        changed_fields += ["charge_status", "is_active"]
    elif transaction_kind == TransactionKind.PENDING:
        payment.charge_status = ChargeStatus.PENDING
        changed_fields += ["charge_status"]
    elif transaction_kind == TransactionKind.CANCEL:
        payment.charge_status = ChargeStatus.CANCELLED
        payment.is_active = False
        changed_fields += ["charge_status", "is_active"]
    elif transaction_kind == TransactionKind.CAPTURE_FAILED:
        if payment.charge_status in {
            ChargeStatus.PARTIALLY_CHARGED,
            ChargeStatus.FULLY_CHARGED,
        }:
            payment.captured_amount -= transaction.amount
            payment.charge_status = ChargeStatus.PARTIALLY_CHARGED
            if payment.captured_amount <= 0:
                payment.charge_status = ChargeStatus.NOT_CHARGED
            changed_fields += ["charge_status", "captured_amount", "modified_at"]
    if changed_fields:
        payment.save(update_fields=changed_fields)
    transaction.already_processed = True
    transaction.save(update_fields=["already_processed"])
    if "captured_amount" in changed_fields and payment.order_id:
        updates_amounts_for_order(payment.order)
    if transaction_kind == TransactionKind.AUTH and payment.order_id:
        update_order_authorize_data(payment.order)


def fetch_customer_id(user: User, gateway: str):
    """Retrieve users customer_id stored for desired gateway."""
    meta_key = prepare_key_for_gateway_customer_id(gateway)
    return user.get_value_from_private_metadata(key=meta_key)


def store_customer_id(user: User, gateway: str, customer_id: str):
    """Store customer_id in users private meta for desired gateway."""
    meta_key = prepare_key_for_gateway_customer_id(gateway)
    user.store_value_in_private_metadata(items={meta_key: customer_id})
    user.save(update_fields=["private_metadata", "updated_at"])


def prepare_key_for_gateway_customer_id(gateway_name: str) -> str:
    return (gateway_name.strip().upper()) + ".customer_id"


def update_payment(payment: "Payment", gateway_response: "GatewayResponse"):
    changed_fields = []
    if psp_reference := gateway_response.psp_reference:
        payment.psp_reference = psp_reference
        changed_fields.append("psp_reference")

    if gateway_response.payment_method_info:
        update_payment_method_details(
            payment, gateway_response.payment_method_info, changed_fields
        )

    if changed_fields:
        payment.save(update_fields=changed_fields)


def update_payment_method_details(
    payment: "Payment",
    payment_method_info: Optional["PaymentMethodInfo"],
    changed_fields: list[str],
):
    if not payment_method_info:
        return
    if payment_method_info.brand:
        payment.cc_brand = payment_method_info.brand
        changed_fields.append("cc_brand")
    if payment_method_info.last_4:
        payment.cc_last_digits = payment_method_info.last_4
        changed_fields.append("cc_last_digits")
    if payment_method_info.exp_year:
        payment.cc_exp_year = payment_method_info.exp_year
        changed_fields.append("cc_exp_year")
    if payment_method_info.exp_month:
        payment.cc_exp_month = payment_method_info.exp_month
        changed_fields.append("cc_exp_month")
    if payment_method_info.type:
        payment.payment_method_type = payment_method_info.type
        changed_fields.append("payment_method_type")


def get_payment_token(payment: Payment):
    auth_transaction = payment.transactions.filter(
        kind=TransactionKind.AUTH, is_success=True
    ).first()
    if auth_transaction is None:
        raise PaymentError("Cannot process unauthorized transaction")
    return auth_transaction.token


def is_currency_supported(currency: str, gateway_id: str, manager: "PluginsManager"):
    """Return true if the given gateway supports given currency."""
    available_gateways = manager.list_payment_gateways(currency=currency)
    return any(gateway.id == gateway_id for gateway in available_gateways)


def price_from_minor_unit(value: str, currency: str):
    """Convert minor unit (smallest unit of currency) to decimal value.

    (value: 1000, currency: USD) will be converted to 10.00
    """

    value = Decimal(value)
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return value * number_places


def price_to_minor_unit(value: Decimal, currency: str):
    """Convert decimal value to the smallest unit of currency.

    Take the value, discover the precision of currency and multiply value by
    Decimal('10.0'), then change quantization to remove the comma.
    Decimal(10.0) -> str(1000)
    """
    value = quantize_price(value, currency=currency)
    precision = get_currency_precision(currency)
    number_places = Decimal("10.0") ** precision
    value_without_comma = value * number_places
    return str(value_without_comma.quantize(Decimal(1)))


def get_channel_slug_from_payment(payment: Payment) -> str | None:
    channel_slug = None

    if payment.checkout:
        channel_slug = payment.checkout.channel.slug
    elif payment.order:
        channel_slug = payment.order.channel.slug

    return channel_slug


def try_void_or_refund_inactive_payment(
    payment: Payment, transaction: Transaction, manager: "PluginsManager"
):
    """Handle refund or void inactive payments.

    In case when we have open multiple payments for single checkout but only one is
    active. Some payment methods don't required confirmation so we can receive delayed
    webhook when we have order already paid.
    """
    from .gateway import payment_refund_or_void

    if not transaction.is_success:
        return

    if not transaction.already_processed:
        update_payment_charge_status(payment, transaction)
    channel_slug = get_channel_slug_from_payment(payment)
    try:
        payment_refund_or_void(payment, manager, channel_slug=channel_slug)
    except PaymentError:
        logger.exception(
            "Unable to void/refund an inactive payment %s, %s.",
            payment.id,
            payment.psp_reference,
        )


def payment_owned_by_user(
    payment_pk: int,
    user,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> bool:
    if not user:
        return False
    return (
        Payment.objects.using(database_connection_name)
        .filter((Q(order__user=user) | Q(checkout__user=user)) & Q(pk=payment_pk))
        .first()
        is not None
    )


def get_final_session_statuses():
    return [
        TransactionEventType.AUTHORIZATION_FAILURE,
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_FAILURE,
        TransactionEventType.CHARGE_SUCCESS,
        TransactionEventType.CHARGE_REQUEST,
    ]


def get_correct_event_types_based_on_request_type(request_type: str) -> list[str]:
    type_map = {
        TransactionEventType.AUTHORIZATION_REQUEST: [
            TransactionEventType.AUTHORIZATION_FAILURE,
            TransactionEventType.AUTHORIZATION_ADJUSTMENT,
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ],
        TransactionEventType.CHARGE_REQUEST: [
            TransactionEventType.CHARGE_FAILURE,
            TransactionEventType.CHARGE_SUCCESS,
        ],
        TransactionEventType.REFUND_REQUEST: [
            TransactionEventType.REFUND_FAILURE,
            TransactionEventType.REFUND_SUCCESS,
        ],
        TransactionEventType.CANCEL_REQUEST: [
            TransactionEventType.CANCEL_FAILURE,
            TransactionEventType.CANCEL_SUCCESS,
        ],
        "session-request": [
            TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
            TransactionEventType.CHARGE_ACTION_REQUIRED,
            *get_final_session_statuses(),
        ],
    }
    return type_map.get(request_type, [])


ErrorMsg = str


def parse_transaction_action_data_for_action_webhook(
    response_data: Any,
    request_type: str,
    request_event_amount: Decimal,
) -> tuple[Optional["TransactionRequestResponse"], ErrorMsg | None]:
    """Parse response from transaction action webhook.

    It takes the recieved response from sync webhook and
    returns TransactionRequestResponse with all details.
    If unable to parse, None will be returned.
    """
    if request_type not in [
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.REFUND_REQUEST,
        TransactionEventType.CANCEL_REQUEST,
    ]:
        logger.error(
            "Request type %s not supported for parsing transaction action data.",
            request_type,
            extra={"request_type": request_type},
        )
        return None, "Request type not supported"

    try:
        response_data_model = _validate_transaction_action_data(
            response_data,
            request_type,
        )
    except ValidationError as error:
        error_msg_response = parse_validation_error(error)
        logger.warning(error_msg_response)
        return None, truncate_transaction_event_message(error_msg_response)
    except ValueError as error:
        error_msg_response = str(error)
        logger.warning(
            "Error while parsing transaction action data: %s",
            error_msg_response,
            extra={"request_type": request_type},
        )
        return None, truncate_transaction_event_message(error_msg_response)

    event = None
    if isinstance(response_data_model, transaction_schemas.TransactionBaseSchema):
        event = TransactionRequestEventResponse(
            psp_reference=response_data_model.psp_reference,
            type=response_data_model.result,
            amount=response_data_model.amount or request_event_amount,
            time=response_data_model.time,
            external_url=str(response_data_model.external_url),
            message=response_data_model.message,
        )
    return (
        TransactionRequestResponse(
            psp_reference=response_data_model.psp_reference,
            available_actions=response_data_model.actions,
            event=event,
        ),
        None,
    )


def parse_transaction_action_data_for_session_webhook(
    response_data: Any,
    request_event_amount: Decimal,
) -> tuple[Optional["TransactionSessionResponse"], ErrorMsg | None]:
    """Parse response from transaction session webhook.

    It takes the recieved response from sync webhook and
    returns TransactionRequestResponse with all details.
    If unable to parse, None will be returned.
    """
    try:
        response_data_model = _validate_transaction_session_action_data(
            response_data,
        )
    except ValidationError as error:
        error_msg_response = parse_validation_error(error)
        logger.warning(error_msg_response)
        return None, truncate_transaction_event_message(error_msg_response)
    except ValueError as error:
        error_msg_response = str(error)
        logger.warning(
            "Error while parsing transaction action data: %s",
            error_msg_response,
            extra={"request_type": SESSION_REQUEST_EVENT_TYPE},
        )
        return None, truncate_transaction_event_message(error_msg_response)

    event = TransactionRequestEventResponse(
        psp_reference=response_data_model.psp_reference,
        type=response_data_model.result,
        amount=response_data_model.amount or request_event_amount,
        time=response_data_model.time,
        external_url=str(response_data_model.external_url),
        message=response_data_model.message,
    )

    payment_method_details = None
    if parsed_payment_method_details := response_data_model.payment_method_details:
        payment_method_details = PaymentMethodDetails(
            type=parsed_payment_method_details.type,
            name=parsed_payment_method_details.name,
        )
        if isinstance(
            parsed_payment_method_details,
            transaction_schemas.CardPaymentMethodDetails,
        ):
            payment_method_details.brand = parsed_payment_method_details.brand
            payment_method_details.first_digits = (
                parsed_payment_method_details.first_digits
            )
            payment_method_details.last_digits = (
                parsed_payment_method_details.last_digits
            )
            payment_method_details.exp_month = parsed_payment_method_details.exp_month
            payment_method_details.exp_year = parsed_payment_method_details.exp_year

    return (
        TransactionSessionResponse(
            psp_reference=response_data_model.psp_reference,
            available_actions=response_data_model.actions,
            payment_method_details=payment_method_details,
            event=event,
        ),
        None,
    )


def _validate_transaction_action_data(
    response_data: Any,
    request_type: str,
) -> (
    transaction_schemas.TransactionBaseSchema
    | transaction_schemas.TransactionAsyncSchema
):
    request_type_to_schemas_map: dict[str, tuple] = {
        TransactionEventType.CHARGE_REQUEST: (
            transaction_schemas.TransactionChargeRequestedSyncSuccessSchema,
            transaction_schemas.TransactionChargeRequestedSyncFailureSchema,
            transaction_schemas.TransactionChargeRequestedAsyncSchema,
        ),
        TransactionEventType.REFUND_REQUEST: (
            transaction_schemas.TransactionRefundRequestedSyncSuccessSchema,
            transaction_schemas.TransactionRefundRequestedSyncFailureSchema,
            transaction_schemas.TransactionRefundRequestedAsyncSchema,
        ),
        TransactionEventType.CANCEL_REQUEST: (
            transaction_schemas.TransactionCancelationRequestedSyncSuccessSchema,
            transaction_schemas.TransactionCancelationRequestedSyncFailureSchema,
            transaction_schemas.TransactionCancelationRequestedAsyncSchema,
        ),
    }
    success_schema, failure_schema, async_schema = request_type_to_schemas_map[
        request_type
    ]
    result_value = response_data.get("result")
    if result_value in get_args(success_schema.model_fields["result"].annotation):
        return success_schema.model_validate(response_data)
    if result_value in get_args(failure_schema.model_fields["result"].annotation):
        return failure_schema.model_validate(response_data)
    if result_value is None:
        return async_schema.model_validate(response_data)
    possible_values = ", ".join(
        list(get_args(success_schema.model_fields["result"].annotation))
        + list(get_args(failure_schema.model_fields["result"].annotation))
    )
    logger.warning(
        "Invalid value for `result`: %s. Possible values: %s.",
        result_value,
        possible_values,
    )
    raise ValueError(
        f"Missing or invalid value for `result`: {result_value}. Possible values: {possible_values}."
    )


def _validate_transaction_session_action_data(
    response_data: Any,
) -> transaction_schemas.TransactionSessionBaseSchema:
    success_schema = transaction_schemas.TransactionSessionSuccessSchema
    failure_schema = transaction_schemas.TransactionSessionFailureSchema
    action_required_schema = transaction_schemas.TransactionSessionActionRequiredSchema

    result_value = response_data.get("result")
    if result_value in get_args(success_schema.model_fields["result"].annotation):
        return success_schema.model_validate(response_data)
    if result_value in get_args(failure_schema.model_fields["result"].annotation):
        return failure_schema.model_validate(response_data)
    if result_value in get_args(
        action_required_schema.model_fields["result"].annotation
    ):
        return action_required_schema.model_validate(response_data)
    possible_values = ", ".join(
        [
            value.name
            for value in transaction_schemas.TransactionEventTypeEnum.__members__.values()
        ]
    )
    logger.warning(
        "Invalid value for `result`: %s. Possible values: %s.",
        result_value,
        possible_values,
    )
    raise ValueError(
        f"Missing or invalid value for `result`: {result_value}. Possible values: {possible_values}."
    )


def parse_available_actions(available_actions):
    if available_actions is not None:
        possible_actions = {
            str_to_enum(event_action): event_action
            for event_action, _ in TransactionAction.CHOICES
        }
        available_actions = [
            possible_actions[action]
            for action in available_actions
            if action in possible_actions
        ]
    return available_actions


def truncate_transaction_event_message(message: str):
    return truncatechars(message, TRANSACTION_EVENT_MSG_MAX_LENGTH)


def get_failed_transaction_event_type_for_request_event(
    request_event: TransactionEvent,
):
    if request_event.type == TransactionEventType.AUTHORIZATION_REQUEST:
        return TransactionEventType.AUTHORIZATION_FAILURE
    if request_event.type == TransactionEventType.CHARGE_REQUEST:
        return TransactionEventType.CHARGE_FAILURE
    if request_event.type == TransactionEventType.REFUND_REQUEST:
        return TransactionEventType.REFUND_FAILURE
    if request_event.type == TransactionEventType.CANCEL_REQUEST:
        return TransactionEventType.CANCEL_FAILURE
    return None


def get_failed_type_based_on_event(event: TransactionEvent):
    event_type = get_failed_transaction_event_type_for_request_event(event)
    if event_type:
        return event_type
    if event.type in [
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.AUTHORIZATION_ADJUSTMENT,
    ]:
        return TransactionEventType.AUTHORIZATION_FAILURE
    if event.type in [
        TransactionEventType.CHARGE_BACK,
        TransactionEventType.CHARGE_SUCCESS,
    ]:
        return TransactionEventType.CHARGE_FAILURE
    if event.type in [
        TransactionEventType.REFUND_REVERSE,
        TransactionEventType.REFUND_SUCCESS,
    ]:
        return TransactionEventType.REFUND_FAILURE
    if event.type == TransactionEventType.CANCEL_SUCCESS:
        return TransactionEventType.CANCEL_FAILURE
    return event.type


@allow_writer()
def create_failed_transaction_event(
    event: TransactionEvent,
    cause: str,
):
    return TransactionEvent.objects.create(
        type=get_failed_type_based_on_event(event),
        amount_value=event.amount_value,
        currency=event.currency,
        transaction_id=event.transaction_id,
        message=cause,
        include_in_calculations=False,
        psp_reference=event.psp_reference,
        related_granted_refund_id=event.related_granted_refund_id,
    )


def authorization_success_already_exists(transaction_id: int) -> bool:
    return TransactionEvent.objects.filter(
        transaction_id=transaction_id,
        type=TransactionEventType.AUTHORIZATION_SUCCESS,
    ).exists()


def get_already_existing_event(event: TransactionEvent) -> TransactionEvent | None:
    if event.type in [
        TransactionEventType.AUTHORIZATION_ACTION_REQUIRED,
        TransactionEventType.CHARGE_ACTION_REQUIRED,
        TransactionEventType.INFO,
    ]:
        # We don't need to take into account the events that are only a record of
        # additional action required from the payment app.
        return None
    existing_event = (
        TransactionEvent.objects.filter(
            transaction_id=event.transaction_id,
            psp_reference=event.psp_reference,
            type=event.type,
        )
        .select_for_update(of=("self",))
        .first()
    )
    if existing_event:
        return existing_event
    return None


def deduplicate_event(
    event: TransactionEvent, app: App
) -> tuple[TransactionEvent, ErrorMsg | None]:
    """Deduplicate the TransactionEvent.

    In case of having an existing event with the same type, psp reference
    and amount, the event will be treated as a duplicate.
    In case of a mismatch between the amounts, the failure TransactionEvent
    will be created.
    In case of already having `AUTHORIZATION_SUCCESS` event and trying to
    create a new one, the failure TransactionEvent will be created.
    """
    error_message = None

    already_existing_event = get_already_existing_event(event)
    if already_existing_event:
        if already_existing_event.amount != event.amount:
            error_message = (
                "The transaction with provided `pspReference` and "
                "`type` already exists with different amount."
            )
        event = already_existing_event

    elif event.type == TransactionEventType.AUTHORIZATION_SUCCESS:
        already_existing_authorization = authorization_success_already_exists(
            event.transaction_id
        )
        if already_existing_authorization:
            error_message = (
                "Event with `AUTHORIZATION_SUCCESS` already "
                "reported for the transaction. Use "
                "`AUTHORIZATION_ADJUSTMENT` to change the "
                "authorization amount."
            )
    if error_message:
        logger.warning(
            msg=error_message,
            extra={
                "transaction_id": event.transaction_id,
                "psp_reference": event.psp_reference,
                "app_identifier": app.identifier,
                "app_id": app.pk,
            },
        )
    return event, error_message


def _create_event_from_response(
    response: TransactionRequestEventResponse,
    app: App,
    transaction_id: int,
    currency: str,
    related_granted_refund_id: int | None = None,
) -> tuple[TransactionEvent | None, ErrorMsg | None]:
    app_identifier = None
    if app and app.identifier:
        app_identifier = app.identifier
    event = TransactionEvent(
        psp_reference=response.psp_reference,
        created_at=response.time or timezone.now(),
        type=response.type,
        amount_value=response.amount,
        external_url=response.external_url,
        currency=currency,
        transaction_id=transaction_id,
        message=response.message,
        app_identifier=app_identifier,
        app=app,
        include_in_calculations=True,
        related_granted_refund_id=related_granted_refund_id,
    )
    with transaction.atomic():
        _transaction = (
            TransactionItem.objects.filter(pk=transaction_id)
            .select_for_update(of=("self",))
            .first()
        )
        event, error_msg = deduplicate_event(event, app)
        if error_msg:
            return None, error_msg
        if not event.pk:
            event.save()
    return event, None


def _get_parsed_transaction_data_for_session_webhook(
    transaction_webhook_response: dict[str, Any] | None,
    request_event_amount: Decimal,
) -> tuple[Optional["TransactionSessionResponse"], ErrorMsg | None]:
    if transaction_webhook_response is None:
        return None, "Failed to delivery request."

    transaction_request_response, error_msg = (
        parse_transaction_action_data_for_session_webhook(
            transaction_webhook_response,
            request_event_amount=request_event_amount,
        )
    )
    if not transaction_request_response:
        return None, error_msg or ""
    return transaction_request_response, None


def _get_parsed_transaction_data_for_action_webhook(
    transaction_webhook_response: dict[str, Any] | None,
    event_type: str,
    request_event_amount: Decimal,
) -> tuple[Optional["TransactionRequestResponse"], ErrorMsg | None]:
    if transaction_webhook_response is None:
        return None, "Failed to delivery request."

    transaction_request_response, error_msg = (
        parse_transaction_action_data_for_action_webhook(
            transaction_webhook_response,
            event_type,
            request_event_amount=request_event_amount,
        )
    )
    if not transaction_request_response:
        return None, error_msg or ""
    return transaction_request_response, None


def update_order_with_transaction_details(transaction: TransactionItem):
    if transaction.order_id:
        order = cast(Order, transaction.order)
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


def update_transaction_item_with_payment_method_details(
    transaction_item: TransactionItem,
    payment_method_details: PaymentMethodDetails,
) -> list[str]:
    """Assign the payment method details to the transaction item.

    Returns the list of updated fields.
    """
    updated_fields = []
    if payment_method_details.type != transaction_item.payment_method_type:
        transaction_item.payment_method_type = payment_method_details.type
        updated_fields.append("payment_method_type")
    if payment_method_details.name != transaction_item.payment_method_name:
        transaction_item.payment_method_name = payment_method_details.name
        updated_fields.append("payment_method_name")
    if payment_method_details.brand != transaction_item.cc_brand:
        transaction_item.cc_brand = payment_method_details.brand
        updated_fields.append("cc_brand")
    if payment_method_details.first_digits != transaction_item.cc_first_digits:
        transaction_item.cc_first_digits = payment_method_details.first_digits
        updated_fields.append("cc_first_digits")
    if payment_method_details.last_digits != transaction_item.cc_last_digits:
        transaction_item.cc_last_digits = payment_method_details.last_digits
        updated_fields.append("cc_last_digits")
    if payment_method_details.exp_month != transaction_item.cc_exp_month:
        transaction_item.cc_exp_month = payment_method_details.exp_month
        updated_fields.append("cc_exp_month")
    if payment_method_details.exp_year != transaction_item.cc_exp_year:
        transaction_item.cc_exp_year = payment_method_details.exp_year
        updated_fields.append("cc_exp_year")
    return updated_fields


def process_order_with_transaction(
    transaction: TransactionItem,
    manager: "PluginsManager",
    user: Optional["User"],
    app: Optional["App"],
    previous_authorized_value: Decimal = Decimal(0),
    previous_charged_value: Decimal = Decimal(0),
    previous_refunded_value: Decimal = Decimal(0),
    related_granted_refund: OrderGrantedRefund | None = None,
):
    order = None
    # This is executed after we ensure that the transaction is not a checkout
    # transaction, so we can safely cast the order_id to UUID.
    order_id = cast(UUID, transaction.order_id)
    with traced_atomic_transaction():
        order, transaction = get_order_and_transaction_item_locked_for_update(
            order_id, transaction.pk
        )
        update_fields = []
        updates_amounts_for_order(order, save=False)
        update_fields.extend(
            [
                "total_charged_amount",
                "charge_status",
                "total_authorized_amount",
                "authorize_status",
            ]
        )
        if (
            order.channel.automatically_confirm_all_new_orders
            and order.status == OrderStatus.UNCONFIRMED
        ):
            status_updated = refresh_order_status(order)
            if status_updated:
                update_fields.append("status")
        if update_fields:
            update_fields.append("updated_at")
            order.save(update_fields=update_fields)

    update_order_search_vector(order)
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
    if related_granted_refund:
        calculate_order_granted_refund_status(related_granted_refund)


def process_order_or_checkout_with_transaction(
    transaction: TransactionItem,
    manager: "PluginsManager",
    user: Optional["User"],
    app: Optional["App"],
    previous_authorized_value: Decimal = Decimal(0),
    previous_charged_value: Decimal = Decimal(0),
    previous_refunded_value: Decimal = Decimal(0),
    related_granted_refund: OrderGrantedRefund | None = None,
):
    checkout_deleted = False
    if transaction.checkout_id:
        with traced_atomic_transaction():
            locked_checkout, transaction = (
                get_checkout_and_transaction_item_locked_for_update(
                    transaction.checkout_id, transaction.pk
                )
            )
            if transaction.checkout_id and locked_checkout:
                transaction_amounts_for_checkout_updated_without_price_recalculation(
                    transaction, locked_checkout, manager, user, app
                )
            else:
                checkout_deleted = True
                # If the checkout was deleted, we still want to update the order associated with the transaction.

    if transaction.order_id or checkout_deleted:
        process_order_with_transaction(
            transaction,
            manager,
            user,
            app,
            previous_authorized_value,
            previous_charged_value,
            previous_refunded_value,
            related_granted_refund=related_granted_refund,
        )


def create_transaction_event_for_transaction_session(
    request_event: TransactionEvent,
    app: App,
    manager: "PluginsManager",
    transaction_webhook_response: dict[str, Any] | None = None,
):
    transaction_request_response, error_msg = (
        _get_parsed_transaction_data_for_session_webhook(
            transaction_webhook_response=transaction_webhook_response,
            request_event_amount=request_event.amount_value,
        )
    )
    if not transaction_request_response or not transaction_request_response.event:
        return create_failed_transaction_event(request_event, cause=error_msg or "")

    event = None
    request_event_update_fields = []
    response_event = transaction_request_response.event
    if response_event.type in [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.CHARGE_REQUEST,
    ]:
        request_event.type = response_event.type
        request_event.amount_value = response_event.amount
        request_event.psp_reference = response_event.psp_reference
        request_event.include_in_calculations = True
        if response_event.time:
            request_event.created_at = response_event.time
        request_event.app = app
        request_event.message = response_event.message
        if response_event.external_url:
            request_event.external_url = response_event.external_url
        request_event_update_fields.extend(
            [
                "type",
                "amount_value",
                "psp_reference",
                "include_in_calculations",
                "app",
                "message",
                "created_at",
                "external_url",
            ]
        )
        event = request_event
    else:
        event, error_message = _create_event_from_response(
            response_event,
            app=app,
            transaction_id=request_event.transaction_id,
            currency=request_event.currency,
        )
        if not event:
            return create_failed_transaction_event(
                request_event, cause=error_message or ""
            )
        request_event.psp_reference = event.psp_reference
        request_event_update_fields.append("psp_reference")
    if request_event_update_fields:
        request_event.save(update_fields=request_event_update_fields)

    transaction_item = event.transaction
    transaction_item_updated_fields = []
    if transaction_request_response.payment_method_details:
        transaction_item_updated_fields.extend(
            update_transaction_item_with_payment_method_details(
                transaction_item, transaction_request_response.payment_method_details
            )
        )

    if event.type in [
        TransactionEventType.AUTHORIZATION_REQUEST,
        TransactionEventType.AUTHORIZATION_SUCCESS,
        TransactionEventType.CHARGE_REQUEST,
        TransactionEventType.CHARGE_SUCCESS,
    ]:
        previous_authorized_value = transaction_item.authorized_value
        previous_charged_value = transaction_item.charged_value
        previous_refunded_value = transaction_item.refunded_value

        transaction_item.psp_reference = event.psp_reference
        available_actions = transaction_request_response.available_actions
        if available_actions is not None:
            transaction_item.available_actions = list(set(available_actions))

        recalculate_transaction_amounts(transaction_item, save=False)
        transaction_item.save(
            update_fields=[
                "authorized_value",
                "charged_value",
                "refunded_value",
                "canceled_value",
                "authorize_pending_value",
                "charge_pending_value",
                "refund_pending_value",
                "cancel_pending_value",
                "psp_reference",
                "available_actions",
                "modified_at",
            ]
            + transaction_item_updated_fields
        )

        process_order_or_checkout_with_transaction(
            transaction_item,
            manager,
            None,
            app,
            previous_authorized_value=previous_authorized_value,
            previous_charged_value=previous_charged_value,
            previous_refunded_value=previous_refunded_value,
        )

    elif event.psp_reference and transaction_item.psp_reference != event.psp_reference:
        transaction_item.psp_reference = event.psp_reference
        transaction_item.save(
            update_fields=["psp_reference", "modified_at"]
            + transaction_item_updated_fields
        )
        if transaction_item.checkout_id:
            checkout = cast(Checkout, transaction_item.checkout)
            update_last_transaction_modified_at_for_checkout(checkout, transaction_item)
    elif transaction_item_updated_fields:
        transaction_item.save(update_fields=transaction_item_updated_fields)

    return event


def update_order_granted_status_if_needed(request_event: TransactionEvent):
    if request_event.related_granted_refund_id:
        granted_refund = cast(OrderGrantedRefund, request_event.related_granted_refund)
        calculate_order_granted_refund_status(granted_refund)


def create_transaction_event_from_request_and_webhook_response(
    request_event: TransactionEvent,
    app: App,
    transaction_webhook_response: dict[str, Any] | None = None,
):
    transaction_request_response, error_msg = (
        _get_parsed_transaction_data_for_action_webhook(
            transaction_webhook_response=transaction_webhook_response,
            event_type=request_event.type,
            request_event_amount=request_event.amount_value,
        )
    )
    transaction_item = request_event.transaction
    if not transaction_request_response:
        recalculate_refundable_for_checkout(transaction_item, request_event)
        failure_event = create_failed_transaction_event(
            request_event, cause=error_msg or ""
        )
        update_order_granted_status_if_needed(request_event)
        return failure_event

    psp_reference = transaction_request_response.psp_reference
    if psp_reference is not None:
        request_event.psp_reference = psp_reference
        request_event.include_in_calculations = True
        request_event.save(update_fields=["psp_reference", "include_in_calculations"])
    event = None
    if response_event := transaction_request_response.event:
        event, error_msg = _create_event_from_response(
            response_event,
            app=app,
            transaction_id=request_event.transaction_id,
            currency=request_event.currency,
            related_granted_refund_id=request_event.related_granted_refund_id,
        )
        if error_msg:
            recalculate_refundable_for_checkout(transaction_item, request_event)
            failure_event = create_failed_transaction_event(
                request_event, cause=error_msg
            )
            update_order_granted_status_if_needed(request_event)
            return failure_event

    transaction_item = request_event.transaction
    previous_authorized_value = transaction_item.authorized_value
    previous_charged_value = transaction_item.charged_value
    previous_refunded_value = transaction_item.refunded_value
    recalculate_transaction_amounts(transaction_item, save=False)
    available_actions = transaction_request_response.available_actions
    if available_actions is not None:
        transaction_item.available_actions = list(set(available_actions))

    transaction_item.save(
        update_fields=[
            "available_actions",
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
    )

    if transaction_item.order_id:
        # circular import
        from ..order.actions import order_transaction_updated

        manager = get_plugins_manager(allow_replica=False)
        order = cast(Order, transaction_item.order)
        order_info = fetch_order_info(order)
        update_order_with_transaction_details(transaction_item)
        order_transaction_updated(
            order_info=order_info,
            transaction_item=transaction_item,
            manager=manager,
            user=None,
            app=app,
            previous_authorized_value=previous_authorized_value,
            previous_charged_value=previous_charged_value,
            previous_refunded_value=previous_refunded_value,
        )
        if request_event.related_granted_refund_id:
            granted_refund = cast(
                OrderGrantedRefund, request_event.related_granted_refund
            )
            calculate_order_granted_refund_status(granted_refund)

    elif transaction_item.checkout_id:
        manager = get_plugins_manager(allow_replica=True)
        recalculate_refundable_for_checkout(transaction_item, request_event, event)
        transaction_amounts_for_checkout_updated(
            transaction_item, manager, app=app, user=None
        )
    return event


def _prepare_manual_event(
    transaction: TransactionItem,
    transaction_amount: Decimal,
    input_amount: Decimal,
    event_type: str,
    user: Optional["User"],
    app: Optional["App"],
) -> TransactionEvent:
    amount_to_update = input_amount - transaction_amount
    return TransactionEvent(
        type=event_type,
        amount_value=amount_to_update,
        currency=transaction.currency,
        transaction_id=transaction.pk,
        include_in_calculations=True,
        app_identifier=app.identifier if app else None,
        app=app,
        user=user,
        created_at=timezone.now(),
        message="Manual adjustment of the transaction.",
    )


def prepare_manual_event(
    events_to_create: list[TransactionEvent],
    amount_field: str,
    money_data: dict[str, Decimal],
    event_type: str,
    transaction: TransactionItem,
    user: Optional["User"],
    app: Optional["App"],
):
    amount_value = money_data.get(amount_field)
    if amount_value is None:
        return
    transaction_amount = getattr(transaction, amount_field)
    if transaction_amount != amount_value:
        events_to_create.append(
            _prepare_manual_event(
                transaction,
                transaction_amount,
                amount_value,
                event_type,
                user,
                app,
            )
        )


def create_manual_adjustment_events(
    transaction: TransactionItem,
    money_data: dict[str, Decimal],
    user: Optional["User"],
    app: Optional["App"],
) -> list[TransactionEvent]:
    """Create TransactionEvent used to recalculate the transaction amounts.

    The transaction amounts are calculated based on the amounts stored in
    the TransactionEvents assigned to the given transaction. To properly
    match the amounts, the manual events are created in case of calling
    transactionCreate or transactionUpdate
    """
    events_to_create: list[TransactionEvent] = []
    if "authorized_value" in money_data:
        authorized_value = money_data["authorized_value"]
        event_type = TransactionEventType.AUTHORIZATION_SUCCESS
        current_authorized_value = transaction.authorized_value
        if transaction.events.filter(type=event_type).exists():
            event_type = TransactionEventType.AUTHORIZATION_ADJUSTMENT
            # adjust overwrite the amount of authorization so we need to set
            # current auth value to 0, to match calculations
            current_authorized_value = Decimal(0)
        if transaction.authorized_value != authorized_value:
            events_to_create.append(
                _prepare_manual_event(
                    transaction,
                    current_authorized_value,
                    authorized_value,
                    event_type,
                    user,
                    app,
                )
            )
    prepare_manual_event(
        events_to_create=events_to_create,
        amount_field="charged_value",
        money_data=money_data,
        event_type=TransactionEventType.CHARGE_SUCCESS,
        transaction=transaction,
        app=app,
        user=user,
    )
    prepare_manual_event(
        events_to_create=events_to_create,
        amount_field="refunded_value",
        money_data=money_data,
        event_type=TransactionEventType.REFUND_SUCCESS,
        transaction=transaction,
        app=app,
        user=user,
    )
    prepare_manual_event(
        events_to_create=events_to_create,
        amount_field="canceled_value",
        money_data=money_data,
        event_type=TransactionEventType.CANCEL_SUCCESS,
        transaction=transaction,
        app=app,
        user=user,
    )
    if events_to_create:
        with allow_writer():
            return TransactionEvent.objects.bulk_create(events_to_create)
    return []


def get_transaction_item_params(
    source_object: Checkout | Order,
    user: User | None,
    app: App | None,
    psp_reference: str | None,
    available_actions: list[str] | None = None,
    name: str = "",
):
    return {
        "name": name,
        "checkout_id": (
            source_object.pk if isinstance(source_object, Checkout) else None
        ),
        "order_id": source_object.pk if isinstance(source_object, Order) else None,
        "currency": source_object.currency,
        "app": app,
        "app_identifier": app.identifier if app else None,
        "user": user,
        "psp_reference": psp_reference,
        "available_actions": available_actions if available_actions else [],
    }


@allow_writer()
def create_transaction_for_order(
    order: "Order",
    user: Optional["User"],
    app: Optional["App"],
    psp_reference: str | None,
    charged_value: Decimal,
    available_actions: list[str] | None = None,
    name: str = "",
) -> TransactionItem:
    transaction_defaults = get_transaction_item_params(
        source_object=order,
        user=user,
        app=app,
        psp_reference=psp_reference,
        available_actions=available_actions,
        name=name,
    )
    transaction_item = TransactionItem.objects.create(**transaction_defaults)
    create_manual_adjustment_events(
        transaction=transaction_item,
        money_data={"charged_value": charged_value},
        user=user,
        app=app,
    )
    recalculate_transaction_amounts(transaction=transaction_item)
    return transaction_item


@allow_writer()
def handle_transaction_initialize_session(
    source_object: Checkout | Order,
    payment_gateway_data: PaymentGatewayData,
    amount: Decimal,
    action: str,
    customer_ip_address: str | None,
    app: App,
    manager: PluginsManager,
    idempotency_key: str,
):
    transaction_item_defaults = get_transaction_item_params(
        source_object=source_object, user=None, app=app, psp_reference=None
    )

    try:
        transaction_item, _ = TransactionItem.objects.get_or_create(
            idempotency_key=idempotency_key,
            order_id=transaction_item_defaults["order_id"],
            checkout_id=transaction_item_defaults["checkout_id"],
            defaults=transaction_item_defaults,
        )

        if action == TransactionFlowStrategy.CHARGE:
            event_type = TransactionEventType.CHARGE_REQUEST
        else:
            event_type = TransactionEventType.AUTHORIZATION_REQUEST

        request_event, _ = TransactionEvent.objects.get_or_create(
            idempotency_key=idempotency_key,
            transaction=transaction_item,
            type=event_type,
            currency=transaction_item.currency,
            amount_value=amount,
            defaults={
                "include_in_calculations": False,
                "type": (
                    TransactionEventType.CHARGE_REQUEST
                    if action == TransactionFlowStrategy.CHARGE
                    else TransactionEventType.AUTHORIZATION_REQUEST
                ),
                "currency": transaction_item.currency,
                "amount_value": amount,
                "idempotency_key": idempotency_key,
            },
        )
    except IntegrityError as e:
        raise TransactionItemIdempotencyUniqueError() from e

    session_data = TransactionSessionData(
        transaction=transaction_item,
        source_object=source_object,
        payment_gateway_data=payment_gateway_data,
        action=TransactionProcessActionData(
            action_type=action, currency=source_object.currency, amount=amount
        ),
        customer_ip_address=customer_ip_address,
        idempotency_key=idempotency_key,
    )

    result = manager.transaction_initialize_session(session_data)

    response_data = result.response if result else None

    created_event = create_transaction_event_for_transaction_session(
        request_event,
        app,
        transaction_webhook_response=response_data,
        manager=manager,
    )
    data_to_return = response_data.get("data") if response_data else None
    return created_event.transaction, created_event, data_to_return


def handle_transaction_process_session(
    transaction_item: TransactionItem,
    source_object: Checkout | Order,
    payment_gateway_data: PaymentGatewayData,
    action: str,
    app: App,
    customer_ip_address: str | None,
    manager: PluginsManager,
    request_event: TransactionEvent,
):
    session_data = TransactionSessionData(
        transaction=transaction_item,
        source_object=source_object,
        payment_gateway_data=payment_gateway_data,
        action=TransactionProcessActionData(
            action_type=action,
            currency=source_object.currency,
            amount=request_event.amount_value,
        ),
        customer_ip_address=customer_ip_address,
    )

    result = manager.transaction_process_session(session_data)

    response_data = result.response if result else None

    created_event = create_transaction_event_for_transaction_session(
        request_event,
        app,
        transaction_webhook_response=response_data,
        manager=manager,
    )
    data_to_return = response_data.get("data") if response_data else None
    return created_event, data_to_return


def get_transaction_event_amount(event_type: str, psp_reference: str):
    """Deduce the transaction event amount if possible.

    - In case of missing amount for event INFO, use 0
    - In case of missing amount for *_FAILURE the amount is taken from *_SUCCESS or
    *_REQUEST event with the same pspReference.
    - In case of REFUND_REVERSE, the amount is taken from REFUND_SUCCESS with the same
    pspReference.
    - In case of CHARGEBACK the amount is taken from CHARGE_SUCCESS with the same
    pspReference.
    - If the specific event for the pspReference doesn't exist, the exception is raised.
    """
    if event_type == TransactionEventType.INFO:
        return Decimal(0)

    event_type_map = {
        TransactionEventType.CHARGE_FAILURE: [
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_FAILURE,
        ],
        TransactionEventType.REFUND_FAILURE: [
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.CHARGE_FAILURE,
        ],
        TransactionEventType.CANCEL_FAILURE: [
            TransactionEventType.CANCEL_SUCCESS,
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_FAILURE,
        ],
        TransactionEventType.AUTHORIZATION_FAILURE: [
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_REQUEST,
        ],
        TransactionEventType.REFUND_REVERSE: [TransactionEventType.REFUND_SUCCESS],
        TransactionEventType.CHARGE_BACK: [TransactionEventType.CHARGE_SUCCESS],
    }
    allowed_event_types = event_type_map.get(event_type, [])
    matched_event = (
        TransactionEvent.objects.filter(
            psp_reference=psp_reference, type__in=allowed_event_types
        )
        .order_by("-created_at")
        .first()
    )
    if matched_event is None:
        raise ValueError(f"Unable to deduce the amount for {event_type} event.")
    return matched_event.amount_value
