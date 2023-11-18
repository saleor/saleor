from unittest.mock import patch

import pytest

from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import WebhookSampleEventTypeEnum

SAMPLE_PAYLOAD_QUERY = """
  query webhookSamplePayload($event_type: WebhookSampleEventTypeEnum!) {
    webhookSamplePayload(eventType: $event_type)
  }
"""


@patch("saleor.graphql.webhook.resolvers.payloads.generate_sample_payload")
@pytest.mark.parametrize(
    ("event_type", "has_access"),
    [
        (WebhookSampleEventTypeEnum.ORDER_CREATED, True),
        (WebhookSampleEventTypeEnum.ORDER_FULLY_PAID, True),
        (WebhookSampleEventTypeEnum.ORDER_UPDATED, True),
        (WebhookSampleEventTypeEnum.ORDER_CANCELLED, True),
        (WebhookSampleEventTypeEnum.ORDER_FULFILLED, True),
        (WebhookSampleEventTypeEnum.CUSTOMER_CREATED, False),
        (WebhookSampleEventTypeEnum.PRODUCT_CREATED, False),
        (WebhookSampleEventTypeEnum.PRODUCT_UPDATED, False),
        (WebhookSampleEventTypeEnum.CHECKOUT_CREATED, False),
        (WebhookSampleEventTypeEnum.CHECKOUT_UPDATED, False),
        (WebhookSampleEventTypeEnum.FULFILLMENT_CREATED, True),
        (WebhookSampleEventTypeEnum.FULFILLMENT_CANCELED, True),
        (WebhookSampleEventTypeEnum.PAGE_CREATED, False),
        (WebhookSampleEventTypeEnum.PAGE_UPDATED, False),
        (WebhookSampleEventTypeEnum.PAGE_DELETED, False),
    ],
)
def test_sample_payload_query_by_app(
    mock_generate_sample_payload,
    event_type,
    has_access,
    app_api_client,
    permission_manage_orders,
):
    mock_generate_sample_payload.return_value = {"mocked_response": ""}
    query = SAMPLE_PAYLOAD_QUERY
    variables = {"event_type": event_type.name}
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_orders]
    )
    if not has_access:
        assert_no_permission(response)
        mock_generate_sample_payload.assert_not_called()
    else:
        get_graphql_content(response)
        mock_generate_sample_payload.assert_called_with(event_type.value)


@patch("saleor.graphql.webhook.resolvers.payloads.generate_sample_payload")
@pytest.mark.parametrize(
    ("event_type", "has_access"),
    [
        (WebhookSampleEventTypeEnum.ORDER_CREATED, False),
        (WebhookSampleEventTypeEnum.ORDER_FULLY_PAID, False),
        (WebhookSampleEventTypeEnum.ORDER_UPDATED, False),
        (WebhookSampleEventTypeEnum.ORDER_CANCELLED, False),
        (WebhookSampleEventTypeEnum.ORDER_FULFILLED, False),
        (WebhookSampleEventTypeEnum.CUSTOMER_CREATED, True),
        (WebhookSampleEventTypeEnum.PRODUCT_CREATED, True),
        (WebhookSampleEventTypeEnum.PRODUCT_UPDATED, True),
        (WebhookSampleEventTypeEnum.CHECKOUT_CREATED, True),
        (WebhookSampleEventTypeEnum.CHECKOUT_UPDATED, True),
        (WebhookSampleEventTypeEnum.FULFILLMENT_CREATED, False),
        (WebhookSampleEventTypeEnum.FULFILLMENT_CANCELED, False),
        (WebhookSampleEventTypeEnum.PAGE_CREATED, True),
        (WebhookSampleEventTypeEnum.PAGE_UPDATED, True),
        (WebhookSampleEventTypeEnum.PAGE_DELETED, True),
    ],
)
def test_sample_payload_query_by_staff(
    mock_generate_sample_payload,
    event_type,
    has_access,
    staff_api_client,
    permission_manage_users,
    permission_manage_products,
    permission_manage_checkouts,
    permission_manage_pages,
):
    mock_generate_sample_payload.return_value = {"mocked_response": ""}
    query = SAMPLE_PAYLOAD_QUERY
    staff_api_client.user.user_permissions.add(permission_manage_users)
    staff_api_client.user.user_permissions.add(permission_manage_products)
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    staff_api_client.user.user_permissions.add(permission_manage_pages)
    variables = {"event_type": event_type.name}
    response = staff_api_client.post_graphql(query, variables=variables)
    if not has_access:
        assert_no_permission(response)
        mock_generate_sample_payload.assert_not_called()
    else:
        get_graphql_content(response)
        mock_generate_sample_payload.assert_called_with(event_type.value)
