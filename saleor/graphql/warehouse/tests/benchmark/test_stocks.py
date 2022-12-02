import pytest

from .....warehouse.models import Stock, Warehouse
from ....tests.utils import get_graphql_content


@pytest.fixture
def stocks(address, variant):
    warehouses = Warehouse.objects.bulk_create(
        [
            Warehouse(
                address=address.get_copy(),
                name=f"Warehouse {i}",
                slug=f"warehouse_{i}",
                email=f"warehouse{i}@example.com",
            )
            for i in range(10)
        ]
    )
    return Stock.objects.bulk_create(
        [
            Stock(warehouse=warehouse, product_variant=variant)
            for warehouse in warehouses
        ]
    )


STOCKS_QUERY = """
query {
  stocks(first: 100) {
    edges {
      node {
        id
        warehouse {
          name
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_stocks_query(
    staff_api_client,
    stocks,
    permission_manage_products,
    count_queries,
):
    get_graphql_content(
        staff_api_client.post_graphql(
            STOCKS_QUERY,
            permissions=[permission_manage_products],
            check_no_permissions=False,
        )
    )
