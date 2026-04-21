import json
from unittest.mock import patch

import graphene
from django.utils.functional import SimpleLazyObject

from .....account.models import Address
from .....core.utils.json_serializer import CustomJsonEncoder
from .....warehouse import WarehouseClickAndCollectOption
from .....warehouse.models import Stock, Warehouse
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import get_graphql_content

OUT_OF_STOCK_IN_CHANNEL_PATH = (
    "saleor.graphql.warehouse.mutations.warehouse_delete"
    ".trigger_out_of_stock_in_channel_events_for_stocks"
)

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


@patch(
    "saleor.graphql.warehouse.mutations.warehouse_delete."
    "trigger_product_variant_out_of_stock"
)
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
    product_variant_out_of_stock_webhook.assert_called_once_with(
        old_first_stock, requestor=staff_api_client.user
    )


@patch(
    "saleor.graphql.warehouse.mutations.warehouse_delete."
    "trigger_product_variant_out_of_stock"
)
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


@patch(OUT_OF_STOCK_IN_CHANNEL_PATH)
def test_delete_warehouse_triggers_channel_out_of_stock_events(
    mocked_trigger,
    staff_api_client,
    warehouse,
    variant,
    channel_USD,
    site_settings,
    permission_manage_products,
):
    # given - warehouse is the only one in the channel
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    expected_stocks = list(warehouse.stock_set.all())
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then - channel-scoped trigger fired with the warehouse's stocks
    mocked_trigger.assert_called_once()
    passed_stocks, passed_site_settings = mocked_trigger.call_args.args
    assert {s.pk for s in passed_stocks} == {s.pk for s in expected_stocks}
    assert passed_site_settings == site_settings


@patch(OUT_OF_STOCK_IN_CHANNEL_PATH)
def test_delete_warehouse_skips_channel_events_when_legacy_flag_enabled(
    mocked_trigger,
    staff_api_client,
    warehouse,
    variant,
    channel_USD,
    site_settings,
    permission_manage_products,
):
    # given - legacy flag is on
    site_settings.use_legacy_shipping_zone_stock_availability = True
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=5)
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_trigger.assert_not_called()


@patch(OUT_OF_STOCK_IN_CHANNEL_PATH)
def test_delete_warehouse_skips_channel_events_when_no_stocks(
    mocked_trigger,
    staff_api_client,
    warehouse,
    site_settings,
    permission_manage_products,
):
    # given - warehouse has no stocks
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then
    mocked_trigger.assert_not_called()


@patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_out_of_stock_in_channel"
)
def test_delete_warehouse_fires_out_of_stock_in_channel_per_variant(
    mocked_inner_trigger,
    staff_api_client,
    warehouse,
    variant,
    channel_USD,
    site_settings,
    permission_manage_products,
):
    # given - non-C&C warehouse is the only availability source in the channel
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    warehouse_stocks = list(warehouse.stock_set.all())
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then - one channel event per (variant, channel) pair
    expected_pairs = {
        (s.product_variant_id, channel_USD.slug) for s in warehouse_stocks
    }
    fired_pairs = {
        (info.variant_id, info.channel_slug)
        for call in mocked_inner_trigger.call_args_list
        for info in call.args[0]
    }
    assert fired_pairs == expected_pairs


@patch(
    "saleor.warehouse.channel_stock_availability"
    ".trigger_product_variant_out_of_stock_in_channel"
)
def test_delete_warehouse_does_not_fire_channel_event_when_another_warehouse_covers(
    mocked_inner_trigger,
    staff_api_client,
    warehouse,
    channel_USD,
    address,
    site_settings,
    permission_manage_products,
):
    # given - another non-C&C warehouse in the same channel still has stock for
    # every variant held in the deleted warehouse
    site_settings.use_legacy_shipping_zone_stock_availability = False
    site_settings.save(update_fields=["use_legacy_shipping_zone_stock_availability"])
    warehouse_stocks = list(warehouse.stock_set.all())
    other_warehouse = Warehouse.objects.create(
        address=address.get_copy(),
        name="other",
        slug="other",
        click_and_collect_option=WarehouseClickAndCollectOption.DISABLED,
    )
    other_warehouse.channels.add(channel_USD)
    Stock.objects.bulk_create(
        [
            Stock(
                product_variant_id=stock.product_variant_id,
                warehouse=other_warehouse,
                quantity=3,
            )
            for stock in warehouse_stocks
        ]
    )
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_WAREHOUSE,
        variables={"id": warehouse_id},
        permissions=[permission_manage_products],
    )
    get_graphql_content(response)

    # then - other warehouse covers every (variant, channel), no event fires
    mocked_inner_trigger.assert_not_called()
