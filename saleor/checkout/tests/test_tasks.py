import datetime
import logging
from decimal import Decimal
from unittest import mock
from uuid import UUID

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from ...channel.models import Channel
from ...order import OrderEvents
from ...order.models import Order
from ...product.models import ProductChannelListing, ProductVariantChannelListing
from .. import CheckoutAuthorizeStatus
from ..models import Checkout, CheckoutLine
from ..tasks import (
    automatic_checkout_completion_task,
    delete_expired_checkouts,
    task_logger,
    trigger_automatic_checkout_completion_task,
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
                expired_anonymous_checkout.channel_id, Decimal(11)
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
                not_expired_checkout_1.channel_id, Decimal(11)
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
                not_expired_checkout_2.channel_id, Decimal(11)
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
                not_expired_checkout_3.channel_id, Decimal(11)
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
                expired_user_checkout_1.channel_id, Decimal(11)
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
                expired_user_checkout_2.channel_id, Decimal(11)
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
                not_expired_checkout_1.channel_id, Decimal(11)
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
                not_expired_checkout_2.channel_id, Decimal(11)
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
                not_expired_checkout_3.channel_id, Decimal(11)
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
                expired_anonymous_checkout.channel_id, Decimal(11)
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
                expired_user_checkout.channel_id, Decimal(11)
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
                expired_anonymous_checkout.channel_id, Decimal(11)
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
                expired_user_checkout.channel_id, Decimal(11)
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
    assert Checkout.objects.count() == 1, (
        "Should have deleted 6 checkouts thus only 1 should be left"
    )

    # Should have triggered a new task to delete more checkouts
    mocked_task.assert_called_once_with(**task_params, invocation_count=2)
    mocked_task.reset_mock()

    # Ensure we delete the remaining, and we do not trigger anymore task.
    deleted_count, has_more = delete_expired_checkouts(
        **task_params, invocation_count=2
    )
    assert deleted_count == 1
    assert has_more is False
    assert Checkout.objects.count() == 0, (
        "Should have deleted the last remaining checkout (one)"
    )

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


def test_automatic_checkout_completion_transaction_flow(
    checkout_with_prices,
    transaction_item_generator,
    app,
    caplog,
    django_capture_on_commit_callbacks,
    warehouse_for_cc,
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
        automatic_checkout_completion_task(checkout.pk)

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


def test_automatic_checkout_completion_payment_flow(
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
        automatic_checkout_completion_task(checkout.pk)

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


def test_automatic_checkout_completion_missing_checkout(checkout, caplog):
    # given
    checkout.delete()

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    # when
    automatic_checkout_completion_task(checkout.pk)

    # then
    assert not caplog.records


def test_automatic_checkout_completion_unavailable_variant(
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
        automatic_checkout_completion_task(checkout.pk)

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


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_automatic_checkout_completion_line_without_listing(
    channel_listing_model,
    listing_filter_field,
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

    channel_listing_model.objects.filter(
        channel_id=checkout.channel_id,
        **{listing_filter_field: variant.id},
    ).delete()

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout.total.gross.amount
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        automatic_checkout_completion_task(checkout.pk)

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


def test_automatic_checkout_completion_error_raised(
    checkout_with_item, app, caplog, checkout_delivery
):
    # given
    checkout = checkout_with_item
    checkout_pk = checkout.pk
    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.save(update_fields=["assigned_delivery"])

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    # when
    automatic_checkout_completion_task(checkout.pk)

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


def test_automatic_checkout_completion_missing_lines(
    checkout_with_prices,
    transaction_item_generator,
    app,
    caplog,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_prices
    checkout_pk = checkout.pk

    # delete lines
    checkout.lines.all().delete()

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout.total.gross.amount
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        automatic_checkout_completion_task(checkout.pk)

    # then
    assert Checkout.objects.filter(pk=checkout_pk).exists()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        "The automatic checkout completion not triggered, as the checkout "
        f"{checkout_id} has no lines."
    )
    assert caplog.records[0].checkout_id == checkout_id
    assert caplog.records[0].levelno == logging.INFO


def test_automatic_checkout_completion_missing_delivery_method(
    checkout_with_prices,
    transaction_item_generator,
    app,
    caplog,
    django_capture_on_commit_callbacks,
):
    # given
    checkout = checkout_with_prices
    checkout.shipping_method = None
    checkout.collection_point = None
    checkout.assigned_delivery = None
    checkout.save(
        update_fields=["shipping_method", "collection_point", "assigned_delivery"]
    )
    checkout_pk = checkout.pk

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout.total.gross.amount
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        automatic_checkout_completion_task(checkout.pk)

    # then
    assert Checkout.objects.filter(pk=checkout_pk).exists()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout_pk)
    assert len(caplog.records) == 1
    assert caplog.records[0].message == (
        "The automatic checkout completion not triggered, as the checkout "
        f"{checkout_id} has no shipping method set."
    )
    assert caplog.records[0].checkout_id == checkout_id
    assert caplog.records[0].levelno == logging.INFO


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
def test_trigger_automatic_checkout_completion_task_no_channels(
    mocked_automatic_checkout_completion,
    caplog,
    checkouts_list,
):
    # given
    Channel.objects.all().update(automatically_complete_fully_paid_checkouts=False)
    Checkout.objects.update(authorize_status=CheckoutAuthorizeStatus.FULL)

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert not mocked_automatic_checkout_completion.called
    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message
        == "No channels configured for automatic checkout completion."
    )
    assert caplog.records[0].levelno == logging.INFO


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_no_eligible_checkouts(
    mocked_automatic_checkout_completion, channel_USD, caplog, checkouts_list
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    # allow catching the log in caplog
    parent_logger = task_logger.parent
    parent_logger.propagate = True

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert not mocked_automatic_checkout_completion.called
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "No checkouts found for automatic completion."
    assert caplog.records[0].levelno == logging.INFO


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_with_eligible_checkouts(
    mocked_automatic_checkout_completion,
    checkout_with_prices,
    channel_USD,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    Checkout.objects.update(
        authorize_status=CheckoutAuthorizeStatus.FULL,
        last_change=timezone.now() - datetime.timedelta(minutes=7),
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert mocked_automatic_checkout_completion.call_count == 1
    mocked_automatic_checkout_completion.assert_called_once_with(
        args=[checkout_with_prices.token],
        kwargs={},
        headers={"MessageGroupId": mock.ANY},
    )


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_checkout_not_eligible_due_to_delay(
    mocked_automatic_checkout_completion,
    checkout_with_prices,
    channel_USD,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 10
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    Checkout.objects.update(
        authorize_status=CheckoutAuthorizeStatus.FULL,
        last_change=timezone.now() - datetime.timedelta(minutes=5),
        channel=channel_USD,
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert not mocked_automatic_checkout_completion.called


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_checkout_too_old(
    mocked_automatic_checkout_completion,
    checkout_with_prices,
    channel_USD,
    settings,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    checkout = checkout_with_prices
    # Older than the threshold defined in settings
    Checkout.objects.filter(pk=checkout.pk).update(
        last_change=timezone.now()
        - (
            settings.AUTOMATIC_CHECKOUT_COMPLETION_OLDEST_MODIFIED
            + datetime.timedelta(days=1)
        ),
        authorize_status=CheckoutAuthorizeStatus.FULL,
        channel=channel_USD,
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert not mocked_automatic_checkout_completion.called


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_checkout_not_eligible_due_missing_billing_address(
    mocked_automatic_checkout_completion,
    checkout_with_prices,
    channel_USD,
    shipping_method,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    Checkout.objects.update(
        authorize_status=CheckoutAuthorizeStatus.FULL,
        last_change=timezone.now() - datetime.timedelta(minutes=7),
        email="test@email.com",
        billing_address=None,
        shipping_method=shipping_method,
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert not mocked_automatic_checkout_completion.called


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_checkout_not_eligible_due_missing_email_or_user(
    mocked_automatic_checkout_completion,
    checkout_with_prices,
    channel_USD,
    address,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    Checkout.objects.update(
        authorize_status=CheckoutAuthorizeStatus.FULL,
        last_change=timezone.now() - datetime.timedelta(minutes=7),
        billing_address=address,
        email=None,
        user=None,
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert not mocked_automatic_checkout_completion.called


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_checkout_not_eligible_due_total_0(
    mocked_automatic_checkout_completion,
    checkout_with_prices,
    channel_USD,
    shipping_method,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    Checkout.objects.update(
        authorize_status=CheckoutAuthorizeStatus.FULL,
        last_change=timezone.now() - datetime.timedelta(minutes=7),
        total_gross_amount=Decimal("0.00"),
        total_net_amount=Decimal("0.00"),
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert not mocked_automatic_checkout_completion.called


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
@pytest.mark.parametrize("batch_size", [1, 2, 5])
def test_trigger_automatic_checkout_completion_task_respects_batch_size(
    mocked_automatic_checkout_completion,
    checkouts_list,
    channel_USD,
    batch_size,
    shipping_method,
    address,
):
    # given

    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    amount = Decimal("10.00")
    Checkout.objects.update(
        authorize_status=CheckoutAuthorizeStatus.FULL,
        billing_address=address,
        email="test@email.com",
        channel=channel_USD,
        last_change=timezone.now() - datetime.timedelta(minutes=10),
        shipping_method=shipping_method,
        total_gross_amount=amount,
        total_net_amount=amount,
    )

    # when
    with mock.patch(
        "saleor.checkout.tasks.AUTOMATIC_COMPLETION_BATCH_SIZE", batch_size
    ):
        trigger_automatic_checkout_completion_task()

    # then
    # Should only process the specified batch of checkouts
    assert mocked_automatic_checkout_completion.call_count == batch_size


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_prioritizes_never_attempted(
    mocked_automatic_checkout_completion,
    checkouts_list,
    channel_USD,
    address,
    checkout_delivery,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
        ]
    )

    # Create checkouts with different last_automatic_completion_attempt times
    never_attempted = checkouts_list[0]
    attempted_recently = checkouts_list[1]

    never_attempted.channel = channel_USD
    never_attempted.authorize_status = CheckoutAuthorizeStatus.FULL
    never_attempted.last_change = timezone.now() - datetime.timedelta(minutes=10)
    never_attempted.last_automatic_completion_attempt = None
    never_attempted.email = "test@email.com"
    never_attempted.billing_address = address
    never_attempted.assigned_delivery = checkout_delivery(never_attempted)
    never_attempted.total_gross_amount = Decimal("10.00")
    never_attempted.total_net_amount = Decimal("8.00")

    attempted_recently.channel = channel_USD
    attempted_recently.authorize_status = CheckoutAuthorizeStatus.FULL
    attempted_recently.last_change = timezone.now() - datetime.timedelta(minutes=10)
    attempted_recently.last_automatic_completion_attempt = (
        timezone.now() - datetime.timedelta(minutes=2)
    )
    attempted_recently.email = "test@email.com"
    attempted_recently.billing_address = address
    attempted_recently.assigned_delivery = checkout_delivery(attempted_recently)
    attempted_recently.total_gross_amount = Decimal("10.00")
    attempted_recently.total_net_amount = Decimal("8.00")

    Checkout.objects.bulk_update(
        [never_attempted, attempted_recently],
        [
            "authorize_status",
            "last_change",
            "last_automatic_completion_attempt",
            "channel",
            "billing_address",
            "email",
            "assigned_delivery",
            "total_gross_amount",
            "total_net_amount",
        ],
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert mocked_automatic_checkout_completion.call_count == 2
    # Never attempted should be processed first
    assert (
        mocked_automatic_checkout_completion.call_args_list[0][1]["args"][0]
        == never_attempted.pk
    )


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_multiple_channels(
    mocked_automatic_checkout_completion,
    checkouts_list,
    channel_USD,
    channel_PLN,
    address,
    checkout_delivery,
    shipping_method_channel_PLN,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5

    channel_PLN.automatically_complete_fully_paid_checkouts = True
    channel_PLN.automatic_completion_delay = 10
    Channel.objects.bulk_update(
        [channel_USD, channel_PLN],
        ["automatically_complete_fully_paid_checkouts", "automatic_completion_delay"],
    )

    # Prepare checkouts for bulk update
    checkout_usd = checkouts_list[0]
    checkout_usd.channel = channel_USD
    checkout_usd.authorize_status = CheckoutAuthorizeStatus.FULL
    checkout_usd.assigned_delivery = checkout_delivery(checkout_usd)
    checkout_usd.billing_address = address
    checkout_usd.email = "test@email.com"
    checkout_usd.total_gross_amount = Decimal("10.00")
    checkout_usd.total_net_amount = Decimal("8.00")
    checkout_usd.last_change = timezone.now() - datetime.timedelta(minutes=10)

    checkout_pln = checkouts_list[1]
    checkout_pln.channel = channel_PLN
    checkout_pln.authorize_status = CheckoutAuthorizeStatus.FULL
    checkout_pln.assigned_delivery = checkout_delivery(
        checkout_pln, shipping_method_channel_PLN
    )
    checkout_pln.billing_address = address
    checkout_pln.email = "test@email.com"
    checkout_pln.total_gross_amount = Decimal("0.5")
    checkout_pln.total_net_amount = Decimal("0.5")
    checkout_pln.last_change = timezone.now() - datetime.timedelta(minutes=15)

    checkout_pln_not_ready = checkouts_list[2]
    checkout_pln_not_ready.channel = channel_PLN
    checkout_pln_not_ready.assigned_delivery = checkout_delivery(
        checkout_pln_not_ready, shipping_method_channel_PLN
    )
    checkout_pln_not_ready.billing_address = address
    checkout_pln_not_ready.email = "test@email.com"
    checkout_pln_not_ready.total_gross_amount = Decimal("1.00")
    checkout_pln_not_ready.total_net_amount = Decimal("1.00")
    checkout_pln_not_ready.authorize_status = CheckoutAuthorizeStatus.FULL

    Checkout.objects.bulk_update(
        [checkout_usd, checkout_pln, checkout_pln_not_ready],
        [
            "channel",
            "authorize_status",
            "last_change",
            "assigned_delivery",
            "billing_address",
            "email",
            "total_gross_amount",
            "total_net_amount",
        ],
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert mocked_automatic_checkout_completion.call_count == 2
    called_checkouts = [
        call.kwargs["args"][0]
        for call in mocked_automatic_checkout_completion.call_args_list
    ]
    assert checkout_usd.pk in called_checkouts
    assert checkout_pln.pk in called_checkouts
    assert checkout_pln_not_ready.pk not in called_checkouts


@mock.patch("saleor.checkout.tasks.automatic_checkout_completion_task.apply_async")
@freeze_time("2024-05-31 12:00:01")
def test_trigger_automatic_checkout_completion_task_with_cut_off_date(
    mocked_automatic_checkout_completion,
    checkouts_list,
    channel_USD,
    address,
    checkout_delivery,
):
    # given
    channel_USD.automatically_complete_fully_paid_checkouts = True
    channel_USD.automatic_completion_delay = 5
    channel_USD.automatic_completion_cut_off_date = timezone.now() - datetime.timedelta(
        days=10
    )
    channel_USD.save(
        update_fields=[
            "automatically_complete_fully_paid_checkouts",
            "automatic_completion_delay",
            "automatic_completion_cut_off_date",
        ]
    )

    eligible_checkout = checkouts_list[0]
    eligible_checkout.channel = channel_USD
    eligible_checkout.authorize_status = CheckoutAuthorizeStatus.FULL
    eligible_checkout.last_change = timezone.now() - datetime.timedelta(minutes=15)
    eligible_checkout.created_at = timezone.now() - datetime.timedelta(days=5)
    eligible_checkout.email = "test@email.com"
    eligible_checkout.billing_address = address
    eligible_checkout.assigned_delivery = checkout_delivery(eligible_checkout)
    eligible_checkout.total_gross_amount = Decimal("10.00")
    eligible_checkout.total_net_amount = Decimal("8.00")

    ineligible_checkout_due_to_cut_off = checkouts_list[1]
    ineligible_checkout_due_to_cut_off.channel = channel_USD
    ineligible_checkout_due_to_cut_off.authorize_status = CheckoutAuthorizeStatus.FULL
    ineligible_checkout_due_to_cut_off.last_change = (
        timezone.now() - datetime.timedelta(minutes=15)
    )
    ineligible_checkout_due_to_cut_off.email = "test@email.com"
    ineligible_checkout_due_to_cut_off.billing_address = address
    ineligible_checkout_due_to_cut_off.assigned_delivery = checkout_delivery(
        ineligible_checkout_due_to_cut_off
    )
    ineligible_checkout_due_to_cut_off.total_gross_amount = Decimal("10.00")
    ineligible_checkout_due_to_cut_off.total_net_amount = Decimal("8.00")
    ineligible_checkout_due_to_cut_off.created_at = timezone.now() - datetime.timedelta(
        days=15
    )

    Checkout.objects.bulk_update(
        [eligible_checkout, ineligible_checkout_due_to_cut_off],
        [
            "channel",
            "authorize_status",
            "last_change",
            "created_at",
            "email",
            "billing_address",
            "assigned_delivery",
            "total_gross_amount",
            "total_net_amount",
        ],
    )

    # when
    trigger_automatic_checkout_completion_task()

    # then
    assert mocked_automatic_checkout_completion.call_count == 1
    called_checkouts = [
        call.kwargs["args"][0]
        for call in mocked_automatic_checkout_completion.call_args_list
    ]
    assert eligible_checkout.pk in called_checkouts
    assert ineligible_checkout_due_to_cut_off.pk not in called_checkouts
