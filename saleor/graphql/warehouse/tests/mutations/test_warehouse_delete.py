import json
from unittest.mock import patch

import graphene
from django.utils.functional import SimpleLazyObject

from .....account.models import Address
from .....core.utils.json_serializer import CustomJsonEncoder
from .....warehouse.models import Stock, Warehouse
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import get_graphql_content

MUTATION_DELETE_WAREHOUSE = """
mutation deleteWarehouse($id: ID!) {
    deleteWarehouse(id: $id) {
        errors {
            message
            field
            code
        }
    }
}
"""


def test_delete_warehouse_mutation(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    assert Warehouse.objects.count() == 1

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["deleteWarehouse"]["errors"]
    assert len(errors) == 0
    assert not Warehouse.objects.exists()


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_warehouse_mutation_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    warehouse,
    permission_manage_products,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["deleteWarehouse"]["errors"]) == 0
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": warehouse_id,
                "name": warehouse.name,
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.WAREHOUSE_DELETED,
        [any_webhook],
        warehouse,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_delete_warehouse_mutation_with_webhooks(
    product_variant_out_of_stock_webhook,
    staff_api_client,
    warehouse,
    permission_manage_products,
    variant_with_many_stocks,
):
    # given
    old_first_stock = Stock.objects.first()
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    assert Warehouse.objects.count() == 3
    assert Stock.objects.count() == 3

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["deleteWarehouse"]["errors"]
    assert len(errors) == 0
    assert Warehouse.objects.count() == 2
    assert Stock.objects.count() == 2
    product_variant_out_of_stock_webhook.assert_called_once_with(old_first_stock)


@patch("saleor.plugins.manager.PluginsManager.product_variant_out_of_stock")
def test_delete_warehouse_mutation_with_webhooks_for_many_product_variants(
    product_variant_out_of_stock_webhook,
    staff_api_client,
    warehouse,
    permission_manage_products,
    product_with_two_variants,
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    assert Warehouse.objects.count() == 1
    assert Stock.objects.count() == 2

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["deleteWarehouse"]["errors"]
    assert len(errors) == 0
    assert Warehouse.objects.count() == 0
    assert Stock.objects.count() == 0
    assert product_variant_out_of_stock_webhook.call_count == 2


def test_delete_warehouse_deletes_associated_address(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    assert Address.objects.count() == 1

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["deleteWarehouse"]["errors"]
    assert len(errors) == 0
    assert not Address.objects.exists()
