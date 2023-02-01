from datetime import timedelta
from decimal import Decimal
from typing import Callable, List

import pytest
from django.utils import timezone

from .. import TransactionEventType
from ..models import TransactionEvent, TransactionItem
from ..transaction_item_calculations import recalculate_transaction_amounts


@pytest.fixture
def transaction_events_generator(
    transaction_item_created_by_app,
) -> Callable[
    [List[str], List[str], List[Decimal], TransactionItem], List[TransactionEvent]
]:
    def factory(
        psp_references: List[str],
        types: List[str],
        amounts: List[Decimal],
        transaction: TransactionItem = transaction_item_created_by_app,
    ):
        return TransactionEvent.objects.bulk_create(
            TransactionEvent(
                transaction=transaction,
                psp_reference=reference,
                type=event_type,
                amount_value=amount,
            )
            for reference, event_type, amount in zip(psp_references, types, amounts)
        )

    return factory


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
    assert transaction.authorized_value == authorized_value
    assert transaction.charged_value == charged_value
    assert transaction.refunded_value == refunded_value
    assert transaction.canceled_value == canceled_value
    assert transaction.authorize_pending_value == authorize_pending_value
    assert transaction.charge_pending_value == charge_pending_value
    assert transaction.refund_pending_value == refund_pending_value
    assert transaction.cancel_pending_value == cancel_pending_value


def test_with_only_authorize_success_event(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorized_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorize_pending_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorize_pending_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorize_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorize_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorize_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorize_value = Decimal("11.00")
    events = transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorize_value = Decimal("11.00")
    authorize_adjustment_value = Decimal("100")
    events = transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    first_authorize_value = Decimal("11.00")
    second_authorize_value = Decimal("12.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    charged_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    charge_pending_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    charge_pending_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    charge_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    charge_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    charge_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    charge_value = Decimal("11.00")
    events = transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    first_charge_value = Decimal("11.00")
    second_charge_value = Decimal("12.00")
    transaction_events_generator(
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


def test_with_charge_back(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    first_charge_value = Decimal("11.00")
    second_charge_value = Decimal("12.00")
    charge_back_value = Decimal("10.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    refunded_value = Decimal("11.00")
    transaction_events_generator(
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
    _assert_amounts(transaction, refunded_value=refunded_value)


def test_with_only_refund_request_event(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    refund_pending_value = Decimal("11.00")
    transaction_events_generator(
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
    _assert_amounts(transaction, refund_pending_value=refund_pending_value)


def test_with_only_refund_failure_event(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    refund_pending_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    refund_value = Decimal("11.00")
    transaction_events_generator(
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
    )


def test_with_refund_request_and_failure_events(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    refund_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    refund_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    refund_value = Decimal("11.00")
    events = transaction_events_generator(
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
    )


def test_with_refund_request_and_success_events_different_psp_references(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    first_refund_value = Decimal("11.00")
    second_refund_value = Decimal("12.00")
    transaction_events_generator(
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
    )


def test_with_refund_reverse(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    first_refund_value = Decimal("11.00")
    second_refund_value = Decimal("12.00")
    reverse_refund = Decimal("10.00")
    transaction_events_generator(
        psp_references=["1", "2", "3"],
        types=[
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_SUCCESS,
            TransactionEventType.REFUND_REVERSE,
        ],
        amounts=[first_refund_value, second_refund_value, reverse_refund],
    )

    # when
    recalculate_transaction_amounts(transaction)

    # then
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        refund_pending_value=Decimal("0"),
        refunded_value=first_refund_value + second_refund_value - reverse_refund,
    )


def test_with_only_cancel_success_event(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    canceled_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    cancel_pending_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    cancel_pending_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    cancel_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    cancel_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    cancel_value = Decimal("11.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    cancel_value = Decimal("11.00")
    events = transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    first_cancel_value = Decimal("11.00")
    second_cancel_value = Decimal("12.00")
    transaction_events_generator(
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
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app
    authorize_value = Decimal("110.00")
    charge_value = Decimal("100.00")
    first_refund_value = Decimal("30.0")
    second_refund_value = Decimal("11.00")
    transaction_events_generator(
        psp_references=[None, None, None, None, "5"],
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
        charged_value=charge_value,
        refunded_value=first_refund_value + second_refund_value,
    )


def test_event_multiple_events(
    transaction_item_created_by_app, transaction_events_generator
):
    # given
    transaction = transaction_item_created_by_app

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
    transaction.refresh_from_db()
    _assert_amounts(
        transaction,
        authorized_value=authorize_adjustment_value,
        charged_value=first_charge_value + second_charge_value - charge_back_value,
        refunded_value=first_refund_value - refund_reverse_value,
        charge_pending_value=charge_pending_value,
        refund_pending_value=second_refund_pending_value,
    )
