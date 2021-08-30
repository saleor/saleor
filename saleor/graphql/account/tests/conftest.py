from typing import List

import pytest

from saleor.payment.interface import CustomerSource


@pytest.fixture
def customer_sources() -> List[CustomerSource]:
    return [
        CustomerSource(
            id=f"CustomerSource:{i}",
            gateway="mirumee.payments.dummy",
        )
        for i in range(5)
    ]
