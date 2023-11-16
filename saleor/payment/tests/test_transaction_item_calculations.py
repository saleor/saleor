import datetime
from datetime import timedelta
from decimal import Decimal

import pytz
from django.utils import timezone
from freezegun import freeze_time

from .. import TransactionEventType
from ..models import TransactionItem
from ..transaction_item_calculations import recalculate_transaction_amounts


def _assert_amounts(
    transaction: TransactionItem,
    authorized_value=Decimal("0"),
    charged_value=Decimal("0"),
    refunded_value=Decimal("0"),
    canceled_value=Decimal("0"),
    authorize_pending_value=Decimal("0"),
    charge_pending_value=Decimal("0"),
    refund_pending_value=Decimal("0"),
    cancel_pending_value=Decimal("0"),
):
    assert sum(
        [
            transaction.authorized_value,
            transaction.charged_value,
            transaction.refunded_value,
            transaction.canceled_value,
            transaction.authorize_pending_value,
            transaction.charge_pending_value,
            transaction.refund_pending_value,
            transaction.cancel_pending_value,
        ]
    ) == sum(
        [
            authorized_value,
            charged_value,
            refunded_value,
            canceled_value,
            authorize_pending_value,
            charge_pending_value,
            refund_pending_value,
            cancel_pending_value,
        ]
    )
    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.refunded_value == refunded_value
    assert transaction.canceled_value == canceled_value
    assert transaction.authorize_pending_value == authorize_pending_value
    assert transaction.charge_pending_value == charge_pending_value
    assert transaction.refund_pending_value == refund_pending_value
    assert transaction.cancel_pending_value == cancel_pending_value


def test_with_only_authorize_success_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorized_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ],
        amounts=[
            authorized_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(transaction, authorized_value=authorized_value)


def test_with_only_authorize_request_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorize_pending_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_REQUEST,
        ],
        amounts=[
            authorize_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(transaction, authorize_pending_value=authorize_pending_value)


def test_with_only_authorize_failure_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorize_pending_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_FAILURE,
        ],
        amounts=[
            authorize_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, authorize_pending_value=Decimal("0"), authorized_value=Decimal("0")
    )


def test_with_authorize_request_and_success_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorize_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ],
        amounts=[authorize_value, authorize_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        authorize_pending_value=Decimal("0"),
        authorized_value=authorize_value,
    )


def test_with_authorize_request_and_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorize_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_FAILURE,
        ],
        amounts=[authorize_value, authorize_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, authorize_pending_value=Decimal("0"), authorized_value=Decimal("0")
    )


def test_with_authorize_success_and_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorize_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_FAILURE,
        ],
        amounts=[authorize_value, authorize_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, authorize_pending_value=Decimal("0"), authorized_value=Decimal("0")
    )


def test_with_authorize_success_and_older_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorize_value = Decimal("11.00")
    events = transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_FAILURE,
        ],
        amounts=[authorize_value, authorize_value],
    )
    failure_event = events[1]
    assert failure_event.type == TransactionEventType.AUTHORIZATION_FAILURE
    failure_event.created_at = timezone.now() - timedelta(minutes=5)
    failure_event.save()

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        authorize_pending_value=Decimal("0"),
        authorized_value=authorize_value,
    )


def test_with_authorize_adjustment(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorize_value = Decimal("11.00")
    authorize_adjustment_value = Decimal("100")
    events = transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "2", "3", "4"],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_ADJUSTMENT,
            TransactionEventType.AUTHORIZATION_ADJUSTMENT,
        ],
        amounts=[
            authorize_value,
            authorize_value,
            authorize_adjustment_value,
            authorize_value,
        ],
    )

    # set the newest time for adjustment event
    adjustment_event = events[2]
    assert adjustment_event.type == TransactionEventType.AUTHORIZATION_ADJUSTMENT
    adjustment_event.created_at = timezone.now() + timedelta(minutes=5)
    adjustment_event.save()

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        authorize_pending_value=Decimal("0"),
        authorized_value=authorize_adjustment_value,
    )


def test_with_authorize_request_and_success_events_different_psp_references(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    first_authorize_value = Decimal("11.00")
    second_authorize_value = Decimal("12.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "2", "2"],
        types=[
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ],
        amounts=[first_authorize_value, second_authorize_value, second_authorize_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        authorize_pending_value=first_authorize_value,
        authorized_value=second_authorize_value,
    )


def test_with_only_charge_success_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    charged_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.CHARGE_SUCCESS,
        ],
        amounts=[
            charged_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(transaction, charged_value=charged_value)


def test_with_only_charge_request_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    charge_pending_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.CHARGE_REQUEST,
        ],
        amounts=[
            charge_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(transaction, charge_pending_value=charge_pending_value)


def test_with_only_charge_failure_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    charge_pending_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.CHARGE_FAILURE,
        ],
        amounts=[
            charge_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, charge_pending_value=Decimal("0"), charged_value=Decimal("0")
    )


def test_with_charge_request_and_success_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    charge_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.CHARGE_SUCCESS,
        ],
        amounts=[charge_value, charge_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        charge_pending_value=Decimal("0"),
        charged_value=charge_value,
    )


def test_with_charge_request_and_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    charge_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.CHARGE_FAILURE,
        ],
        amounts=[charge_value, charge_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, charge_pending_value=Decimal("0"), charged_value=Decimal("0")
    )


def test_with_charge_success_and_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    charge_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_FAILURE,
        ],
        amounts=[charge_value, charge_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, charge_pending_value=Decimal("0"), charged_value=Decimal("0")
    )


def test_with_charge_success_and_older_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    charge_value = Decimal("11.00")
    events = transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_FAILURE,
        ],
        amounts=[charge_value, charge_value],
    )
    failure_event = events[1]
    assert failure_event.type == TransactionEventType.CHARGE_FAILURE
    failure_event.created_at = timezone.now() - timedelta(minutes=5)
    failure_event.save()

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        charge_pending_value=Decimal("0"),
        charged_value=charge_value,
    )


def test_with_charge_request_and_success_events_different_psp_references(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    first_charge_value = Decimal("11.00")
    second_charge_value = Decimal("12.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "2", "2"],
        types=[
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.CHARGE_SUCCESS,
        ],
        amounts=[first_charge_value, second_charge_value, second_charge_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        charge_pending_value=first_charge_value,
        charged_value=second_charge_value,
    )


def test_with_charge_back(transaction_item_generator, transaction_events_generator):
    # given
    transaction = transaction_item_generator()
    first_charge_value = Decimal("11.00")
    second_charge_value = Decimal("12.00")
    charge_back_value = Decimal("10.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "2", "3"],
        types=[
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_BACK,
        ],
        amounts=[first_charge_value, second_charge_value, charge_back_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        charge_pending_value=Decimal("0"),
        charged_value=first_charge_value + second_charge_value - charge_back_value,
    )


def test_with_only_refund_success_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    refunded_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.REFUND_SUCCESS,
        ],
        amounts=[
            refunded_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, refunded_value=refunded_value, charged_value=-refunded_value
    )


def test_with_only_refund_request_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    refund_pending_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.REFUND_REQUEST,
        ],
        amounts=[
            refund_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        refund_pending_value=refund_pending_value,
        charged_value=-refund_pending_value,
    )


def test_with_only_refund_failure_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    refund_pending_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.REFUND_FAILURE,
        ],
        amounts=[
            refund_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, refund_pending_value=Decimal("0"), refunded_value=Decimal("0")
    )


def test_with_refund_request_and_success_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    refund_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_SUCCESS,
        ],
        amounts=[refund_value, refund_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        refund_pending_value=Decimal("0"),
        refunded_value=refund_value,
        charged_value=-refund_value,
    )


def test_with_refund_request_and_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    refund_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_FAILURE,
        ],
        amounts=[refund_value, refund_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, refund_pending_value=Decimal("0"), refunded_value=Decimal("0")
    )


def test_with_refund_success_and_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    refund_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_FAILURE,
        ],
        amounts=[refund_value, refund_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, refund_pending_value=Decimal("0"), refunded_value=Decimal("0")
    )


def test_with_refund_success_and_older_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    refund_value = Decimal("11.00")
    events = transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_FAILURE,
        ],
        amounts=[refund_value, refund_value],
    )
    failure_event = events[1]
    assert failure_event.type == TransactionEventType.REFUND_FAILURE
    failure_event.created_at = timezone.now() - timedelta(minutes=5)
    failure_event.save()

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        refund_pending_value=Decimal("0"),
        refunded_value=refund_value,
        charged_value=-refund_value,
    )


def test_with_refund_request_and_success_events_different_psp_references(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    first_refund_value = Decimal("11.00")
    second_refund_value = Decimal("12.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "2", "2"],
        types=[
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_SUCCESS,
        ],
        amounts=[first_refund_value, second_refund_value, second_refund_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        refund_pending_value=first_refund_value,
        refunded_value=second_refund_value,
        charged_value=-(first_refund_value + second_refund_value),
    )


def test_with_refund_reverse(transaction_item_generator, transaction_events_generator):
    # given
    transaction = transaction_item_generator()
    first_refund_value = Decimal("11.00")
    second_refund_value = Decimal("12.00")
    reverse_refund = Decimal("10.00")
    charged_value = Decimal("40")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "2", "3", "4"],
        types=[
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_REVERSE,
            TransactionEventType.CHARGE_SUCCESS,
        ],
        amounts=[
            first_refund_value,
            second_refund_value,
            reverse_refund,
            charged_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        refund_pending_value=Decimal("0"),
        charged_value=charged_value
        - first_refund_value
        - second_refund_value
        + reverse_refund,
        refunded_value=first_refund_value + second_refund_value - reverse_refund,
    )


def test_with_only_cancel_success_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    canceled_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.CANCEL_SUCCESS,
        ],
        amounts=[
            canceled_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(transaction, canceled_value=canceled_value)


def test_with_only_cancel_request_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    cancel_pending_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.CANCEL_REQUEST,
        ],
        amounts=[
            cancel_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(transaction, cancel_pending_value=cancel_pending_value)


def test_with_only_cancel_failure_event(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    cancel_pending_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.CANCEL_FAILURE,
        ],
        amounts=[
            cancel_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, cancel_pending_value=Decimal("0"), canceled_value=Decimal("0")
    )


def test_with_cancel_request_and_success_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    cancel_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.CANCEL_SUCCESS,
        ],
        amounts=[cancel_value, cancel_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        cancel_pending_value=Decimal("0"),
        canceled_value=cancel_value,
    )


def test_with_cancel_request_and_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    cancel_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.CANCEL_FAILURE,
        ],
        amounts=[cancel_value, cancel_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, cancel_pending_value=Decimal("0"), canceled_value=Decimal("0")
    )


def test_with_cancel_success_and_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    cancel_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.CANCEL_SUCCESS,
            TransactionEventType.CANCEL_FAILURE,
        ],
        amounts=[cancel_value, cancel_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, cancel_pending_value=Decimal("0"), canceled_value=Decimal("0")
    )


def test_with_cancel_success_and_older_failure_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    cancel_value = Decimal("11.00")
    events = transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "1"],
        types=[
            TransactionEventType.CANCEL_SUCCESS,
            TransactionEventType.CANCEL_FAILURE,
        ],
        amounts=[cancel_value, cancel_value],
    )
    failure_event = events[1]
    assert failure_event.type == TransactionEventType.CANCEL_FAILURE
    failure_event.created_at = timezone.now() - timedelta(minutes=5)
    failure_event.save()

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        cancel_pending_value=Decimal("0"),
        canceled_value=cancel_value,
    )


def test_with_cancel_request_and_success_events_different_psp_references(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    first_cancel_value = Decimal("11.00")
    second_cancel_value = Decimal("12.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "2", "2"],
        types=[
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.CANCEL_SUCCESS,
        ],
        amounts=[first_cancel_value, second_cancel_value, second_cancel_value],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        cancel_pending_value=first_cancel_value,
        canceled_value=second_cancel_value,
    )


def test_event_without_psp_reference(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorize_value = Decimal("110.00")
    charge_value = Decimal("50.00")
    first_refund_value = Decimal("30.0")
    second_refund_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[None, None, "3", "3", None],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_SUCCESS,
        ],
        amounts=[
            authorize_value,
            charge_value,
            first_refund_value,  # value assigned to refund requst
            first_refund_value,
            second_refund_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        authorized_value=authorize_value,
        charged_value=charge_value - first_refund_value,
        refunded_value=first_refund_value + second_refund_value,
    )


def test_event_multiple_events(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()

    authorize_value = Decimal("200.00")
    authorize_adjustment_value = Decimal("250.00")

    first_charge_value = Decimal("59.00")
    first_charge_pending_value = Decimal("59.00")
    second_charge_value = Decimal("11.00")
    charge_back_value = Decimal("5.00")
    charge_pending_value = Decimal("13.00")

    first_refund_value = Decimal("7.00")
    first_refund_pending_value = Decimal("7.00")

    second_refund_pending_value = Decimal("22.00")

    refund_reverse_value = Decimal("3.00")

    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            None,
            "authorization-adjustment",
            "first-charge",
            "first-charge",
            "second-charge",
            "charge-back",
            "charge-pending",
            "first-refund",
            "first-refund",
            "refund-pending",
            "refund-reverse",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_ADJUSTMENT,
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_BACK,
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_REVERSE,
        ],
        amounts=[
            authorize_value,
            authorize_adjustment_value,
            first_charge_value,
            first_charge_pending_value,
            second_charge_value,
            charge_back_value,
            charge_pending_value,
            first_refund_value,
            first_refund_pending_value,
            second_refund_pending_value,
            refund_reverse_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then

    # second pending refund is only use as for the first one we already received
    # success notification
    total_refund_pending = second_refund_pending_value

    # total refund includes all success refund, and removes any refund reverse
    total_refunded = first_refund_value - refund_reverse_value

    total_charge_pending = charge_pending_value

    # total charged is a sum of charges minus the amounts that were moved to refund or
    # pending refund
    total_charged = (
        first_charge_value + second_charge_value - total_refunded - total_refund_pending
    )

    # total authorized is the amount left and accessible for authorization. The amount
    # that was charged, refunded or canceled is subtracted from total authorize
    total_authorized = (
        authorize_adjustment_value
        - total_charged
        - total_charge_pending
        - total_refunded
        - total_refund_pending
    )

    transaction.refresh_from_db()

    _assert_amounts(
        transaction,
        authorized_value=total_authorized,
        # charge back is reduced from charged value as we don't have this part of money
        # anymore
        charged_value=total_charged - charge_back_value,
        refunded_value=total_refunded,
        charge_pending_value=charge_pending_value,
        refund_pending_value=total_refund_pending,
    )


def test_event_multiple_events_with_auth_charge_and_refund(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()

    authorize_value = Decimal("250.00")

    charged_value = Decimal("200")
    charged_pending_value = Decimal("50")
    refunded_value = Decimal("30")
    ongoing_pending_refund_value = Decimal("15")

    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "authorization",
            "charge",
            "charge-pending",
            "refund",
            "refund-pending",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_REQUEST,
        ],
        amounts=[
            authorize_value,
            charged_value,
            charged_pending_value,
            refunded_value,
            ongoing_pending_refund_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    total_refunded = refunded_value
    total_pending_refund = ongoing_pending_refund_value
    total_charged = charged_value - total_refunded - total_pending_refund
    total_pending_charge = charged_pending_value

    total_authorize = (
        authorize_value
        - total_charged
        - total_pending_charge
        - total_refunded
        - total_pending_refund
    )
    transaction.refresh_from_db()

    _assert_amounts(
        transaction,
        authorized_value=total_authorize,
        charged_value=total_charged,
        charge_pending_value=total_pending_charge,
        refunded_value=total_refunded,
        refund_pending_value=total_pending_refund,
    )


def test_event_multiple_events_with_auth_charge_and_refund_without_psp_references(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()

    authorize_value = Decimal("250.00")

    charged_value = Decimal("200")
    charged_pending_value = Decimal("50")
    refunded_value = Decimal("30")
    ongoing_pending_refund_value = Decimal("15")

    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            None,
            None,
            None,
            "charge-request",
            "refund-request",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.CHARGE_REQUEST,
            TransactionEventType.REFUND_REQUEST,
        ],
        amounts=[
            authorize_value,
            charged_value,
            refunded_value,
            charged_pending_value,
            ongoing_pending_refund_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    total_refunded = refunded_value
    total_pending_refund = ongoing_pending_refund_value
    total_charged = charged_value - total_pending_refund
    total_pending_charge = charged_pending_value

    total_authorize = authorize_value - charged_pending_value
    transaction.refresh_from_db()

    _assert_amounts(
        transaction,
        authorized_value=total_authorize,
        charged_value=total_charged,
        charge_pending_value=total_pending_charge,
        refunded_value=total_refunded,
        refund_pending_value=total_pending_refund,
    )


def test_event_multiple_events_with_auth_and_cancel(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()

    authorize_value = Decimal("200.00")
    authorize_adjustment_value = Decimal("250.00")

    canceled_value = Decimal("11.00")
    cancel_pending_value = Decimal("11")
    ongoing_pending_value = Decimal("3")

    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            None,
            "authorization-adjustment",
            "cancel-ref",
            "cancel-ref",
            "ongoing_pending_value",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_ADJUSTMENT,
            TransactionEventType.CANCEL_REQUEST,
            TransactionEventType.CANCEL_SUCCESS,
            TransactionEventType.CANCEL_REQUEST,
        ],
        amounts=[
            authorize_value,
            authorize_adjustment_value,
            cancel_pending_value,
            canceled_value,
            ongoing_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    total_canceled = canceled_value
    total_pending_canceled = ongoing_pending_value

    total_authorized = (
        authorize_adjustment_value - total_canceled - total_pending_canceled
    )

    transaction.refresh_from_db()

    _assert_amounts(
        transaction,
        authorized_value=total_authorized,
        canceled_value=total_canceled,
        cancel_pending_value=total_pending_canceled,
    )


def test_event_multiple_events_with_charge_and_refund(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()

    charged_value = Decimal("250.00")

    refunded_value = Decimal("11.00")
    refund_pending_value = Decimal("15")
    ongoing_refund_pending_value = Decimal("3")

    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "charge",
            "refund",
            "refund",
            "ongoing_refund_pending_value",
        ],
        types=[
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_REQUEST,
        ],
        amounts=[
            charged_value,
            refunded_value,
            refund_pending_value,
            ongoing_refund_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    total_refuned = refunded_value
    total_pending_refund = ongoing_refund_pending_value

    total_charged = charged_value - total_refuned - total_pending_refund

    transaction.refresh_from_db()

    _assert_amounts(
        transaction,
        charged_value=total_charged,
        refunded_value=total_refuned,
        refund_pending_value=total_pending_refund,
    )


def test_event_multiple_events_with_charge_and_failure_refund(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()

    charged_value = Decimal("250.00")

    refunded_value = Decimal("11.00")
    refund_pending_value = Decimal("15")
    ongoing_refund_pending_value = Decimal("3")

    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "charge",
            "refund",
            "refund",
            "ongoing_refund_pending_value",
        ],
        types=[
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_FAILURE,
            TransactionEventType.REFUND_REQUEST,
        ],
        amounts=[
            charged_value,
            refund_pending_value,
            refunded_value,
            ongoing_refund_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    total_refuned = Decimal(0)
    total_pending_refund = ongoing_refund_pending_value

    total_charged = charged_value - total_refuned - total_pending_refund

    transaction.refresh_from_db()

    _assert_amounts(
        transaction,
        charged_value=total_charged,
        refunded_value=total_refuned,
        refund_pending_value=total_pending_refund,
    )


def test_event_multiple_events_and_transaction_with_amounts(
    transaction_item_generator, transaction_events_generator
):
    # given
    currently_authorized = Decimal("30")
    currently_charged = Decimal("200")
    transaction = transaction_item_generator(
        authorized_value=currently_authorized,
        charged_value=currently_charged,
    )
    charged_value = Decimal("20.00")

    refunded_value = Decimal("11.00")
    refund_pending_value = Decimal("15")
    ongoing_refund_pending_value = Decimal("3")

    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "charge",
            "refund",
            "refund",
            "ongoing_refund_pending_value",
        ],
        types=[
            TransactionEventType.CHARGE_SUCCESS,
            TransactionEventType.REFUND_REQUEST,
            TransactionEventType.REFUND_FAILURE,
            TransactionEventType.REFUND_REQUEST,
        ],
        amounts=[
            charged_value,
            refund_pending_value,
            refunded_value,
            ongoing_refund_pending_value,
        ],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then

    total_refuned = Decimal(0)
    total_pending_refund = ongoing_refund_pending_value

    total_charged = max(
        (currently_charged + charged_value - total_refuned - total_pending_refund),
        Decimal("0"),
    )

    transaction.refresh_from_db()

    _assert_amounts(
        transaction,
        authorized_value=currently_authorized - charged_value,
        charged_value=total_charged,
        refunded_value=total_refuned,
        refund_pending_value=total_pending_refund,
    )


def test_skips_event_that_should_not_be_taken_into_account(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    first_value = Decimal("11.00")
    second_value = Decimal("12.00")
    transaction_events = transaction_events_generator(
        transaction=transaction,
        psp_references=["1", "2", "2"],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
            TransactionEventType.AUTHORIZATION_REQUEST,
            TransactionEventType.AUTHORIZATION_FAILURE,
        ],
        amounts=[first_value, second_value, second_value],
    )
    transaction_event_to_skip = transaction_events[-1]
    transaction_event_to_skip.include_in_calculations = False
    transaction_event_to_skip.save()

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction, authorized_value=first_value, authorize_pending_value=second_value
    )


@freeze_time("2020-03-18 12:00:00")
def test_recalculate_transaction_amounts_updates_transaction_modified_at(
    transaction_item_generator, transaction_events_generator
):
    # given
    transaction = transaction_item_generator()
    authorized_value = Decimal("11.00")
    transaction_events_generator(
        transaction=transaction,
        psp_references=[
            "1",
        ],
        types=[
            TransactionEventType.AUTHORIZATION_SUCCESS,
        ],
        amounts=[
            authorized_value,
        ],
    )
    # when
    with freeze_time("2023-03-18 12:00:00"):
        calculation_time = datetime.datetime.now(pytz.UTC)
        recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    assert transaction.modified_at == calculation_time
