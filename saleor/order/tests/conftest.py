import pytest

from saleor.payment import TransactionKind


@pytest.fixture()
def mock_refund_response():
    def fun(mocked_fun):
        def _side_effect(payment, manager, amount, *args, **kwargs):
            return payment.transactions.create(
                is_success=True,
                kind=TransactionKind.REFUND,
                amount=amount,
                currency=payment.currency,
                gateway_response={},
            )

        mocked_fun.side_effect = _side_effect

    return fun
