import pytest
from django.conf import settings

from tests.api.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_get_payment_token(count_queries, api_client):
    query = """
        query getPaymentToken($gateway: GatewaysEnum!) {
          paymentClientToken(gateway: $gateway)
        }
    """
    variables = {"gateway": settings.DUMMY.upper()}
    get_graphql_content(api_client.post_graphql(query, variables))
