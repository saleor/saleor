import pytest

from ....tests.utils import get_graphql_content

SALES_QUERY = """
query GetSales($channel: String){
  sales(last: 10, channel: $channel) {
    edges {
      node {
        id
        name
        type
        startDate
        endDate
        categories(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        collections(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        products(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        variants(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        channelListings {
          id
          discountValue
          currency
          channel {
            id
            name
            isActive
            slug
            currencyCode
          }
        }
        discountValue
        currency
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_sales_query_with_channel_slug(
    staff_api_client,
    promotion_converted_from_sale_list_for_benchmark,
    channel_USD,
    permission_manage_discounts,
    count_queries,
):
    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            SALES_QUERY,
            variables,
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_sales_query_without_channel_slug(
    staff_api_client,
    promotion_converted_from_sale_list_for_benchmark,
    permission_manage_discounts,
    count_queries,
):
    get_graphql_content(
        staff_api_client.post_graphql(
            SALES_QUERY,
            {},
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
    )
