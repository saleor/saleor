from datetime import timedelta
from unittest import mock
from uuid import UUID

import pytest
from django.utils import timezone

from ..models import Checkout
from ..tasks import delete_expired_checkouts


def test_delete_expired_anonymous_checkouts(checkouts_list, variant, customer_user):
    # given
    now = timezone.now()
    checkout_count = Checkout.objects.count()

    expired_anonymous_checkout = checkouts_list[0]
    expired_anonymous_checkout.email = None
    expired_anonymous_checkout.user = None
    expired_anonymous_checkout.created_at = now - timedelta(days=40)
    expired_anonymous_checkout.last_change = now - timedelta(days=35)
    expired_anonymous_checkout.lines.create(
        checkout=expired_anonymous_checkout, variant=variant, quantity=1
    )

    not_expired_checkout_1 = checkouts_list[1]
    not_expired_checkout_1.email = None
    not_expired_checkout_1.user = None
    not_expired_checkout_1.created_at = now - timedelta(days=35)
    not_expired_checkout_1.last_change = now - timedelta(days=29)
    not_expired_checkout_1.lines.create(
        checkout=not_expired_checkout_1, variant=variant, quantity=1
    )

    not_expired_checkout_2 = checkouts_list[2]
    not_expired_checkout_2.email = None
    not_expired_checkout_2.user = customer_user
    not_expired_checkout_2.created_at = now - timedelta(days=45)
    not_expired_checkout_2.last_change = now - timedelta(days=40)
    not_expired_checkout_2.lines.create(
        checkout=not_expired_checkout_2, variant=variant, quantity=1
    )

    not_expired_checkout_3 = checkouts_list[3]
    not_expired_checkout_3.email = "test@example.com"
    not_expired_checkout_3.user = None
    not_expired_checkout_3.created_at = now - timedelta(days=45)
    not_expired_checkout_3.last_change = now - timedelta(days=40)
    not_expired_checkout_3.lines.create(
        checkout=not_expired_checkout_3, variant=variant, quantity=1
    )

    empty_checkout = checkouts_list[4]
    empty_checkout.last_change = now - timedelta(hours=8)
    assert empty_checkout.lines.count() == 0

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

    expired_user_checkout_1 = checkouts_list[0]
    expired_user_checkout_1.email = None
    expired_user_checkout_1.user = customer_user
    expired_user_checkout_1.created_at = now - timedelta(days=100)
    expired_user_checkout_1.last_change = now - timedelta(days=98)
    expired_user_checkout_1.lines.create(
        checkout=expired_user_checkout_1, variant=variant, quantity=1
    )

    expired_user_checkout_2 = checkouts_list[1]
    expired_user_checkout_2.email = "test@example.com"
    expired_user_checkout_2.user = None
    expired_user_checkout_2.created_at = now - timedelta(days=100)
    expired_user_checkout_2.last_change = now - timedelta(days=91)
    expired_user_checkout_2.lines.create(
        checkout=expired_user_checkout_2, variant=variant, quantity=1
    )

    not_expired_checkout_1 = checkouts_list[2]
    not_expired_checkout_1.email = None
    not_expired_checkout_1.user = None
    not_expired_checkout_1.created_at = now - timedelta(days=35)
    not_expired_checkout_1.last_change = now - timedelta(days=29)
    not_expired_checkout_1.lines.create(
        checkout=not_expired_checkout_1, variant=variant, quantity=1
    )

    not_expired_checkout_2 = checkouts_list[3]
    not_expired_checkout_2.email = "test@example.com"
    not_expired_checkout_2.user = None
    not_expired_checkout_2.created_at = now - timedelta(days=100)
    not_expired_checkout_2.last_change = now - timedelta(days=60)
    not_expired_checkout_2.lines.create(
        checkout=not_expired_checkout_2, variant=variant, quantity=1
    )

    not_expired_checkout_3 = checkouts_list[4]
    not_expired_checkout_3.email = None
    not_expired_checkout_3.user = customer_user
    not_expired_checkout_3.created_at = now - timedelta(days=100)
    not_expired_checkout_3.last_change = now - timedelta(days=89)
    not_expired_checkout_3.lines.create(
        checkout=not_expired_checkout_3, variant=variant, quantity=1
    )

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
    empty_checkout_1.last_change = now - timedelta(hours=8)
    assert empty_checkout_1.lines.count() == 0

    empty_checkout_2 = checkouts_list[1]
    empty_checkout_2.email = "test@example.com"
    empty_checkout_2.user = customer_user
    empty_checkout_2.last_change = now - timedelta(hours=8)
    assert empty_checkout_2.lines.count() == 0

    empty_checkout_3 = checkouts_list[2]
    empty_checkout_3.last_change = now - timedelta(hours=2)
    assert empty_checkout_3.lines.count() == 0

    not_empty_checkout = checkouts_list[3]
    not_empty_checkout.last_change = now - timedelta(days=2)
    not_empty_checkout.lines.create(
        checkout=not_empty_checkout, variant=variant, quantity=1
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

    expired_anonymous_checkout = checkouts_list[0]
    expired_anonymous_checkout.email = None
    expired_anonymous_checkout.created_at = now - timedelta(days=40)
    expired_anonymous_checkout.last_change = now - timedelta(days=35)
    expired_anonymous_checkout.lines.create(
        checkout=expired_anonymous_checkout, variant=variant, quantity=1
    )

    expired_user_checkout = checkouts_list[2]
    expired_user_checkout.user = customer_user
    expired_user_checkout.created_at = now - timedelta(days=100)
    expired_user_checkout.last_change = now - timedelta(days=95)
    expired_user_checkout.lines.create(
        checkout=expired_user_checkout, variant=variant, quantity=1
    )

    empty_checkout = checkouts_list[4]
    empty_checkout.last_change = now - timedelta(hours=8)
    assert empty_checkout.lines.count() == 0

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


def test_delete_expired_checkouts_no_checkouts_to_delete(checkout):
    # given
    checkout_count = Checkout.objects.count()

    # when
    delete_expired_checkouts()

    # then
    assert Checkout.objects.count() == checkout_count


@mock.patch("saleor.checkout.tasks.delete_expired_checkouts.delay")
def test_delete_checkouts_until_done(mocked_task: mock.MagicMock, channel_USD):
    """
    Ensure the Celery task ``delete_expired_checkouts`` deletes all inactive
    checkouts from the database until there are none left to delete.

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
    Checkout.objects.update(last_change=timezone.now() - timedelta(hours=7))

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
    """
    Ensure the Celery task stops triggering tasks when the invocation limit is reached.
    """

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
    Checkout.objects.update(last_change=timezone.now() - timedelta(hours=7))

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
