from datetime import timedelta

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
        [
            empty_checkout_1,
            empty_checkout_2,
            empty_checkout_3,
            not_empty_checkout,
        ],
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
        [
            expired_anonymous_checkout,
            expired_user_checkout,
            empty_checkout,
        ],
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
