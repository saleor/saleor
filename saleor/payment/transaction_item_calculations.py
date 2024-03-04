from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, cast

from . import TransactionEventType
from .models import TransactionEvent, TransactionItem


@dataclass
class BaseEvent:
    request: Optional[TransactionEvent] = None
    success: Optional[TransactionEvent] = None
    failure: Optional[TransactionEvent] = None


@dataclass
class AuthorizationEvents(BaseEvent):
    adjustment: Optional[TransactionEvent] = None


@dataclass
class ChargeEvents(BaseEvent):
    back: Optional[TransactionEvent] = None


@dataclass
class RefundEvents(BaseEvent):
    reverse: Optional[TransactionEvent] = None


@dataclass
class CancelEvents(BaseEvent): ...


PSPReference = str

AUTHORIZATION_EVENTS = [
    TransactionEventType.AUTHORIZATION_SUCCESS,
    TransactionEventType.AUTHORIZATION_FAILURE,
    TransactionEventType.AUTHORIZATION_ADJUSTMENT,
    TransactionEventType.AUTHORIZATION_REQUEST,
]


@dataclass
class ActionEventMap:
    without_psp_reference: list[TransactionEvent]
    authorization: dict[PSPReference, AuthorizationEvents] = field(
        default_factory=lambda: defaultdict(AuthorizationEvents)
    )
    charge: dict[PSPReference, ChargeEvents] = field(
        default_factory=lambda: defaultdict(ChargeEvents)
    )
    refund: dict[PSPReference, RefundEvents] = field(
        default_factory=lambda: defaultdict(RefundEvents)
    )
    cancel: dict[PSPReference, CancelEvents] = field(
        default_factory=lambda: defaultdict(CancelEvents)
    )


def _should_increase_pending_amount(
    request: Optional[TransactionEvent],
    success: Optional[TransactionEvent],
    failure: Optional[TransactionEvent],
) -> bool:
    if request:
        # the pending amount should be increased only when we don't
        # have any failure/success event with the psp reference
        if not failure and not success:
            return True
    return False


def _should_increse_amount(
    success: Optional[TransactionEvent], failure: Optional[TransactionEvent]
) -> bool:
    if success and failure:
        # in case of having success and failure events for the same psp reference
        # we take into account the success transaction only when we don't have
        # newer failure event
        if success.created_at > failure.created_at:
            return True
    elif success:
        return True
    return False


def _recalculate_base_amounts(
    transaction: TransactionItem,
    request: Optional[TransactionEvent],
    success: Optional[TransactionEvent],
    failure: Optional[TransactionEvent],
    pending_amount_field_name: str,
    amount_field_name: str,
    previous_amount_field_name: Optional[str],
):
    if _should_increase_pending_amount(request, success, failure):
        request = cast(TransactionEvent, request)
        pending_value = getattr(transaction, pending_amount_field_name)
        setattr(
            transaction, pending_amount_field_name, pending_value + request.amount_value
        )
        if previous_amount_field_name:
            current_previous_amount = getattr(transaction, previous_amount_field_name)
            setattr(
                transaction,
                previous_amount_field_name,
                current_previous_amount - request.amount_value,
            )

    if _should_increse_amount(success, failure):
        success = cast(TransactionEvent, success)
        current_value = getattr(transaction, amount_field_name)
        setattr(transaction, amount_field_name, current_value + success.amount_value)
        if previous_amount_field_name:
            current_previous_amount = getattr(transaction, previous_amount_field_name)
            setattr(
                transaction,
                previous_amount_field_name,
                current_previous_amount - success.amount_value,
            )


def _recalculate_authorization_amounts(
    transaction: TransactionItem, authorization_events: AuthorizationEvents
):
    success = authorization_events.success
    failure = authorization_events.failure
    request = authorization_events.request
    adjustment = authorization_events.adjustment

    if adjustment:
        # adjustment event overwrites the total amount of authorized
        # value.
        transaction.authorized_value = adjustment.amount_value

    _recalculate_base_amounts(
        transaction,
        request,
        success,
        failure,
        pending_amount_field_name="authorize_pending_value",
        amount_field_name="authorized_value",
        previous_amount_field_name=None,
    )


def _recalculate_charge_amounts(
    transaction: TransactionItem, charge_events: ChargeEvents
):
    success = charge_events.success
    failure = charge_events.failure
    request = charge_events.request
    back = charge_events.back

    if back:
        transaction.charged_value -= back.amount_value

    _recalculate_base_amounts(
        transaction,
        request,
        success,
        failure,
        pending_amount_field_name="charge_pending_value",
        amount_field_name="charged_value",
        previous_amount_field_name="authorized_value",
    )


def _recalculate_refund_amounts(
    transaction: TransactionItem, refund_events: RefundEvents
):
    success = refund_events.success
    failure = refund_events.failure
    request = refund_events.request
    reverse = refund_events.reverse

    if reverse:
        transaction.charged_value += reverse.amount_value
        transaction.refunded_value -= reverse.amount_value

    _recalculate_base_amounts(
        transaction,
        request,
        success,
        failure,
        pending_amount_field_name="refund_pending_value",
        amount_field_name="refunded_value",
        previous_amount_field_name="charged_value",
    )


def _recalculate_cancel_amounts(
    transaction: TransactionItem, cancel_events: CancelEvents
):
    success = cancel_events.success
    failure = cancel_events.failure
    request = cancel_events.request

    _recalculate_base_amounts(
        transaction,
        request,
        success,
        failure,
        pending_amount_field_name="cancel_pending_value",
        amount_field_name="canceled_value",
        previous_amount_field_name="authorized_value",
    )


def _get_authorize_events(events: Iterable[TransactionEvent]) -> list[TransactionEvent]:
    authorize_events: list[TransactionEvent] = [
        event for event in events if event.type in AUTHORIZATION_EVENTS
    ]
    auth_adjustment_event: Optional[TransactionEvent] = next(
        (
            event
            for event in reversed(authorize_events)
            if event.type == TransactionEventType.AUTHORIZATION_ADJUSTMENT
        ),
        None,
    )
    # in case of having authorization_adjustment, the transaction's authorized
    # amount is overwriten by provided amount. In that case we need to skip the older
    # event than the newest authorization_adjustment.
    if auth_adjustment_event:
        adujstment_event_index = authorize_events.index(auth_adjustment_event)
        authorize_events = authorize_events[adujstment_event_index:]
    return authorize_events


def _handle_events_without_psp_reference(
    transaction: TransactionItem, events: list[TransactionEvent]
):
    """Calculate the amounts for event without psp reference.

    The events without a psp reference are the one that are reported by
    transactionCreate or transactionUpdate. For transactionUpdate, we require a
    manually reducing the amount by app, so there is no need to reduce the amount
    from previous state as it is required for transaction events with psp reference
    created by transactionEventReport.
    """

    for event in events:
        if event.type == TransactionEventType.AUTHORIZATION_SUCCESS:
            transaction.authorized_value += event.amount_value
        elif event.type == TransactionEventType.AUTHORIZATION_ADJUSTMENT:
            transaction.authorized_value = event.amount_value
        elif event.type == TransactionEventType.CHARGE_SUCCESS:
            transaction.charged_value += event.amount_value
        elif event.type == TransactionEventType.CHARGE_BACK:
            transaction.charged_value -= event.amount_value

        elif event.type == TransactionEventType.REFUND_SUCCESS:
            transaction.refunded_value += event.amount_value
        elif event.type == TransactionEventType.REFUND_REVERSE:
            transaction.charged_value += event.amount_value
        elif event.type == TransactionEventType.CANCEL_SUCCESS:
            transaction.canceled_value += event.amount_value


def _initilize_action_map(events: Iterable[TransactionEvent]) -> ActionEventMap:
    event_map = ActionEventMap(without_psp_reference=[])
    authorize_events = _get_authorize_events(events)
    events_without_authorize: list[TransactionEvent] = [
        event for event in events if event.type not in AUTHORIZATION_EVENTS
    ]

    for event in authorize_events:
        psp_reference = event.psp_reference
        if not psp_reference:
            event_map.without_psp_reference.append(event)
        elif event.type == TransactionEventType.AUTHORIZATION_REQUEST:
            event_map.authorization[psp_reference].request = event
        elif event.type == TransactionEventType.AUTHORIZATION_SUCCESS:
            event_map.authorization[psp_reference].success = event
        elif event.type == TransactionEventType.AUTHORIZATION_FAILURE:
            event_map.authorization[psp_reference].failure = event
        elif event.type == TransactionEventType.AUTHORIZATION_ADJUSTMENT:
            event_map.authorization[psp_reference].adjustment = event

    for event in events_without_authorize:
        psp_reference = event.psp_reference
        if not psp_reference:
            event_map.without_psp_reference.append(event)
        elif event.type == TransactionEventType.CHARGE_REQUEST:
            event_map.charge[psp_reference].request = event
        elif event.type == TransactionEventType.CHARGE_SUCCESS:
            event_map.charge[psp_reference].success = event
        elif event.type == TransactionEventType.CHARGE_FAILURE:
            event_map.charge[psp_reference].failure = event
        elif event.type == TransactionEventType.CHARGE_BACK:
            event_map.charge[psp_reference].back = event

        elif event.type == TransactionEventType.REFUND_REQUEST:
            event_map.refund[psp_reference].request = event
        elif event.type == TransactionEventType.REFUND_FAILURE:
            event_map.refund[psp_reference].failure = event
        elif event.type == TransactionEventType.REFUND_SUCCESS:
            event_map.refund[psp_reference].success = event
        elif event.type == TransactionEventType.REFUND_REVERSE:
            event_map.refund[psp_reference].reverse = event

        elif event.type == TransactionEventType.CANCEL_REQUEST:
            event_map.cancel[psp_reference].request = event
        elif event.type == TransactionEventType.CANCEL_SUCCESS:
            event_map.cancel[psp_reference].success = event
        elif event.type == TransactionEventType.CANCEL_FAILURE:
            event_map.cancel[psp_reference].failure = event

    return event_map


def _set_transaction_amounts_to_zero(transaction: TransactionItem):
    transaction.authorized_value = Decimal("0")
    transaction.charged_value = Decimal("0")
    transaction.refunded_value = Decimal("0")
    transaction.canceled_value = Decimal("0")

    transaction.authorize_pending_value = Decimal("0")
    transaction.charge_pending_value = Decimal("0")
    transaction.refund_pending_value = Decimal("0")
    transaction.cancel_pending_value = Decimal("0")


def calculate_transaction_amount_based_on_events(transaction: TransactionItem):
    events: Iterable[TransactionEvent] = transaction.events.order_by(
        "created_at"
    ).exclude(include_in_calculations=False)

    action_map = _initilize_action_map(events)
    _set_transaction_amounts_to_zero(transaction)

    _handle_events_without_psp_reference(transaction, action_map.without_psp_reference)

    for authorize_events in action_map.authorization.values():
        _recalculate_authorization_amounts(transaction, authorize_events)

    for charge_events in action_map.charge.values():
        _recalculate_charge_amounts(transaction, charge_events)

    for refund_events in action_map.refund.values():
        _recalculate_refund_amounts(transaction, refund_events)

    for cancel_events in action_map.cancel.values():
        _recalculate_cancel_amounts(transaction, cancel_events)


def recalculate_transaction_amounts(transaction: TransactionItem, save: bool = True):
    """Recalculate transaction amounts.

    The function calculates the transaction amounts based on the amounts that
    are stored in transaction's events. It groups the events based on the
    psp reference and the type of the action (like authorization, or charge).
    The grouping is mandatory to properly match the set of events based on the
    same type and psp reference and correctly increase the amounts.

    In case of having the event of type authorize_adjustment, any authorize
    events older than the `authorize_adjustment` will be skipped. The
    `authorize_adjustment` overwrites the amount of authorization.

    The pending amount is increased only when the `request` event exists for
    a given psp reference. In case of having a success or failure event for
    the same psp reference as the request event, it assumes that the requested
    amount has been already processed. The pending amount will not be increased.

    The transaction amount is increased when the success event exists. In case
    of having a failure event for the same psp reference, the creation time will
    be used to determine which event is newer. If the failure event is newer, the
    success event will be ignored.

    There is a possibility of having events that don't have psp reference (for
    example the events created by Saleor to keep correct amounts). In that case
    the event amounts will be included in the transaction amounts.
    """
    calculate_transaction_amount_based_on_events(transaction)

    transaction.authorized_value = max(transaction.authorized_value, Decimal("0"))
    transaction.authorize_pending_value = max(
        transaction.authorize_pending_value, Decimal("0")
    )

    if save:
        transaction.save(
            update_fields=[
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
