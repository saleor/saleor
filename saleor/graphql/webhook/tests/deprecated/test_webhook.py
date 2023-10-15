import graphene

from .....webhook.deprecated_event_types import WebhookEventType
from .....webhook.models import Webhook
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import WebhookEventTypeEnum

WEBHOOK_CREATE_BY_APP = """
    mutation webhookCreate($name: String, $target_url: String,
            $events: [WebhookEventTypeEnum!]){
      webhookCreate(input:{name: $name, targetUrl:$target_url, events:$events}){
        errors{
          field
          message
        }
        webhook{
          id
        }
      }
    }
"""


def test_webhook_create_by_app(app_api_client, permission_manage_orders):
    query = WEBHOOK_CREATE_BY_APP
    variables = {
        "name": "New integration",
        "target_url": "https://www.example.com",
        "events": [
            WebhookEventTypeEnum.ORDER_CREATED.name,
            WebhookEventTypeEnum.ORDER_CREATED.name,
        ],
    }
    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )
    get_graphql_content(response)
    new_webhook = Webhook.objects.get()
    assert new_webhook.name == "New integration"
    assert new_webhook.target_url == "https://www.example.com"
    events = new_webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


def test_webhook_create_inactive_app(app_api_client, app, permission_manage_orders):
    app.is_active = False
    app.save()
    query = WEBHOOK_CREATE_BY_APP
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "name": "",
    }

    response = app_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_orders]
    )
    assert_no_permission(response)


def test_webhook_create_without_app(app_api_client, app):
    app_api_client.app = None
    app_api_client.app_token = None
    query = WEBHOOK_CREATE_BY_APP
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "name": "",
    }
    response = app_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_create_app_doesnt_exist(app_api_client, app):
    app.delete()

    query = WEBHOOK_CREATE_BY_APP
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "name": "",
    }
    response = app_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


WEBHOOK_CREATE_BY_STAFF = """
    mutation webhookCreate(
        $target_url: String, $events: [WebhookEventTypeEnum!], $app: ID){
      webhookCreate(input:{
            targetUrl:$target_url, events:$events, app: $app}){
        errors{
          field
          message
        }
        webhook{
          id
        }
      }
    }
"""


def test_webhook_create_by_staff(
    staff_api_client,
    app,
    permission_manage_apps,
    permission_manage_orders,
):
    query = WEBHOOK_CREATE_BY_STAFF
    app.permissions.add(permission_manage_orders)
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "app": app_id,
    }
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    new_webhook = Webhook.objects.get()
    assert new_webhook.target_url == "https://www.example.com"
    assert new_webhook.app == app
    events = new_webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


def test_webhook_create_by_staff_with_inactive_app(staff_api_client, app):
    app.is_active = False
    query = WEBHOOK_CREATE_BY_STAFF
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "app": app_id,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


def test_webhook_create_by_staff_without_permission(staff_api_client, app):
    query = WEBHOOK_CREATE_BY_STAFF
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "app": app_id,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


WEBHOOK_UPDATE = """
    mutation webhookUpdate(
        $id: ID!, $events: [WebhookEventTypeEnum!], $is_active: Boolean){
      webhookUpdate(id: $id, input:{events: $events, isActive: $is_active}){
        errors{
          field
          message
        }
        webhook{
          events{
            eventType
          }
          isActive
        }
      }
    }
"""


def test_webhook_update_by_staff(
    staff_api_client, app, webhook, permission_manage_apps
):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "events": [
            WebhookEventTypeEnum.CUSTOMER_CREATED.name,
            WebhookEventTypeEnum.CUSTOMER_CREATED.name,
        ],
        "is_active": False,
    }
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    webhook.refresh_from_db()
    assert webhook.is_active is False
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.CUSTOMER_CREATED.value


def test_webhook_update_by_staff_without_permission(staff_api_client, app, webhook):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "events": [
            WebhookEventTypeEnum.ORDER_CREATED.name,
            WebhookEventTypeEnum.CUSTOMER_CREATED.name,
        ],
        "is_active": False,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


QUERY_WEBHOOK = """
    query webhook($id: ID!){
      webhook(id: $id){
        id
        isActive
        events{
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
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


WEBHOOK_EVENTS_QUERY = """
{
  webhookEvents {
    eventType
    name
  }
}
"""


def test_query_webhook_events(staff_api_client, permission_manage_apps):
    query = WEBHOOK_EVENTS_QUERY
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    webhook_events = content["data"]["webhookEvents"]
    assert len(webhook_events) == len(WebhookEventType.CHOICES)


def test_query_webhook_events_without_permissions(staff_api_client):
    query = WEBHOOK_EVENTS_QUERY
    response = staff_api_client.post_graphql(query)
    assert_no_permission(response)
