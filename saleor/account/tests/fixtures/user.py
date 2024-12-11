import pytest

from ....account.models import User


@pytest.fixture
def customer_user(address):  # pylint: disable=W0613
    default_address = address.get_copy()
    user = User.objects.create_user(
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
    user = User.objects.create_user(
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
    customer_user3 = User.objects.create_user(
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
    return User.objects.create_user(
        "admin@example.com",
        "password",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )


@pytest.fixture
def staff_user(db):
    """Return a staff member."""
    return User.objects.create_user(
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
