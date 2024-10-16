from decimal import Decimal

import graphene
import pytest

from ....payment.interface import PaymentData


@pytest.fixture
def dummy_payment_data(payment_dummy):
    return PaymentData(
        gateway=payment_dummy.gateway,
        amount=Decimal(10),
        currency="USD",
        graphql_payment_id=graphene.Node.to_global_id("Payment", payment_dummy.pk),
        payment_id=payment_dummy.pk,
        billing=None,
        shipping=None,
        order_id=None,
        customer_ip_address=None,
        customer_email="example@test.com",
    )
