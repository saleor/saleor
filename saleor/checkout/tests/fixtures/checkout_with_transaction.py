from decimal import Decimal

import pytest

from ....payment.models import TransactionItem


@pytest.fixture
def checkout_with_item_and_transaction_item(checkout_with_item):
    TransactionItem.objects.create(
        name="Credit card",
        psp_reference="PSP ref",
        available_actions=["refund"],
        currency="USD",
        checkout_id=checkout_with_item.pk,
        charged_value=Decimal("10"),
    )
    return checkout_with_item
