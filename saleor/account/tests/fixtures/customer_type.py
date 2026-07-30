import pytest

from ...models import CustomerType

__all__ = [
    "customer_type",
    "customer_type_with_attributes",
    "default_customer_type",
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
