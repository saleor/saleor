import graphene

from .....app.models import App
from .....webhook.models import Webhook
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import WebhookEventTypeAsyncEnum, WebhookEventTypeSyncEnum

QUERY_WEBHOOK = """
    query webhook($id: ID!) {
      webhook(id: $id) {
        id
        isActive
        name
        subscriptionQuery
        asyncEvents {
          eventType
        }
        syncEvents {
          eventType
        }
      }
    }
"""


def test_query_webhook_by_staff(staff_api_client, webhook, permission_manage_apps):
    query = QUERY_WEBHOOK

    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query, variables=variables)

    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response["id"] == webhook_id
    assert webhook_response["isActive"] == webhook.is_active
    assert webhook_response["subscriptionQuery"] is None
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeAsyncEnum.ORDER_CREATED.value


def test_query_webhook_with_subscription_query_by_staff(
    staff_api_client, subscription_order_created_webhook, permission_manage_apps
):
    query = QUERY_WEBHOOK
    webhook = subscription_order_created_webhook
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query, variables=variables)

    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response["id"] == webhook_id
    assert webhook_response["isActive"] == webhook.is_active
    assert webhook_response["subscriptionQuery"] == webhook.subscription_query
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeAsyncEnum.ORDER_CREATED.value


def test_query_webhook_by_staff_without_permission(staff_api_client, webhook):
    query = QUERY_WEBHOOK
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_query_webhook_by_app(app_api_client, webhook):
    query = QUERY_WEBHOOK

    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = app_api_client.post_graphql(query, variables=variables)

    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response["id"] == webhook_id
    assert webhook_response["isActive"] == webhook.is_active
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeAsyncEnum.ORDER_CREATED.value


def test_query_webhook_by_app_without_permission(app_api_client):
    second_app = App.objects.create(name="Sample app account", is_active=True)
    webhook = Webhook.objects.create(
        app=second_app, target_url="http://www.example.com/test"
    )
    webhook.events.create(event_type="order_created")

    query = QUERY_WEBHOOK
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response is None


def test_query_webhook_by_anonymnous_client(api_client):
    second_app = App.objects.create(name="Sample app account", is_active=True)
    webhook = Webhook.objects.create(
        app=second_app, target_url="http://www.example.com/test"
    )
    webhook.events.create(event_type="order_created")

    query = QUERY_WEBHOOK
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response, ignore_errors=True)
    assert content["data"]["webhook"] is None


def test_query_webhook_sync_and_async_events(
    staff_api_client, webhook, permission_manage_apps
):
    # given
    webhook.events.all().delete()
    webhook.events.create(event_type=WebhookEventTypeAsyncEnum.ORDER_CREATED.value)
    webhook.events.create(
        event_type=WebhookEventTypeSyncEnum.PAYMENT_LIST_GATEWAYS.value
    )
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    response = staff_api_client.post_graphql(QUERY_WEBHOOK, variables=variables)

    # then
    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]

    assert (
        webhook_response["asyncEvents"][0]["eventType"]
        == WebhookEventTypeAsyncEnum.ORDER_CREATED.name
    )
    assert (
        webhook_response["syncEvents"][0]["eventType"]
        == WebhookEventTypeSyncEnum.PAYMENT_LIST_GATEWAYS.name
    )


def test_webhook_query_invalid_id(staff_api_client, webhook, permission_manage_apps):
    webhook_id = "'"
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {
        "id": webhook_id,
    }
    response = staff_api_client.post_graphql(QUERY_WEBHOOK, variables)
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {webhook_id}."
    assert content["data"]["webhook"] is None


def test_webhook_query_object_with_given_id_does_not_exist(
    staff_api_client, webhook, permission_manage_apps
):
    webhook_id = graphene.Node.to_global_id("Webhook", -1)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"id": webhook_id}
    response = staff_api_client.post_graphql(QUERY_WEBHOOK, variables)
    content = get_graphql_content(response)
    assert content["data"]["webhook"] is None


def test_webhook_with_invalid_object_type(
    staff_api_client, webhook, permission_manage_apps
):
    webhook_id = graphene.Node.to_global_id("Product", webhook.pk)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"id": webhook_id}
    response = staff_api_client.post_graphql(QUERY_WEBHOOK, variables)
    content = get_graphql_content(response)
    assert content["data"]["webhook"] is None


def test_webhook_without_name(
    staff_api_client, webhook_without_name, permission_manage_apps
):
    query = QUERY_WEBHOOK
    webhook_id = graphene.Node.to_global_id("Webhook", webhook_without_name.pk)
    variables = {"id": webhook_id}
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response["name"] is None
    events = webhook_without_name.events.all()
    assert len(events) == 1
