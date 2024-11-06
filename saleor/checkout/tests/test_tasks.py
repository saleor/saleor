import datetime
import logging
from decimal import Decimal
from unittest import mock
from uuid import UUID

import graphene
import pytest
from django.utils import timezone

from ...order import OrderEvents
from ...order.models import Order
from ..models import Checkout, CheckoutLine
from ..tasks import (
    automatic_checkout_completion_task,
    delete_expired_checkouts,
    task_logger,
)


def test_delete_expired_anonymous_checkouts(checkouts_list, variant, customer_user):
    # given
    now = timezone.now()
    checkout_count = Checkout.objects.count()

    variant_listings_map = {
        listing.channel_id: listing.price_amount
        for listing in variant.channel_listings.all()
    }
    lines_to_create = []

    expired_anonymous_checkout = checkouts_list[0]
    expired_anonymous_checkout.email = None
    expired_anonymous_checkout.user = None
    expired_anonymous_checkout.created_at = now - datetime.timedelta(days=40)
    expired_anonymous_checkout.last_change = now - datetime.timedelta(days=35)
    lines_to_create.append(
        CheckoutLine(
            checkout=expired_anonymous_checkout,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                expired_anonymous_checkout.channel_id, Decimal("11")
            ),
        )
    )

    not_expired_checkout_1 = checkouts_list[1]
    not_expired_checkout_1.email = None
    not_expired_checkout_1.user = None
    not_expired_checkout_1.created_at = now - datetime.timedelta(days=35)
    not_expired_checkout_1.last_change = now - datetime.timedelta(days=29)
    lines_to_create.append(
        CheckoutLine(
            checkout=not_expired_checkout_1,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                not_expired_checkout_1.channel_id, Decimal("11")
            ),
        )
    )

    not_expired_checkout_2 = checkouts_list[2]
    not_expired_checkout_2.email = None
    not_expired_checkout_2.user = customer_user
    not_expired_checkout_2.created_at = now - datetime.timedelta(days=45)
    not_expired_checkout_2.last_change = now - datetime.timedelta(days=40)
    lines_to_create.append(
        CheckoutLine(
            checkout=not_expired_checkout_2,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                not_expired_checkout_2.channel_id, Decimal("11")
            ),
        )
    )

    not_expired_checkout_3 = checkouts_list[3]
    not_expired_checkout_3.email = "test@example.com"
    not_expired_checkout_3.user = None
    not_expired_checkout_3.created_at = now - datetime.timedelta(days=45)
    not_expired_checkout_3.last_change = now - datetime.timedelta(days=40)
    lines_to_create.append(
        CheckoutLine(
            checkout=not_expired_checkout_3,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                not_expired_checkout_3.channel_id, Decimal("11")
            ),
        )
    )

    empty_checkout = checkouts_list[4]
    empty_checkout.last_change = now - datetime.timedelta(hours=8)
    assert empty_checkout.lines.count() == 0

    CheckoutLine.objects.bulk_create(lines_to_create)

    Checkout.objects.bulk_update(
        [
            expired_anonymous_checkout,
            not_expired_checkout_1,
            not_expired_checkout_2,
            not_expired_checkout_3,
        ],
        ["created_at", "last_change", "email", "user"],
    )

    # when
    delete_expired_checkouts()

    # then
    assert Checkout.objects.count() == checkout_count - 1
    with pytest.raises(Checkout.DoesNotExist):
        expired_anonymous_checkout.refresh_from_db()


def test_delete_expired_user_checkouts(checkouts_list, variant, customer_user):
    # given
    now = timezone.now()
    checkout_count = Checkout.objects.count()

    variant_listings_map = {
        listing.channel_id: listing.price_amount
        for listing in variant.channel_listings.all()
    }
    lines_to_create = []

    expired_user_checkout_1 = checkouts_list[0]
    expired_user_checkout_1.email = None
    expired_user_checkout_1.user = customer_user
    expired_user_checkout_1.created_at = now - datetime.timedelta(days=100)
    expired_user_checkout_1.last_change = now - datetime.timedelta(days=98)
    lines_to_create.append(
        CheckoutLine(
            checkout=expired_user_checkout_1,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                expired_user_checkout_1.channel_id, Decimal("11")
            ),
        )
    )

    expired_user_checkout_2 = checkouts_list[1]
    expired_user_checkout_2.email = "test@example.com"
    expired_user_checkout_2.user = None
    expired_user_checkout_2.created_at = now - datetime.timedelta(days=100)
    expired_user_checkout_2.last_change = now - datetime.timedelta(days=91)
    lines_to_create.append(
        CheckoutLine(
            checkout=expired_user_checkout_2,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                expired_user_checkout_2.channel_id, Decimal("11")
            ),
        )
    )

    not_expired_checkout_1 = checkouts_list[2]
    not_expired_checkout_1.email = None
    not_expired_checkout_1.user = None
    not_expired_checkout_1.created_at = now - datetime.timedelta(days=35)
    not_expired_checkout_1.last_change = now - datetime.timedelta(days=29)
    lines_to_create.append(
        CheckoutLine(
            checkout=not_expired_checkout_1,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                not_expired_checkout_1.channel_id, Decimal("11")
            ),
        )
    )

    not_expired_checkout_2 = checkouts_list[3]
    not_expired_checkout_2.email = "test@example.com"
    not_expired_checkout_2.user = None
    not_expired_checkout_2.created_at = now - datetime.timedelta(days=100)
    not_expired_checkout_2.last_change = now - datetime.timedelta(days=60)
    lines_to_create.append(
        CheckoutLine(
            checkout=not_expired_checkout_2,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                not_expired_checkout_2.channel_id, Decimal("11")
            ),
        )
    )

    not_expired_checkout_3 = checkouts_list[4]
    not_expired_checkout_3.email = None
    not_expired_checkout_3.user = customer_user
    not_expired_checkout_3.created_at = now - datetime.timedelta(days=100)
    not_expired_checkout_3.last_change = now - datetime.timedelta(days=89)
    lines_to_create.append(
        CheckoutLine(
            checkout=not_expired_checkout_3,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                not_expired_checkout_3.channel_id, Decimal("11")
            ),
        )
    )
    CheckoutLine.objects.bulk_create(lines_to_create)
    Checkout.objects.bulk_update(
        [
            expired_user_checkout_1,
            expired_user_checkout_2,
            not_expired_checkout_1,
            not_expired_checkout_2,
            not_expired_checkout_3,
        ],
        ["created_at", "last_change", "email", "user"],
    )

    # when
    delete_expired_checkouts()

    # then
    assert Checkout.objects.count() == checkout_count - 2
    for checkout in [expired_user_checkout_1, expired_user_checkout_2]:
        with pytest.raises(Checkout.DoesNotExist):
            checkout.refresh_from_db()


def test_delete_empty_checkouts(checkouts_list, customer_user, variant):
    # given
    now = timezone.now()
    checkout_count = Checkout.objects.count()

    empty_checkout_1 = checkouts_list[0]
    empty_checkout_1.last_change = now - datetime.timedelta(hours=8)
    assert empty_checkout_1.lines.count() == 0

    empty_checkout_2 = checkouts_list[1]
    empty_checkout_2.email = "test@example.com"
    empty_checkout_2.user = customer_user
    empty_checkout_2.last_change = now - datetime.timedelta(hours=8)
    assert empty_checkout_2.lines.count() == 0

    empty_checkout_3 = checkouts_list[2]
    empty_checkout_3.last_change = now - datetime.timedelta(hours=2)
    assert empty_checkout_3.lines.count() == 0

    not_empty_checkout = checkouts_list[3]
    not_empty_checkout.last_change = now - datetime.timedelta(days=2)
    not_empty_checkout.lines.create(
        checkout=not_empty_checkout,
        variant=variant,
        quantity=1,
        undiscounted_unit_price_amount=variant.channel_listings.get(
            channel_id=not_empty_checkout.channel_id
        ).price_amount,
    )

    Checkout.objects.bulk_update(
        [empty_checkout_1, empty_checkout_2, empty_checkout_3, not_empty_checkout],
        ["last_change", "email", "user"],
    )

    # when
    delete_expired_checkouts()

    # then
    for checkout in [empty_checkout_1, empty_checkout_2]:
        with pytest.raises(Checkout.DoesNotExist):
            checkout.refresh_from_db()
    assert Checkout.objects.count() == checkout_count - 2


def test_delete_expired_checkouts(checkouts_list, customer_user, variant):
    # given
    now = timezone.now()
    checkout_count = Checkout.objects.count()

    lines_to_create = []
    variant_listings_map = {
        listing.channel_id: listing.price_amount
        for listing in variant.channel_listings.all()
    }

    expired_anonymous_checkout = checkouts_list[0]
    expired_anonymous_checkout.email = None
    expired_anonymous_checkout.created_at = now - datetime.timedelta(days=40)
    expired_anonymous_checkout.last_change = now - datetime.timedelta(days=35)
    lines_to_create.append(
        CheckoutLine(
            checkout=expired_anonymous_checkout,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                expired_anonymous_checkout.channel_id, Decimal("11")
            ),
        )
    )

    expired_user_checkout = checkouts_list[2]
    expired_user_checkout.user = customer_user
    expired_user_checkout.created_at = now - datetime.timedelta(days=100)
    expired_user_checkout.last_change = now - datetime.timedelta(days=95)
    lines_to_create.append(
        CheckoutLine(
            checkout=expired_user_checkout,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                expired_user_checkout.channel_id, Decimal("11")
            ),
        )
    )

    empty_checkout = checkouts_list[4]
    empty_checkout.last_change = now - datetime.timedelta(hours=8)
    assert empty_checkout.lines.count() == 0

    CheckoutLine.objects.bulk_create(lines_to_create)
    Checkout.objects.bulk_update(
        [expired_anonymous_checkout, expired_user_checkout, empty_checkout],
        ["created_at", "last_change", "email", "user"],
    )

    # when
    delete_expired_checkouts()

    # then
    assert Checkout.objects.count() == checkout_count - 3
    for checkout in [expired_anonymous_checkout, expired_user_checkout, empty_checkout]:
        with pytest.raises(Checkout.DoesNotExist):
            checkout.refresh_from_db()


@pytest.mark.parametrize(
    (
        "authorized",
        "auth_pending",
        "charged",
        "charge_pending",
        "refund_pending",
        "refund",
        "canceled",
        "cancel_pending",
        "expected_checkout_count",
    ),
    [
        (0, 0, 0, 0, 0, 0, 0, 0, 2),
        (1, 0, 0, 0, 0, 0, 0, 0, 5),
        (0, 1, 0, 0, 0, 0, 0, 0, 5),
        (0, 0, 1, 0, 0, 0, 0, 0, 5),
        (0, 0, 0, 1, 0, 0, 0, 0, 5),
        (0, 0, 0, 0, 1, 0, 0, 0, 5),
        # The checkout count is 2 as transaction which is fully refunded can be deleted
        (0, 0, 0, 0, 0, 1, 0, 0, 2),
        # The checkout count is 2 as transaction which is fully canceled can be deleted
        (0, 0, 0, 0, 0, 0, 1, 0, 2),
        (0, 0, 0, 0, 0, 0, 0, 1, 5),
        (1, 1, 1, 1, 1, 1, 1, 1, 5),
    ],
)
def test_delete_expired_checkouts_doesnt_delete_when_transaction_amount_exists(
    authorized,
    auth_pending,
    charged,
    charge_pending,
    refund_pending,
    refund,
    canceled,
    cancel_pending,
    expected_checkout_count,
    checkouts_list,
    customer_user,
    variant,
):
    # given
    now = timezone.now()

    lines_to_create = []
    variant_listings_map = {
        listing.channel_id: listing.price_amount
        for listing in variant.channel_listings.all()
    }

    expired_anonymous_checkout = checkouts_list[0]
    expired_anonymous_checkout.email = None
    expired_anonymous_checkout.created_at = now - datetime.timedelta(days=40)
    expired_anonymous_checkout.last_change = now - datetime.timedelta(days=35)
    lines_to_create.append(
        CheckoutLine(
            checkout=expired_anonymous_checkout,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                expired_anonymous_checkout.channel_id, Decimal("11")
            ),
        )
    )
    expired_anonymous_checkout.payment_transactions.create(
        authorized_value=Decimal(authorized),
        authorize_pending_value=Decimal(auth_pending),
        charged_value=Decimal(charged),
        charge_pending_value=Decimal(charge_pending),
        refund_pending_value=Decimal(refund_pending),
        refunded_value=Decimal(refund),
        canceled_value=Decimal(canceled),
        cancel_pending_value=Decimal(cancel_pending),
    )

    empty_checkout = checkouts_list[1]
    empty_checkout.last_change = now - datetime.timedelta(hours=8)
    assert empty_checkout.lines.count() == 0
    empty_checkout.payment_transactions.create(
        authorized_value=Decimal(authorized),
        authorize_pending_value=Decimal(auth_pending),
        charged_value=Decimal(charged),
        charge_pending_value=Decimal(charge_pending),
        refund_pending_value=Decimal(refund_pending),
        refunded_value=Decimal(refund),
        canceled_value=Decimal(canceled),
        cancel_pending_value=Decimal(cancel_pending),
    )

    expired_user_checkout = checkouts_list[2]
    expired_user_checkout.email = None
    expired_user_checkout.user = customer_user
    expired_user_checkout.created_at = now - datetime.timedelta(days=100)
    expired_user_checkout.last_change = now - datetime.timedelta(days=98)
    lines_to_create.append(
        CheckoutLine(
            checkout=expired_user_checkout,
            variant=variant,
            quantity=1,
            undiscounted_unit_price_amount=variant_listings_map.get(
                expired_user_checkout.channel_id, Decimal("11")
            ),
        )
    )
    expired_user_checkout.payment_transactions.create(
        authorized_value=Decimal(authorized),
        authorize_pending_value=Decimal(auth_pending),
        charged_value=Decimal(charged),
        charge_pending_value=Decimal(charge_pending),
        refund_pending_value=Decimal(refund_pending),
        refunded_value=Decimal(refund),
        canceled_value=Decimal(canceled),
        cancel_pending_value=Decimal(cancel_pending),
    )

    CheckoutLine.objects.bulk_create(lines_to_create)
    Checkout.objects.bulk_update(
        [expired_anonymous_checkout, expired_user_checkout, empty_checkout],
        ["created_at", "last_change", "email", "user"],
    )

    # when
    delete_expired_checkouts()

    # then
    assert Checkout.objects.count() == expected_checkout_count


def test_delete_expired_checkouts_no_checkouts_to_delete(checkout):
    # given
    checkout_count = Checkout.objects.count()

    # when
    delete_expired_checkouts()

    # then
    assert Checkout.objects.count() == checkout_count


@mock.patch("saleor.checkout.tasks.delete_expired_checkouts.delay")
def test_delete_checkouts_until_done(mocked_task: mock.MagicMock, channel_USD):
    """Ensure the task deletes all inactive checkouts from the database.

    Given the settings:
    - Max 2 inactive checkouts to delete per single ``DELETE FROM`` SQL statement
    - A maximum of 3 ``DELETE FROM`` SQL statements may be run per task (totalling
      to a max 6 inactivate checkout/task).

    Database data:
    - 7 inactive checkouts

    The expected flow is:
    1. Deletes 2 checkouts three times (three SQL statement expected)
    2. Triggers a new task due to having still inactive checkouts left to be
       deleted (1 checkout left).
    """

    # Create 7 empty checkouts in DB
    Checkout.objects.bulk_create(
        [
            Checkout(
                currency=channel_USD.currency_code,
                channel=channel_USD,
                token=UUID(int=checkout_id),
            )
            for checkout_id in range(7)
        ]
    )
    Checkout.objects.update(last_change=timezone.now() - datetime.timedelta(hours=7))

    task_params = {
        "batch_size": 2,
        "batch_count": 3,
        "invocation_limit": 10,
    }
    mocked_task.assert_not_called()

    # Delete inactive checkouts.
    deleted_count, has_more = delete_expired_checkouts(
        **task_params, invocation_count=1
    )
    assert deleted_count == 6
    assert has_more is True
    assert (
        Checkout.objects.count() == 1
    ), "Should have deleted 6 checkouts thus only 1 should be left"

    # Should have triggered a new task to delete more checkouts
    mocked_task.assert_called_once_with(**task_params, invocation_count=2)
    mocked_task.reset_mock()

    # Ensure we delete the remaining, and we do not trigger anymore task.
    deleted_count, has_more = delete_expired_checkouts(
        **task_params, invocation_count=2
    )
    assert deleted_count == 1
    assert has_more is False
    assert (
        Checkout.objects.count() == 0
    ), "Should have deleted the last remaining checkout (one)"

    # Shouldn't have triggered a new task as nothing is left to be deleted.
    mocked_task.assert_not_called()


@mock.patch("saleor.checkout.tasks.delete_expired_checkouts.delay")
def test_aborts_deleting_checkouts_when_invocation_count_exhausted(
    mocked_task: mock.MagicMock, channel_USD
):
    """Ensure the Celery task stops triggering tasks when the invocation limit is reached."""

    # Create 3 empty checkouts in DB
    Checkout.objects.bulk_create(
        [
            Checkout(
                currency=channel_USD.currency_code,
                channel=channel_USD,
                token=UUID(int=checkout_id),
            )
            for checkout_id in range(3)
        ]
    )
    Checkout.objects.update(last_change=timezone.now() - datetime.timedelta(hours=7))

    mocked_task.assert_not_called()
    task_params = {
        "batch_size": 1,
        "batch_count": 1,
        "invocation_limit": 2,
    }

    # Invocation #1, should delete 1 checkout
    deleted_count, has_more = delete_expired_checkouts(
        **task_params, invocation_count=1
    )
    assert deleted_count == 1
    assert has_more is True

    # Should have triggered a new task to delete more checkouts
    mocked_task.assert_called_once_with(**task_params, invocation_count=2)
    mocked_task.reset_mock()

    # Invocation #2, should delete 1 checkout and should stop there (has_more=True
    # & no more task.delay()).
    deleted_count, has_more = delete_expired_checkouts(
        **task_params, invocation_count=2
    )
    assert deleted_count == 1
    assert has_more is True

    # Should have stopped there
    mocked_task.assert_not_called()


def test_automatic_checkout_completion_task_transaction_flow(
    checkout_with_prices,
    transaction_item_generator,
    app,
    caplog,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_prices
    checkout_pk = checkout.pk

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout.total.gross.amount
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        automatic_checkout_completion_task(checkout_pk, None, app.id)

    # then
    assert not Checkout.objects.filter(pk=checkout_pk).exists()
    order = Order.objects.filter(checkout_token=checkout_pk).first()
    assert order
    assert order.events.filter(
        type=OrderEvents.PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT
    ).exists()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].message == (
        f"Automatic checkout completion triggered for checkout: {checkout_id}."
    )
    assert caplog.records[0].checkout_id == checkout_id
    assert caplog.records[0].levelno == logging.INFO

    assert caplog.records[1].message == (
        f"Automatic checkout completion succeeded for checkout: {checkout_id}."
    )
    assert caplog.records[1].checkout_id == checkout_id
    assert caplog.records[1].levelno == logging.INFO


def test_automatic_checkout_completion_task_payment_flow(
    checkout_ready_to_complete,
    payment_dummy,
    app,
    caplog,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_ready_to_complete
    checkout_pk = checkout.pk

    checkout.gift_cards.clear()
    checkout.payments.add(payment_dummy)

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    # when
    with django_capture_on_commit_callbacks(execute=True):
        automatic_checkout_completion_task(checkout_pk, None, app.id)

    # then
    assert not Checkout.objects.filter(pk=checkout_pk).exists()
    order = Order.objects.filter(checkout_token=checkout_pk).first()
    assert order
    assert order.events.filter(
        type=OrderEvents.PLACED_AUTOMATICALLY_FROM_PAID_CHECKOUT
    ).exists()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].message == (
        f"Automatic checkout completion triggered for checkout: {checkout_id}."
    )
    assert caplog.records[0].checkout_id == checkout_id
    assert caplog.records[0].levelno == logging.INFO

    assert caplog.records[1].message == (
        f"Automatic checkout completion succeeded for checkout: {checkout_id}."
    )
    assert caplog.records[1].checkout_id == checkout_id
    assert caplog.records[1].levelno == logging.INFO


def test_automatic_checkout_completion_task_missing_checkout(checkout, caplog):
    # given
    checkout_pk = checkout.pk
    checkout.delete()

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    # when
    automatic_checkout_completion_task(checkout_pk, None, None)

    # then
    assert not caplog.records


def test_automatic_checkout_completion_task_unavailable_variant(
    checkout_with_prices,
    transaction_item_generator,
    app,
    caplog,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_prices
    checkout_pk = checkout.pk

    # make the checkout line unavailable
    line = checkout.lines.first()
    variant = line.variant
    product = line.variant.product
    product.channel_listings.update(is_published=False)

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout.total.gross.amount
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        automatic_checkout_completion_task(checkout_pk, None, app.id)

    # then
    assert Checkout.objects.filter(pk=checkout_pk).exists()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        "The automatic checkout completion not triggered, as the checkout "
        f"{checkout_id} contains unavailable variants: {variant_id}."
    )
    assert caplog.records[0].checkout_id == checkout_id
    assert caplog.records[0].levelno == logging.INFO


def test_automatic_checkout_completion_task_error_raised(checkout, app, caplog):
    # given
    checkout_pk = checkout.pk
    checkout.billing_address = None
    checkout.save(update_fields=["billing_address"])

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    # when
    automatic_checkout_completion_task(checkout_pk, None, app.id)

    # then
    assert Checkout.objects.filter(pk=checkout_pk).exists()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)
    assert len(caplog.records) == 2
    assert caplog.records[0].message == (
        f"Automatic checkout completion triggered for checkout: {checkout_id}."
    )
    assert caplog.records[0].checkout_id == checkout_id
    assert caplog.records[0].levelno == logging.INFO

    assert caplog.records[1].message == (
        f"Automatic checkout completion failed for checkout: {checkout_id}."
    )
    assert caplog.records[1].checkout_id == checkout_id
    assert caplog.records[1].error
    assert caplog.records[1].levelno == logging.WARNING
