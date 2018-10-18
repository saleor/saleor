from tests.api.utils import get_graphql_content
from saleor.graphql.product.types import ReportingPeriod


def test_product_sales(staff_api_client, order_with_lines):
    query = """
    query TopProducts($period: ReportingPeriod!) {
        reportProductSales(period: $period) {
            edges {
                node {
                    quantityOrdered
                    sku
                }
            }
        }
    }
    """
    # TODO: add tests for different periods
    variables = {'period': ReportingPeriod.DAY.name}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    edges = content['data']['reportProductSales']['edges']

    line_a = order_with_lines.lines.all()[1]
    assert edges[0]['node']['sku'] == line_a.product_sku
    assert edges[0]['node']['quantityOrdered'] == line_a.quantity

    line_b = order_with_lines.lines.all()[0]
    assert edges[1]['node']['sku'] == line_b.product_sku
    assert edges[1]['node']['quantityOrdered'] == line_b.quantity
