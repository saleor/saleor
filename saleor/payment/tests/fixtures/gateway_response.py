from decimal import Decimal

import pytest

from ....payment import TransactionKind
from ....payment.interface import GatewayResponse


@pytest.fixture
def action_required_gateway_response():
    return GatewayResponse(
        is_success=True,
        action_required=True,
        action_required_data={
            "paymentData": "test",
            "paymentMethodType": "scheme",
            "url": "https://test.adyen.com/hpp/3d/validate.shtml",
            "data": {
                "MD": "md-test-data",
                "PaReq": "PaReq-test-data",
                "TermUrl": "http://127.0.0.1:3000/",
            },
            "method": "POST",
            "type": "redirect",
        },
        kind=TransactionKind.CAPTURE,
        amount=Decimal(3.0),
        currency="usd",
        transaction_id="1234",
        error=None,
    )


@pytest.fixture
def success_gateway_response():
    return GatewayResponse(
        is_success=True,
        action_required=False,
        action_required_data={},
        kind=TransactionKind.CAPTURE,
        amount=Decimal("10.0"),
        currency="usd",
        transaction_id="1234",
        error=None,
    )
