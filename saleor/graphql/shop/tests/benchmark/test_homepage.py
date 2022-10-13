import pytest

from ....order.tests.benchmark.test_order import FRAGMENT_SHIPPING_METHODS
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_shop(api_client, channel_USD, count_queries):
    query = (
        FRAGMENT_SHIPPING_METHODS
        + """
        query getShop($channel: String!) {
          shop {
            defaultCountry {
              code
              country
            }
            availableShippingMethods(channel: $channel) {
              ...AvailableShippingMethods
            }
            countries {
              country
              code
            }
          }
        }
    """
    )

    get_graphql_content(
        api_client.post_graphql(query, variables={"channel": channel_USD.slug})
    )
