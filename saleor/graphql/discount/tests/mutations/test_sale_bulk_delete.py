from unittest import mock

import graphene
import pytest

from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, Sale, SaleChannelListing
from .....discount.tests.sale_converter import convert_sales_to_promotions
from ....tests.utils import get_graphql_content


@pytest.fixture
def sale_list(channel_USD, product_list, category, collection):
    sales = Sale.objects.bulk_create(
        [Sale(name="Sale 1"), Sale(name="Sale 2"), Sale(name="Sale 3")]
    )
    for sale, product in zip(sales, product_list):
        sale.products.add(product)
        sale.variants.add(product.variants.first())

    sales[0].categories.add(category)
    sales[1].collections.add(collection)

    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(sale=sale, discount_value=5, channel=channel_USD)
            for sale in sales
        ]
    )
    return list(sales)


SALE_BULK_DELETE_MUTATION = """
    mutation saleBulkDelete($ids: [ID!]!) {
        saleBulkDelete(ids: $ids) {
            count
            errors {
                field
                code
            }
        }
    }
    """


@mock.patch("saleor.plugins.manager.PluginsManager.sale_deleted")
@mock.patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_delete_sales(
    update_products_discounted_prices_for_promotion_task,
    deleted_webhook_mock,
    staff_api_client,
    sale_list,
    permission_manage_discounts,
):
    # given
    variables = {
        "ids": [graphene.Node.to_global_id("Sale", sale.id) for sale in sale_list]
    }
    convert_sales_to_promotions()

    # when
    response = staff_api_client.post_graphql(
        SALE_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["saleBulkDelete"]["count"] == 3
    assert not Promotion.objects.filter(
        old_sale_id__in=[sale.id for sale in sale_list]
    ).exists()
    update_products_discounted_prices_for_promotion_task.called_once()
    assert deleted_webhook_mock.call_count == len(sale_list)


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_sales_triggers_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    staff_api_client,
    sale_list,
    permission_manage_discounts,
    any_webhook,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {
        "ids": [graphene.Node.to_global_id("Sale", sale.id) for sale in sale_list]
    }
    convert_sales_to_promotions()
    # when
    response = staff_api_client.post_graphql(
        SALE_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["saleBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == 3


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_sales_with_variants_triggers_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    staff_api_client,
    sale_list,
    permission_manage_discounts,
    any_webhook,
    settings,
    product,
    collection,
    category,
    product_variant_list,
):
    # given
    for sale in sale_list:
        sale.products.add(product)
        sale.collections.add(collection)
        sale.categories.add(category)
        sale.variants.add(*product_variant_list)

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {
        "ids": [graphene.Node.to_global_id("Sale", sale.id) for sale in sale_list]
    }
    convert_sales_to_promotions()

    # when
    response = staff_api_client.post_graphql(
        SALE_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["saleBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == 3


@mock.patch("saleor.plugins.manager.PluginsManager.sale_deleted")
@mock.patch(
    "saleor.product.tasks.update_products_discounted_prices_for_promotion_task.delay"
)
def test_delete_sales_with_promotion_ids(
    update_products_discounted_prices_for_promotion_task,
    deleted_webhook_mock,
    staff_api_client,
    any_webhook,
    sale_list,
    permission_manage_discounts,
):
    # given
    convert_sales_to_promotions()
    variables = {
        "ids": [
            graphene.Node.to_global_id("Promotion", promotion.id)
            for promotion in Promotion.objects.all()
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        SALE_BULK_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)

    assert not content["data"]["saleBulkDelete"]["count"]
    errors = content["data"]["saleBulkDelete"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name

    deleted_webhook_mock.assert_not_called()
    update_products_discounted_prices_for_promotion_task.assert_not_called()
