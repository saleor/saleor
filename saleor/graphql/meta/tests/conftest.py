import pytest

PRIVATE_KEY = "private_key"
PRIVATE_VALUE = "private_vale"

PUBLIC_KEY = "key"
PUBLIC_VALUE = "value"


@pytest.fixture
def payment_with_public_metadata(payment):
    payment.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    payment.save(update_fields=["metadata"])
    return payment


@pytest.fixture
def payment_with_private_metadata(payment):
    payment.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    payment.save(update_fields=["private_metadata"])
    return payment
