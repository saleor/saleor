import pytest

from ....attribute.models import AssignedUserAttributeValue, AttributeValue
from ...models import CustomerType

__all__ = [
    "b2b_customer_user",
    "customer_type",
    "customer_type_with_attributes",
    "default_customer_type",
    "gold_customer_user",
    "get_or_create_default_customer_type",
]


def get_or_create_default_customer_type() -> CustomerType:
    # Transactional tests (django_db(transaction=True)) flush all tables on
    # teardown, wiping the default customer type created by the data migration,
    # so recreate it on demand instead of assuming the migration row exists.
    customer_type, _ = CustomerType.objects.get_or_create(
        is_default=True,
        defaults={"name": "Default", "slug": "default"},
    )
    return customer_type


@pytest.fixture
def customer_type(db):
    return CustomerType.objects.create(name="B2B", slug="b2b")


@pytest.fixture
def customer_type_with_attributes(
    customer_type,
    loyalty_customer_attribute,
    description_customer_attribute,
    hidden_customer_attribute,
):
    customer_type.customer_attributes.add(
        loyalty_customer_attribute,
        description_customer_attribute,
        hidden_customer_attribute,
    )
    return customer_type


@pytest.fixture(autouse=True)
def default_customer_type(db):
    return get_or_create_default_customer_type()


@pytest.fixture
def b2b_customer_user(customer_user, customer_type):
    """Return the customer as a member of the B2B customer type."""
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])
    return customer_user


@pytest.fixture
def gold_customer_user(b2b_customer_user, customer_type_with_attributes):
    """Return a B2B customer holding the gold loyalty level.

    The loyalty attribute is assigned to the B2B type, so the value is visible
    through the customer type membership guard.
    """
    gold_value = AttributeValue.objects.get(
        attribute__slug="loyalty-level", slug="gold"
    )
    AssignedUserAttributeValue.objects.create(user=b2b_customer_user, value=gold_value)
    return b2b_customer_user
