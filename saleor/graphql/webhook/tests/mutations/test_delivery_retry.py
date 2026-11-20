from unittest.mock import patch

import graphene

from .....core import EventDeliveryStatus
from .....graphql.tests.utils import assert_no_permission, get_graphql_content
from .....webhook.error_codes import WebhookErrorCode
from .....webhook.event_types import WebhookEventAsyncType

WEBHOOK_DELIVERY_RETRY_MUTATION = """
    mutation eventDeliveryRetry($id: ID!){
      eventDeliveryRetry(id: $id){
        errors{
          field
          code
          message
        }
        delivery{
          id
        }
      }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.event_delivery_retry")
def test_delivery_retry_mutation(
    mocked_send_request_async,
    app_api_client,
    permission_manage_apps,
    event_delivery,
    settings,
):
    # given
    query = WEBHOOK_DELIVERY_RETRY_MUTATION
    delivery_id = graphene.Node.to_global_id("EventDelivery", event_delivery.pk)
    variables = {"id": delivery_id}

    # when
    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    mocked_send_request_async.assert_called_once_with(event_delivery)
    errors = content["data"]["eventDeliveryRetry"]["errors"]
    assert len(errors) == 0


def test_webhook_delivery_retry_without_permission(
    staff_api_client, app, event_delivery
):
    query = WEBHOOK_DELIVERY_RETRY_MUTATION
    delivery_id = graphene.Node.to_global_id("EventDelivery", event_delivery.pk)
    variables = {"id": delivery_id}
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_delivery_retry_wrong_type(
    staff_api_client, app, event_attempt, permission_manage_apps
):
    query = WEBHOOK_DELIVERY_RETRY_MUTATION
    delivery_wrong_id = graphene.Node.to_global_id(
        "EventDeliveryAttempt", event_attempt.id
    )
    variables = {"id": delivery_wrong_id}
    expected_message = (
        f"Invalid ID: {delivery_wrong_id}. Expected: EventDelivery,"
        + " received: EventDeliveryAttempt."
    )
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    errors = content["data"]["eventDeliveryRetry"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["message"] == expected_message


def test_delivery_retry_mutation_wrong_id(
    app_api_client, permission_manage_apps, event_delivery
):
    # given
    query = WEBHOOK_DELIVERY_RETRY_MUTATION
    variables = {"id": "/w"}
    expected_message = "Invalid ID: /w. Expected: EventDelivery."
    # when
    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    # then
    errors = content["data"]["eventDeliveryRetry"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["message"] == expected_message


def test_delivery_retry_mutation_for_removed_app(
    app_api_client, permission_manage_apps, event_delivery_removed_app
):
    # given
    query = WEBHOOK_DELIVERY_RETRY_MUTATION
    delivery_id = graphene.Node.to_global_id(
        "EventDelivery", event_delivery_removed_app.pk
    )
    variables = {"id": delivery_id}

    # when
    response = app_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_apps]
    )

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["eventDeliveryRetry"]
    assert app_data["delivery"] is None
    assert app_data["errors"][0]["code"] == WebhookErrorCode.NOT_FOUND.name
    assert app_data["errors"][0]["field"] == "id"


@patch("saleor.plugins.manager.PluginsManager.event_delivery_retry")
def test_delivery_retry_rejects_saleor_api_url_changed(
    mocked_event_delivery_retry,
    app_api_client,
    permission_manage_apps,
    event_delivery,
):
    # given
    event_delivery.event_type = WebhookEventAsyncType.SALEOR_API_URL_CHANGED
    event_delivery.status = EventDeliveryStatus.FAILED
    event_delivery.save(update_fields=["event_type", "status"])
    delivery_id = graphene.Node.to_global_id("EventDelivery", event_delivery.pk)

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_DELIVERY_RETRY_MUTATION,
        variables={"id": delivery_id},
        permissions=[permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["eventDeliveryRetry"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == WebhookErrorCode.INVALID.name
    assert errors[0]["message"] == (
        "Deliveries of the SALEOR_API_URL_CHANGED event can't be retried, because "
        "a retry would carry the new Saleor API URL instead of the previous one. "
        "Reinstall the app instead."
    )
    mocked_event_delivery_retry.assert_not_called()
    event_delivery.refresh_from_db(fields=["status"])
    assert event_delivery.status == EventDeliveryStatus.FAILED
