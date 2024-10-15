import pytest

from ....tests.utils import get_graphql_content

VOUCHERS_QUERY = """
query GetVouchers($channel: String){
  vouchers(last: 10, channel: $channel) {
    edges {
      node {
        id
        name
        type
        startDate
        endDate
        usageLimit
        code
        applyOncePerOrder
        applyOncePerCustomer
        discountValueType
        minCheckoutItemsQuantity
        countries{
          code
          country
          vat{
            countryCode
            standardRate
          }
        }
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
          minSpent{
            currency
            amount
          }
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
def test_vouchers_query_with_channel_slug(
    staff_api_client,
    vouchers_list,
    channel_USD,
    permission_manage_discounts,
    count_queries,
):
    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            VOUCHERS_QUERY,
            variables,
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_vouchers_query_withot_channel_slug(
    staff_api_client,
    vouchers_list,
    permission_manage_discounts,
    count_queries,
):
    get_graphql_content(
        staff_api_client.post_graphql(
            VOUCHERS_QUERY,
            {},
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
    )
