import json
from unittest import mock

import graphene
from freezegun import freeze_time

from ....graphql.product.tests.mutations.test_product_create import (
    CREATE_PRODUCT_MUTATION,
)
from ....webhook.transport.asynchronous import create_deliveries_for_subscriptions
from ..product_created import ProductCreated


@freeze_time("2024-01-01 10:00")
@mock.patch("saleor.webhook.utils.get_webhooks_for_event")
@mock.patch("saleor.webhook.transport.asynchronous.transport.trigger_webhooks_async")
def test_product_created_trigger(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    product,
    django_capture_on_commit_callbacks,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]

    # when
    with django_capture_on_commit_callbacks(execute=True):
        ProductCreated.trigger_webhook_async(product)

    # then
    mocked_webhook_trigger.assert_called_once_with(
        data=None,
        event_type=ProductCreated,
        webhooks=[any_webhook],
        subscribable_object=product,
        requestor=None,
        legacy_data_generator=mock.ANY,
        allow_replica=True,
    )


SUBSCRIPTION_PRODUCT_CREATED = """
    subscription {
      event {
        ...on ProductCreated {
          product {
            id
          }
        }
      }
    }
"""


def test_product_created(product, subscription_webhook):
    # given
    event_type = ProductCreated.event_type
    webhook = subscription_webhook(SUBSCRIPTION_PRODUCT_CREATED, event_type)
    webhooks = [webhook]
    product_id = graphene.Node.to_global_id("Product", product.id)

    # when
    deliveries = create_deliveries_for_subscriptions(event_type, product, webhooks)
    expected_payload = json.dumps({"product": {"id": product_id}})

    # then
    assert deliveries[0].payload.get_payload() == expected_payload
    assert len(deliveries) == len(webhooks)
    assert deliveries[0].webhook == webhooks[0]


@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async"
)
@mock.patch("saleor.webhook.utils.get_webhooks_for_event")
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.generate_payload_from_subscription"
)
def test_trigger_webhook_async_with_subscription_use_main_db(
    mocked_generate_payload,
    mocked_get_webhooks_for_event,
    mocked_request,
    staff_api_client,
    product_type,
    category,
    permission_manage_products,
    subscription_webhook,
    settings,
):
    # given
    webhook = subscription_webhook(
        SUBSCRIPTION_PRODUCT_CREATED, ProductCreated.event_type
    )
    mocked_get_webhooks_for_event.return_value = [webhook]

    product_type_id = graphene.Node.to_global_id("ProductType", product_type.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    product_name = "test name"
    product_slug = "product-test-slug"

    variables = {
        "input": {
            "productType": product_type_id,
            "category": category_id,
            "name": product_name,
            "slug": product_slug,
        }
    }

    # when
    staff_api_client.post_graphql(
        CREATE_PRODUCT_MUTATION, variables, permissions=[permission_manage_products]
    )

    # then
    mocked_generate_payload.assert_called_once()
    assert not mocked_generate_payload.call_args[1]["request"].allow_replica
