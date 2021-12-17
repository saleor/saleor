import json
import logging
from collections import defaultdict
from decimal import Decimal
from itertools import chain
from typing import Any, Dict, Iterator, List, Optional, Tuple

import graphene
from babel.numbers import get_currency_precision
from django.core.serializers.json import DjangoJSONEncoder

from ..account.models import User
from ..checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ..checkout.models import Checkout
from ..core.prices import quantize_price
from ..core.tracing import traced_atomic_transaction
from ..discount.utils import fetch_active_discounts
from ..order import FulfillmentLineData, FulfillmentStatus, OrderLineData
from ..order.models import FulfillmentLine, Order, OrderLine
from ..plugins.manager import PluginsManager, get_plugins_manager
from . import ChargeStatus, GatewayError, PaymentError, TransactionKind
from .error_codes import PaymentErrorCode
from .interface import (
    AddressData,
    GatewayResponse,
    PaymentData,
    PaymentLineData,
    PaymentMethodInfo,
)
from .models import Payment, Transaction

logger = logging.getLogger(__name__)

GENERIC_TRANSACTION_ERROR = "Transaction was unsuccessful"
ALLOWED_GATEWAY_KINDS = {choices[0] for choices in TransactionKind.CHOICES}


def create_payment_lines_information(
    payment: Payment,
    manager: PluginsManager,
) -> List[PaymentLineData]:
    checkout = payment.checkout
    order = payment.order

    if checkout:
        return create_checkout_payment_lines_information(checkout, manager)
    elif order:
        return create_order_payment_lines_information(order)

    return []


def create_checkout_payment_lines_information(
    checkout: Checkout, manager: PluginsManager
) -> List[PaymentLineData]:
    line_items = []
    lines = fetch_checkout_lines(checkout)
    discounts = fetch_active_discounts()
    checkout_info = fetch_checkout_info(checkout, lines, discounts, manager)
    address = checkout_info.shipping_address or checkout_info.billing_address

    for line_info in lines:
        unit_price = manager.calculate_checkout_line_unit_price(
            checkout_info,
            lines,
            line_info,
            address,
            discounts,
        ).price_with_sale
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
                gross=unit_gross,
            )
        )
    shipping_amount = manager.calculate_checkout_shipping(
        checkout_info=checkout_info,
        lines=lines,
        address=address,
        discounts=discounts,
    ).gross.amount

    line_items.append(create_shipping_payment_line_data(amount=shipping_amount))

    voucher_line_item = create_checkout_voucher_payment_line_data(checkout)
    if voucher_line_item:
        line_items.append(voucher_line_item)

    return line_items


def create_order_payment_lines_information(order: Order) -> List[PaymentLineData]:
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
                gross=order_line.unit_price_gross_amount,
            )
        )

    line_items.append(
        create_shipping_payment_line_data(amount=order.shipping_price_gross_amount)
    )

    voucher_line_item = create_order_voucher_payment_line_data(order)
    if voucher_line_item:
        line_items.append(voucher_line_item)

    return line_items


# Values are outside of model's pk range to resolve
# any collision with actual product variant pk
VOUCHER_PAYMENT_LINE_ID = 0
SHIPPING_PAYMENT_LINE_ID = -1


def create_shipping_payment_line_data(amount: Decimal) -> PaymentLineData:
    return PaymentLineData(
        quantity=1,
        product_name="Shipping",
        product_sku="Shipping",
        variant_id=SHIPPING_PAYMENT_LINE_ID,
        gross=amount,
    )


def create_checkout_voucher_payment_line_data(
    checkout: Checkout,
) -> Optional[PaymentLineData]:
    discount_amount = -checkout.discount_amount
    return create_voucher_payment_line_data(discount_amount)


def create_order_voucher_payment_line_data(
    order: Order,
) -> Optional[PaymentLineData]:
    discount_amount = order.total_gross_amount - order.undiscounted_total_gross_amount
    return create_voucher_payment_line_data(discount_amount)


def create_voucher_payment_line_data(amount: Decimal) -> Optional[PaymentLineData]:
    if not amount:
        return None
    return PaymentLineData(
        quantity=1,
        product_name="Voucher",
        product_sku="Voucher",
        variant_id=VOUCHER_PAYMENT_LINE_ID,
        gross=amount,
    )


def create_payment_information(
    payment: Payment,
    payment_token: str = None,
    amount: Decimal = None,
    customer_id: str = None,
    store_source: bool = False,
    refund_data: Optional[Dict[int, int]] = None,
    additional_data: Optional[dict] = None,
    manager: Optional[PluginsManager] = None,
) -> PaymentData:
    """Extract order information along with payment details.

    Returns information required to process payment and additional
    billing/shipping addresses for optional fraud-prevention mechanisms.
    """
    checkout = payment.checkout
    if checkout:
        billing = checkout.billing_address
        shipping = checkout.shipping_address
        email = checkout.get_customer_email()
        user_id = checkout.user_id
        checkout_token = str(checkout.token)
        checkout_metadata = checkout.metadata
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

    order_id = payment.order.pk if payment.order else None
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
        order_id=order_id,
        payment_id=payment.pk,
        graphql_payment_id=graphql_payment_id,
        customer_ip_address=payment.customer_ip_address,
        customer_id=customer_id,
        customer_email=email,
        reuse_source=store_source,
        data=additional_data or {},
        graphql_customer_id=graphql_customer_id,
        refund_data=refund_data,
        _resolve_lines=lambda: create_payment_lines_information(
            payment, manager or get_plugins_manager()
        ),
        checkout_token=checkout_token,
        checkout_metadata=checkout_metadata,
    )


RefundLines = Iterator[Tuple[Any, OrderLine]]


def _prepare_refund_lines(
    order: Order,
    order_lines_to_refund: List[OrderLineData],
    fulfillment_lines_to_refund: List[FulfillmentLineData],
) -> Iterator[Tuple[int, int]]:
    previous_fulfillment_lines = FulfillmentLine.objects.prefetch_related(
        "order_line"
    ).filter(
        fulfillment__order_id=order.pk,
        fulfillment__status__in=[
            FulfillmentStatus.REFUNDED,
            FulfillmentStatus.REFUNDED_AND_RETURNED,
        ],
        order_line__variant_id__isnull=False,
    )

    previous_refund_lines = (
        (p_variant_id, line.quantity)
        for line in previous_fulfillment_lines
        if (p_variant_id := line.order_line.variant_id)
    )

    current_order_refund_lines = (
        (variant.id, line.quantity)
        for line in order_lines_to_refund
        if (variant := line.variant)
    )

    current_fulfillment_refund_lines = (
        (f_variant_id, line.quantity)
        for line in fulfillment_lines_to_refund
        if (f_variant_id := line.line.order_line.variant_id)
    )

    return chain(
        previous_refund_lines,
        current_order_refund_lines,
        current_fulfillment_refund_lines,
    )


def create_refund_data(
    order: Order,
    order_lines_to_refund: List[OrderLineData],
    fulfillment_lines_to_refund: List[FulfillmentLineData],
    refund_shipping_costs: bool,
) -> Dict[int, int]:
    order_lines = {line.variant_id: line.quantity for line in order.lines.all()}

    refund_lines = _prepare_refund_lines(
        order, order_lines_to_refund, fulfillment_lines_to_refund
    )

    summed_refund_lines: Dict[int, int] = defaultdict(int)

    for variant_id, quantity in refund_lines:
        summed_refund_lines[variant_id] += quantity

    lines = {
        variant_id: order_lines[variant_id] - summed_refund_lines[variant_id]
        for variant_id in summed_refund_lines
    }

    shipping_previously_refunded = order.fulfillments.exclude(
        shipping_refund_amount__isnull=True
    ).exists()

    lines[SHIPPING_PAYMENT_LINE_ID] = (
        0 if shipping_previously_refunded or refund_shipping_costs else 1
    )

    return lines


def create_payment(
    gateway: str,
    total: Decimal,
    currency: str,
    email: str,
    customer_ip_address: str = "",
    payment_token: Optional[str] = "",
    extra_data: Dict = None,
    checkout: Checkout = None,
    order: Order = None,
    return_url: str = None,
    external_reference: Optional[str] = None,
) -> Payment:
    """Create a payment instance.

    This method is responsible for creating payment instances that works for
    both Django views and GraphQL mutations.
    """

    if extra_data is None:
        extra_data = {}

    data = {
        "is_active": True,
        "customer_ip_address": customer_ip_address,
        "extra_data": json.dumps(extra_data),
        "token": payment_token,
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
        "psp_reference": external_reference or "",
    }

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


def create_transaction(
    payment: Payment,
    kind: str,
    payment_information: PaymentData,
    action_required: bool = False,
    gateway_response: GatewayResponse = None,
    error_msg=None,
    is_success=False,
) -> Transaction:
    """Create a transaction based on transaction kind and gateway response."""
    # Default values for token, amount, currency are only used in cases where
    # response from gateway was invalid or an exception occurred
    if not gateway_response:
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
    )
    return txn


def get_already_processed_transaction_or_create_new_transaction(
    payment: Payment,
    kind: str,
    payment_information: PaymentData,
    action_required: bool = False,
    gateway_response: GatewayResponse = None,
    error_msg=None,
) -> Transaction:
    if gateway_response and gateway_response.transaction_already_processed:
        txn = get_already_processed_transaction(payment, gateway_response)
        if txn:
            return txn
    return create_transaction(
        payment,
        kind,
        payment_information,
        action_required,
        gateway_response,
        error_msg,
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
            "Gateway response kind must be one of {}".format(
                sorted(ALLOWED_GATEWAY_KINDS)
            )
        )

    try:
        json.dumps(response.raw_response, cls=DjangoJSONEncoder)
    except (TypeError, ValueError):
        raise GatewayError("Gateway response needs to be json serializable")


@traced_atomic_transaction()
def gateway_postprocess(transaction, payment):
    changed_fields = []

    if not transaction.is_success or transaction.already_processed:
        if changed_fields:
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
        changed_fields += ["charge_status", "captured_amount", "modified"]

    elif transaction_kind == TransactionKind.VOID:
        payment.is_active = False
        changed_fields += ["is_active", "modified"]

    elif transaction_kind == TransactionKind.REFUND:
        changed_fields += ["captured_amount", "modified"]
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
            changed_fields += ["charge_status", "captured_amount", "modified"]
    if changed_fields:
        payment.save(update_fields=changed_fields)
    transaction.already_processed = True
    transaction.save(update_fields=["already_processed"])
    if "captured_amount" in changed_fields and payment.order:
        payment.order.update_total_paid()


def fetch_customer_id(user: User, gateway: str):
    """Retrieve users customer_id stored for desired gateway."""
    meta_key = prepare_key_for_gateway_customer_id(gateway)
    return user.get_value_from_private_metadata(key=meta_key)


def store_customer_id(user: User, gateway: str, customer_id: str):
    """Store customer_id in users private meta for desired gateway."""
    meta_key = prepare_key_for_gateway_customer_id(gateway)
    user.store_value_in_private_metadata(items={meta_key: customer_id})
    user.save(update_fields=["private_metadata"])


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
    changed_fields: List[str],
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
    return any([gateway.id == gateway_id for gateway in available_gateways])


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
    return str(value_without_comma.quantize(Decimal("1")))
