import pytest
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from ..exceptions import NoDefaultCustomerType
from ..migrations.tasks.saleor3_23 import assign_default_customer_type_to_users_task
from ..models import CustomerType, User
from ..utils import get_default_customer_type


@pytest.mark.django_db
def test_default_customer_type_is_seeded():
    # given the data migration ran

    # when
    default_type = CustomerType.objects.get(is_default=True)

    # then
    assert default_type.name == "Default"
    assert default_type.slug == "default"


def test_get_default_customer_type_returns_default_type(
    customer_type, default_customer_type
):
    # given a non-default type existing alongside the default one

    # when
    result = get_default_customer_type()

    # then
    assert result == default_customer_type
    assert result != customer_type


@pytest.mark.django_db
def test_get_default_customer_type_raises_when_default_is_missing():
    # given
    CustomerType.objects.all().delete()

    # when / then
    with pytest.raises(NoDefaultCustomerType):
        get_default_customer_type()


def test_second_default_customer_type_is_rejected(default_customer_type):
    # given
    assert CustomerType.objects.filter(is_default=True).exists() is True

    # when / then
    with pytest.raises(IntegrityError):
        CustomerType.objects.create(name="Other", slug="other", is_default=True)


@pytest.mark.django_db
def test_multiple_non_default_customer_types_are_allowed():
    # when
    CustomerType.objects.create(name="B2B", slug="b2b")
    CustomerType.objects.create(name="B2C", slug="b2c")

    # then
    assert CustomerType.objects.filter(is_default=False).count() == 2


def test_deleting_customer_type_assigned_to_user_is_protected(
    customer_user, customer_type
):
    # given
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])

    # when / then
    with pytest.raises(ProtectedError):
        customer_type.delete()


def test_assign_default_customer_type_task_backfills_users_without_type(
    customer_user, customer_user2, default_customer_type
):
    # given
    assert customer_user.customer_type is None
    assert customer_user2.customer_type is None

    # when
    assign_default_customer_type_to_users_task()

    # then
    customer_user.refresh_from_db()
    customer_user2.refresh_from_db()
    assert customer_user.customer_type == default_customer_type
    assert customer_user2.customer_type == default_customer_type


def test_assign_default_customer_type_task_keeps_existing_assignments(
    customer_user, customer_user2, customer_type, default_customer_type
):
    # given
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])

    # when
    assign_default_customer_type_to_users_task()

    # then
    customer_user.refresh_from_db()
    customer_user2.refresh_from_db()
    assert customer_user.customer_type == customer_type
    assert customer_user2.customer_type == default_customer_type


def test_assign_default_customer_type_task_processes_all_batches(
    customer_user, customer_user2, staff_user, default_customer_type, monkeypatch
):
    # given a batch size smaller than the number of users to backfill
    monkeypatch.setattr(
        "saleor.account.migrations.tasks.saleor3_23"
        ".ASSIGN_DEFAULT_CUSTOMER_TYPE_BATCH_SIZE",
        1,
    )

    # when the task self-chains (celery runs eagerly in tests)
    assign_default_customer_type_to_users_task()

    # then
    assert User.objects.filter(customer_type__isnull=True).count() == 0
    customer_user.refresh_from_db()
    staff_user.refresh_from_db()
    assert customer_user.customer_type == default_customer_type
    assert staff_user.customer_type == default_customer_type


@pytest.mark.django_db
def test_assign_default_customer_type_task_raises_when_default_is_missing():
    # given
    CustomerType.objects.all().delete()

    # when / then
    with pytest.raises(NoDefaultCustomerType):
        assign_default_customer_type_to_users_task()
