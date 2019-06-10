from django.conf import settings

from tests.api.utils import get_graphql_content


def test_get_payment_token(api_client, django_assert_num_queries):
    """This test ensures getting a gateway does not generate any queries."""
    query = """
        query getPaymentToken($gateway: GatewaysEnum!) {
          paymentClientToken(gateway: $gateway)
        }
    """
    variables = {"gateway": settings.DUMMY.upper()}
    with django_assert_num_queries(0):
        get_graphql_content(api_client.post_graphql(query, variables))
