import pytest

from ...models import CustomerType

__all__ = [
    "customer_type",
    "customer_type_with_attributes",
    "default_customer_type",
]


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


@pytest.fixture
def default_customer_type(db):
    return CustomerType.objects.get(is_default=True)
