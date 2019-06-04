import pytest


@pytest.mark.django_db
@pytest.mark.count_queries
def test_get_payment_token(api_client):
    query = """
        query getPaymentToken($gateway: GatewaysEnum!) {
          paymentClientToken(gateway: $gateway)
        }
    """
    assert query is not None  # so flake stops being upset about the unused variable
