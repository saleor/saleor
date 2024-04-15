import pytest
from django.db import connection

from .....warehouse.models import Stock
from ....tests.utils import get_graphql_content

STOCKS_BULK_UPDATE_MUTATION = """
    mutation StockBulkUpdate($stocks: [StockBulkUpdateInput!]!){
        stockBulkUpdate(stocks: $stocks){
            results{
                errors {
                    field
                    message
                    code
                }
                stock{
                    warehouse{
                        id
                    }
                    productVariant{
                        id
                    }
                    id
                    quantity
                }
            }
            count
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_stocks_bulk_update_queries_count(
    staff_api_client,
    variant,
    variant_with_many_stocks,
    warehouse_no_shipping_zone,
    warehouse_with_external_ref,
    permission_manage_products,
    django_assert_num_queries,
    count_queries,
    any_webhook,
    settings,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variant_1 = variant_with_many_stocks
    variant_2 = variant

    stock_3 = Stock.objects.create(
        warehouse=warehouse_with_external_ref, product_variant=variant, quantity=4
    )
    stock_4 = Stock.objects.create(
        warehouse=warehouse_no_shipping_zone, product_variant=variant, quantity=4
    )

    stocks = variant.stocks.all()
    stock_1 = stocks[0]
    stock_2 = stocks[1]

    new_quantity = 999

    stocks_input = [
        {
            "variantExternalReference": variant_1.external_reference,
            "warehouseExternalReference": stock_1.warehouse.external_reference,
            "quantity": new_quantity,
        }
    ]

    # test number of queries when single object is updated
    with django_assert_num_queries(11):
        staff_api_client.user.user_permissions.add(permission_manage_products)
        response = staff_api_client.post_graphql(
            STOCKS_BULK_UPDATE_MUTATION, {"stocks": stocks_input}
        )
        content = get_graphql_content(response)
        data = content["data"]["stockBulkUpdate"]
        assert data["count"] == 1
        webhook_queries_count = sum(
            [
                1
                for query in connection.queries
                if query["sql"].startswith('SELECT "webhook_webhook"')
            ]
        )
        assert webhook_queries_count == 1

    stocks_input += [
        {
            "variantExternalReference": variant_1.external_reference,
            "warehouseExternalReference": stock_2.warehouse.external_reference,
            "quantity": new_quantity,
        },
        {
            "variantExternalReference": variant_2.external_reference,
            "warehouseExternalReference": stock_3.warehouse.external_reference,
            "quantity": new_quantity,
        },
        {
            "variantExternalReference": variant_2.external_reference,
            "warehouseExternalReference": stock_4.warehouse.external_reference,
            "quantity": new_quantity,
        },
    ]

    # Test number of queries when multiple objects are updated
    with django_assert_num_queries(11):
        staff_api_client.user.user_permissions.add(permission_manage_products)
        response = staff_api_client.post_graphql(
            STOCKS_BULK_UPDATE_MUTATION, {"stocks": stocks_input}
        )

        content = get_graphql_content(response)
        data = content["data"]["stockBulkUpdate"]
        assert data["count"] == 4
        webhook_queries_count = sum(
            [
                1
                for query in connection.queries
                if query["sql"].startswith('SELECT "webhook_webhook"')
            ]
        )
        assert webhook_queries_count == 2
