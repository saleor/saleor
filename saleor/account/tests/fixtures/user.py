from typing import Any

import pytest

from ....account.models import Group, User, UserManager
from ....permission.enums import get_permissions


def dangerously_get_or_create_superuser(
    email: str, password: str | None = None, **extra_fields: Any
) -> tuple[User, bool]:
    """Create a superuser for unittests with the given email and password.

    This should never be called for production use (due to lack of
    validation).
    """
    if user := User.objects.filter(email=email).first():
        return user, False
    user = dangerously_create_test_user(
        email=email, password=password, is_staff=True, is_superuser=True, **extra_fields
    )
    group, group_created = Group.objects.get_or_create(name="Full Access")
    if group_created:
        group.permissions.add(*get_permissions())
    group.user_set.add(user)
    return user, True


def dangerously_create_test_user(
    email, password=None, is_staff=False, is_active=True, **extra_fields
):
    """Create a user for unittests with the given email and password.

    This should never be called for production use (due to lack of
    validation).
    """
    email = UserManager.normalize_email(email)
    # Google OAuth2 backend send unnecessary username field
    extra_fields.pop("username", None)

    user = User(email=email, is_active=is_active, is_staff=is_staff, **extra_fields)
    if password:
        # Semgrep rule that verifies whether the user's password is validated before
        # calling `user.set_password()` is being silenced due to this function being
        # voluntarily insecure and being dedicated for unit-testing only.
        # We might change that in the future by requiring tests to always provide
        # a strong password.
        # For now, it's wrapped around a function name "dangerously_[...]" and being
        # put inside a 'tests' namespace (saleor.account.tests.fixtures.user)
        # in order to minimize as much as possible the risk of someone using that
        # insecure function.
        user.set_password(  # nosemgrep: python.django.security.audit.unvalidated-password.unvalidated-password
            password
        )
    user.save()
    return user


@pytest.fixture
def customer_user(address):  # pylint: disable=W0613
    default_address = address.get_copy()
    user = dangerously_create_test_user(
        "test@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Leslie",
        last_name="Wade",
        external_reference="LeslieWade",
        metadata={"key": "value"},
        private_metadata={"secret_key": "secret_value"},
    )
    user.addresses.add(default_address)
    user._password = "password"
    return user


@pytest.fixture
def customer_user2(address):
    default_address = address.get_copy()
    user = dangerously_create_test_user(
        "test2@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Jane",
        last_name="Doe",
        external_reference="JaneDoe",
    )
    user.addresses.add(default_address)
    user._password = "password"
    return user


@pytest.fixture
def customer_users(address, customer_user, customer_user2):
    default_address = address.get_copy()
    customer_user3 = dangerously_create_test_user(
        "test3@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Chris",
        last_name="Duck",
    )
    customer_user3.addresses.add(default_address)
    customer_user3._password = "password"

    return [customer_user, customer_user2, customer_user3]


@pytest.fixture
def admin_user(db):
    """Return a Django admin user."""
    return dangerously_create_test_user(
        "admin@example.com",
        "password",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )


@pytest.fixture
def staff_user(db):
    """Return a staff member."""
    return dangerously_create_test_user(
        email="staff_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )


@pytest.fixture
def staff_users(staff_user):
    """Return a staff members."""
    staff_users = User.objects.bulk_create(
        [
            User(
                email="staff1_test@example.com",
                password="password",
                is_staff=True,
                is_active=True,
            ),
            User(
                email="staff2_test@example.com",
                password="password",
                is_staff=True,
                is_active=True,
            ),
        ]
    )
    return [staff_user] + staff_users
