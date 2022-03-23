import graphene

from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.subscription_payload import (
    generate_payload_from_subscription,
    initialize_context,
    validate_subscription_query,
)

TEST_VALID_SUBSCRIPTION_QUERY = """
    subscription{
      event{
        ...on ProductUpdated{
          product{
            id
          }
        }
      }
    }
"""

TEST_INVALID_SUBSCRIPTION_QUERY = """
    event{
      ...on ProductUpdated{
        product{
          id
        }
"""


def test_validate_subscription_query_valid():
    result = validate_subscription_query(TEST_VALID_SUBSCRIPTION_QUERY)
    assert result is True


def test_validate_subscription_query_invalid():

    result = validate_subscription_query(TEST_INVALID_SUBSCRIPTION_QUERY)
    assert result is False


def test_generate_payload_from_subscription_product_updated(
    product, subscription_product_updated_webhook
):
    event_type = WebhookEventAsyncType.PRODUCT_UPDATED
    webhook = subscription_product_updated_webhook
    subscribable_object = product
    context = initialize_context()
    product_id = graphene.Node.to_global_id("Product", product.pk)

    payload = generate_payload_from_subscription(
        event_type=event_type,
        subscribable_object=subscribable_object,
        subscription_query=webhook.subscription_query,
        context=context,
        app=webhook.app,
    )
    expected_payload = {"product": {"id": product_id}}
    assert payload == expected_payload
