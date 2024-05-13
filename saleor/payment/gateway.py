import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Callable, Optional, cast

from ..account.models import User
from ..app.models import App
from ..core.prices import quantize_price
from ..core.tracing import traced_atomic_transaction
from ..order.events import (
    event_transaction_cancel_requested,
    event_transaction_charge_requested,
    event_transaction_refund_requested,
)
from ..order.models import OrderGrantedRefund
from ..payment.interface import (
    CustomerSource,
    PaymentGateway,
    RefundData,
    TransactionActionData,
)
from ..webhook.event_types import WebhookEventSyncType
from ..webhook.utils import get_webhooks_for_event
from . import GatewayError, PaymentError, TransactionAction, TransactionKind
from .models import Payment, Transaction, TransactionEvent, TransactionItem
from .utils import (
    clean_authorize,
    clean_capture,
    create_failed_transaction_event,
    create_payment_information,
    create_transaction,
    gateway_postprocess,
    get_already_processed_transaction_or_create_new_transaction,
    recalculate_refundable_for_checkout,
    update_payment,
    validate_gateway_response,
)

if TYPE_CHECKING:
    from ..plugins.manager import PluginsManager

logger = logging.getLogger(__name__)
ERROR_MSG = "Oops! Something went wrong."
GENERIC_TRANSACTION_ERROR = "Transaction was unsuccessful."


def raise_payment_error(fn: Callable) -> Callable:
    def wrapped(*args, **kwargs):
        result = fn(*args, **kwargs)
        if not result.is_success:
            raise PaymentError(result.error or GENERIC_TRANSACTION_ERROR)
        return result

    return wrapped


def payment_postprocess(fn: Callable) -> Callable:
    def wrapped(*args, **kwargs):
        txn = fn(*args, **kwargs)
        gateway_postprocess(txn, txn.payment)
        return txn

    return wrapped


def require_active_payment(fn: Callable) -> Callable:
    def wrapped(payment: Payment, *args, **kwargs):
        if not payment.is_active:
            raise PaymentError("This payment is no longer active.")
        return fn(payment, *args, **kwargs)

    return wrapped


def with_locked_payment(fn: Callable) -> Callable:
    """Lock payment to protect from asynchronous modification."""

    def wrapped(payment: Payment, *args, **kwargs):
        with traced_atomic_transaction():
            payment = Payment.objects.select_for_update().get(id=payment.id)
            return fn(payment, *args, **kwargs)

    return wrapped


def request_charge_action(
    transaction: TransactionItem,
    manager: "PluginsManager",
    charge_value: Optional[Decimal],
    request_event: TransactionEvent,
    channel_slug: str,
    user: Optional[User],
    app: Optional[App],
):
    if charge_value is None:
        charge_value = transaction.authorized_value

    transaction_action_data = _create_transaction_data(
        transaction=transaction,
        action_type=TransactionAction.CHARGE,
        action_value=charge_value,
        request_event=request_event,
    )
    _request_payment_action(
        transaction_action_data=transaction_action_data,
        manager=manager,
        channel_slug=channel_slug,
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
        transaction_request_func=manager.transaction_charge_requested,
        plugin_func_name="transaction_charge_requested",
    )
    if order_id := transaction.order_id:
        event_transaction_charge_requested(
            order_id=order_id,
            reference=transaction.psp_reference or "",
            amount=quantize_price(charge_value, transaction.currency),
            user=user,
            app=app,
        )


def request_refund_action(
    transaction: TransactionItem,
    manager: "PluginsManager",
    refund_value: Optional[Decimal],
    request_event: TransactionEvent,
    channel_slug: str,
    user: Optional[User],
    app: Optional[App],
    granted_refund: Optional[OrderGrantedRefund] = None,
):
    if refund_value is None:
        refund_value = transaction.charged_value

    transaction_action_data = _create_transaction_data(
        transaction=transaction,
        action_type=TransactionAction.REFUND,
        action_value=refund_value,
        request_event=request_event,
        granted_refund=granted_refund,
    )
    _request_payment_action(
        transaction_action_data=transaction_action_data,
        manager=manager,
        channel_slug=channel_slug,
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        transaction_request_func=manager.transaction_refund_requested,
        plugin_func_name="transaction_refund_requested",
    )

    if order_id := transaction.order_id:
        event_transaction_refund_requested(
            order_id=order_id,
            reference=transaction.psp_reference or "",
            amount=quantize_price(refund_value, transaction.currency),
            user=user,
            app=app,
        )


def request_cancelation_action(
    transaction: TransactionItem,
    manager: "PluginsManager",
    cancel_value: Optional[Decimal],
    request_event: TransactionEvent,
    channel_slug: str,
    user: Optional[User],
    app: Optional[App],
    action: str,
):
    transaction_action_data = _create_transaction_data(
        transaction=transaction,
        action_type=action,
        action_value=cancel_value,
        request_event=request_event,
    )
    _request_payment_action(
        transaction_action_data=transaction_action_data,
        manager=manager,
        channel_slug=channel_slug,
        event_type=WebhookEventSyncType.TRANSACTION_CANCELATION_REQUESTED,
        transaction_request_func=manager.transaction_cancelation_requested,
        plugin_func_name="transaction_cancelation_requested",
    )

    if order_id := transaction.order_id:
        event_transaction_cancel_requested(
            order_id=order_id,
            reference=transaction.psp_reference or "",
            user=user,
            app=app,
        )


def _create_transaction_data(
    transaction: TransactionItem,
    action_type: str,
    action_value: Optional[Decimal],
    request_event: TransactionEvent,
    granted_refund: Optional[OrderGrantedRefund] = None,
):
    app_owner = None
    if transaction.app_id:
        app_owner = cast(App, transaction.app)
        if not app_owner.is_active or app_owner.removed_at:
            app_owner = None

    if not app_owner and transaction.app_identifier:
        app_owner = App.objects.filter(
            identifier=transaction.app_identifier,
            removed_at__isnull=True,
            is_active=True,
        ).first()

    return TransactionActionData(
        transaction=transaction,
        action_type=action_type,
        action_value=action_value,
        event=request_event,
        transaction_app_owner=app_owner,
        granted_refund=granted_refund,
    )


def _request_payment_action(
    transaction_action_data: "TransactionActionData",
    manager: "PluginsManager",
    channel_slug: str,
    event_type: str,
    transaction_request_func: Callable[[TransactionActionData, str], None],
    plugin_func_name: str,
):
    transaction_request_event_active = manager.is_event_active_for_any_plugin(
        plugin_func_name, channel_slug=channel_slug
    )
    webhooks = None
    if transaction_action_data.transaction_app_owner:
        webhooks = get_webhooks_for_event(
            event_type=event_type,
            apps_ids=[transaction_action_data.transaction_app_owner.pk],
        )
    if not transaction_request_event_active and not webhooks:
        recalculate_refundable_for_checkout(
            transaction_action_data.transaction, transaction_action_data.event
        )
        create_failed_transaction_event(
            transaction_action_data.event,
            cause="No app or plugin is configured to handle payment action requests.",
        )
        raise PaymentError(
            "No app or plugin is configured to handle payment action requests."
        )

    transaction_request_func(transaction_action_data, channel_slug)


@raise_payment_error
@require_active_payment
@with_locked_payment
@payment_postprocess
def process_payment(
    payment: Payment,
    token: str,
    manager: "PluginsManager",
    channel_slug: str,
    customer_id: Optional[str] = None,
    store_source: bool = False,
    additional_data: Optional[dict] = None,
) -> Transaction:
    payment_data = create_payment_information(
        payment=payment,
        manager=manager,
        payment_token=token,
        customer_id=customer_id,
        store_source=store_source,
        additional_data=additional_data,
    )

    response, error = _fetch_gateway_response(
        manager.process_payment,
        payment.gateway,
        payment_data,
        channel_slug=channel_slug,
    )
    action_required = response is not None and response.action_required
    if response:
        update_payment(payment, response)
    return get_already_processed_transaction_or_create_new_transaction(
        payment=payment,
        kind=TransactionKind.CAPTURE,
        action_required=action_required,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@require_active_payment
@with_locked_payment
@payment_postprocess
def authorize(
    payment: Payment,
    token: str,
    manager: "PluginsManager",
    channel_slug: str,
    customer_id: Optional[str] = None,
    store_source: bool = False,
) -> Transaction:
    clean_authorize(payment)
    payment_data = create_payment_information(
        payment=payment,
        manager=manager,
        payment_token=token,
        customer_id=customer_id,
        store_source=store_source,
    )
    response, error = _fetch_gateway_response(
        manager.authorize_payment,
        payment.gateway,
        payment_data,
        channel_slug=channel_slug,
    )
    if response:
        update_payment(payment, response)
    return get_already_processed_transaction_or_create_new_transaction(
        payment=payment,
        kind=TransactionKind.AUTH,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@payment_postprocess
@raise_payment_error
@require_active_payment
@with_locked_payment
@payment_postprocess
def capture(
    payment: Payment,
    manager: "PluginsManager",
    channel_slug: str,
    amount: Optional[Decimal] = None,
    customer_id: Optional[str] = None,
    store_source: bool = False,
) -> Transaction:
    if amount is None:
        amount = payment.get_charge_amount()
    clean_capture(payment, Decimal(amount))
    token = _get_past_transaction_token(payment, TransactionKind.AUTH)
    payment_data = create_payment_information(
        payment=payment,
        manager=manager,
        payment_token=token,
        amount=amount,
        customer_id=customer_id,
        store_source=store_source,
    )
    response, error = _fetch_gateway_response(
        manager.capture_payment,
        payment.gateway,
        payment_data,
        channel_slug=channel_slug,
    )
    if response:
        update_payment(payment, response)
    return get_already_processed_transaction_or_create_new_transaction(
        payment=payment,
        kind=TransactionKind.CAPTURE,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@with_locked_payment
@payment_postprocess
def refund(
    payment: Payment,
    manager: "PluginsManager",
    channel_slug: str,
    amount: Optional[Decimal] = None,
    refund_data: Optional["RefundData"] = None,
) -> Transaction:
    if amount is None:
        amount = payment.captured_amount
    _validate_refund_amount(payment, amount)
    if not payment.can_refund():
        raise PaymentError("This payment cannot be refunded.")

    kind = TransactionKind.EXTERNAL if payment.is_manual() else TransactionKind.CAPTURE

    token = _get_past_transaction_token(payment, kind)
    payment_data = create_payment_information(
        payment=payment,
        manager=manager,
        payment_token=token,
        amount=amount,
        refund_data=refund_data,
    )
    if payment.is_manual():
        # for manual payment we just need to mark payment as a refunded
        return create_transaction(
            payment,
            kind=TransactionKind.REFUND,
            payment_information=payment_data,
            is_success=True,
        )

    response, error = _fetch_gateway_response(
        manager.refund_payment, payment.gateway, payment_data, channel_slug=channel_slug
    )
    return get_already_processed_transaction_or_create_new_transaction(
        payment=payment,
        kind=TransactionKind.REFUND,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@with_locked_payment
@payment_postprocess
def void(
    payment: Payment,
    manager: "PluginsManager",
    channel_slug: str,
) -> Transaction:
    token = _get_past_transaction_token(payment, TransactionKind.AUTH)
    payment_data = create_payment_information(
        payment=payment, manager=manager, payment_token=token
    )
    response, error = _fetch_gateway_response(
        manager.void_payment, payment.gateway, payment_data, channel_slug=channel_slug
    )
    return get_already_processed_transaction_or_create_new_transaction(
        payment=payment,
        kind=TransactionKind.VOID,
        payment_information=payment_data,
        error_msg=error,
        gateway_response=response,
    )


@raise_payment_error
@require_active_payment
@with_locked_payment
@payment_postprocess
def confirm(
    payment: Payment,
    manager: "PluginsManager",
    channel_slug: str,
    additional_data: Optional[dict] = None,
) -> Transaction:
    txn = payment.transactions.filter(
        kind=TransactionKind.ACTION_TO_CONFIRM, is_success=True
    ).last()
    token = txn.token if txn else ""
    payment_data = create_payment_information(
        payment=payment,
        manager=manager,
        payment_token=token,
        additional_data=additional_data,
    )
    response, error = _fetch_gateway_response(
        manager.confirm_payment,
        payment.gateway,
        payment_data,
        channel_slug=channel_slug,
    )
    action_required = response is not None and response.action_required
    if response:
        update_payment(payment, response)
    return get_already_processed_transaction_or_create_new_transaction(
        payment=payment,
        kind=TransactionKind.CONFIRM,
        payment_information=payment_data,
        action_required=action_required,
        error_msg=error,
        gateway_response=response,
    )


def list_payment_sources(
    gateway: str,
    customer_id: str,
    manager: "PluginsManager",
    channel_slug: Optional[str],
) -> list["CustomerSource"]:
    return manager.list_payment_sources(gateway, customer_id, channel_slug=channel_slug)


def list_gateways(
    manager: "PluginsManager", channel_slug: Optional[str] = None
) -> list["PaymentGateway"]:
    return manager.list_payment_gateways(channel_slug=channel_slug)


def _fetch_gateway_response(fn, *args, **kwargs):
    response, error = None, None
    try:
        response = fn(*args, **kwargs)
        validate_gateway_response(response)
    except GatewayError:
        logger.exception("Gateway response validation failed!")
        response = None
        error = ERROR_MSG
    except PaymentError:
        logger.exception("Error encountered while executing payment gateway.")
        error = ERROR_MSG
        response = None
    return response, error


def _get_past_transaction_token(
    payment: Payment,
    kind: str,  # for kind use "TransactionKind"
) -> str:
    txn = payment.transactions.filter(kind=kind, is_success=True).last()
    if txn is None:
        raise PaymentError(f"Cannot find successful {kind} transaction.")
    return txn.token


def _validate_refund_amount(payment: Payment, amount: Decimal):
    if amount <= 0:
        raise PaymentError("Amount should be a positive number.")
    if amount > payment.captured_amount:
        raise PaymentError("Cannot refund more than captured.")


def payment_refund_or_void(
    payment: Optional[Payment],
    manager: "PluginsManager",
    channel_slug: Optional[str],
    transaction_id: Optional[str] = None,
):
    if payment is None:
        return
    if payment.can_refund():
        refund_transaction = _get_success_transaction(
            TransactionKind.REFUND_ONGOING, payment, transaction_id
        )
        # The refund should be called only if the refund process is not already started
        # with amount equal payment captured amount.
        # There is no need for summing the amount of all refund transactions,
        # because we always called refund with the full amount that was captured.
        # So if the refund wasn't called with current captured amount we should
        # call refund again.
        if (
            not refund_transaction
            or refund_transaction.amount < payment.captured_amount
        ):
            refund(payment, manager, channel_slug=channel_slug)
    elif payment.can_void():
        void_transaction = _get_success_transaction(
            TransactionKind.VOID, payment, transaction_id
        )
        if not void_transaction:
            void(payment, manager, channel_slug=channel_slug)


def _get_success_transaction(
    kind: str, payment: Payment, transaction_id: Optional[str]
):
    if not transaction_id:
        try:
            transaction_id = _get_past_transaction_token(payment, kind)
        except PaymentError:
            return
    return payment.transactions.filter(
        token=transaction_id,
        action_required=False,
        is_success=True,
        kind=kind,
    ).last()
