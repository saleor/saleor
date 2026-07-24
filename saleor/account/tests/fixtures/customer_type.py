import pytest

from ...models import CustomerType

__all__ = ["customer_type", "default_customer_type"]


@pytest.fixture
def customer_type(db):
    return CustomerType.objects.create(name="B2B", slug="b2b")


@pytest.fixture
def default_customer_type(db):
    return CustomerType.objects.get(is_default=True)
