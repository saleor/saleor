import pytest

from ....core.enums import ReportingPeriod
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_list(
    api_client,
    category,
    categories_tree,
    count_queries,
):
    query = """
        query ProductsList {
          shop {
            description
            name
          }
          categories(level: 0, first: 4) {
            edges {
              node {
                id
                name
                backgroundImage {
                  url
                }
              }
            }
          }
        }
    """
    get_graphql_content(api_client.post_graphql(query))


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_report_product_sales(
    staff_api_client,
    order_with_lines,
    order_with_lines_channel_PLN,
    permission_manage_products,
    permission_manage_orders,
    channel_USD,
    count_queries,
):
    query = """
        query TopProducts($period: ReportingPeriod!, $channel: String!) {
          reportProductSales(period: $period, first: 20, channel: $channel) {
            edges {
              node {
                revenue(period: $period) {
                  gross {
                    amount
                  }
                }
                quantityOrdered
                sku
              }
            }
          }
        }
    """
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_USD.slug}
    permissions = [permission_manage_orders, permission_manage_products]
    response = staff_api_client.post_graphql(query, variables, permissions)
    get_graphql_content(response)
