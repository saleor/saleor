import graphene

from .....webhook.models import Webhook
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import WebhookEventTypeAsyncEnum, WebhookEventTypeSyncEnum

WEBHOOK_CREATE = """
    mutation webhookCreate($input: WebhookCreateInput!){
      webhookCreate(input: $input) {
        errors {
          field
          message
        }
        webhook {
          id
        }
      }
    }
"""


def test_webhook_create_by_app(app_api_client, permission_manage_orders):
    query = WEBHOOK_CREATE
    variables = {
        "input": {
            "name": "New integration",
            "targetUrl": "https://www.example.com",
            "asyncEvents": [
                WebhookEventTypeAsyncEnum.ORDER_CREATED.name,
                WebhookEventTypeAsyncEnum.ORDER_CREATED.name,
            ],
        }
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
    assert events[0].event_type == WebhookEventTypeAsyncEnum.ORDER_CREATED.value


def test_webhook_create_inactive_app(app_api_client, app, permission_manage_orders):
    app.is_active = False
    app.save()
    query = WEBHOOK_CREATE
    variables = {
        "input": {
            "targetUrl": "https://www.example.com",
            "asyncEvents": [WebhookEventTypeAsyncEnum.ORDER_CREATED.name],
            "name": "",
        }
    }

    response = app_api_client.post_graphql(
        query, variables=variables, permissions=[permission_manage_orders]
    )
    assert_no_permission(response)


def test_webhook_create_without_app(app_api_client, app):
    app_api_client.app = None
    app_api_client.app_token = None
    query = WEBHOOK_CREATE
    variables = {
        "input": {
            "targetUrl": "https://www.example.com",
            "asyncEvents": [WebhookEventTypeAsyncEnum.ORDER_CREATED.name],
            "name": "",
        }
    }
    response = app_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_create_app_doesnt_exist(app_api_client, app):
    app.delete()

    query = WEBHOOK_CREATE
    variables = {
        "input": {
            "targetUrl": "https://www.example.com",
            "asyncEvents": [WebhookEventTypeAsyncEnum.ORDER_CREATED.name],
            "name": "",
        }
    }
    response = app_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_create_by_staff(
    staff_api_client,
    app,
    permission_manage_apps,
    permission_manage_orders,
):
    query = WEBHOOK_CREATE
    app.permissions.add(permission_manage_orders)
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "input": {
            "targetUrl": "https://www.example.com",
            "asyncEvents": [WebhookEventTypeAsyncEnum.ORDER_CREATED.name],
            "syncEvents": [WebhookEventTypeSyncEnum.PAYMENT_LIST_GATEWAYS.name],
            "app": app_id,
        }
    }
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    new_webhook = Webhook.objects.get()
    assert new_webhook.target_url == "https://www.example.com"
    assert new_webhook.app == app
    events = new_webhook.events.all()
    assert len(events) == 2

    created_event_types = [events[0].event_type, events[1].event_type]
    assert WebhookEventTypeAsyncEnum.ORDER_CREATED.value in created_event_types
    assert WebhookEventTypeSyncEnum.PAYMENT_LIST_GATEWAYS.value in created_event_types


def test_webhook_create_by_staff_with_inactive_app(staff_api_client, app):
    app.is_active = False
    query = WEBHOOK_CREATE
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "input": {
            "targetUrl": "https://www.example.com",
            "asyncEvents": [WebhookEventTypeAsyncEnum.ORDER_CREATED.name],
            "app": app_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


def test_webhook_create_by_staff_without_permission(staff_api_client, app):
    query = WEBHOOK_CREATE
    app_id = graphene.Node.to_global_id("App", app.pk)
    variables = {
        "input": {
            "targetUrl": "https://www.example.com",
            "asyncEvents": [WebhookEventTypeAsyncEnum.ORDER_CREATED.name],
            "app": app_id,
        }
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


def test_webhook_create_inherit_events_from_query(
    app_api_client, permission_manage_orders, subscription_order_created_webhook
):
    # given
    query = WEBHOOK_CREATE
    subscription_query = subscription_order_created_webhook.subscription_query
    variables = {
        "input": {
            "name": "New integration",
            "targetUrl": "https://www.example.com",
            "query": subscription_query,
        }
    }

    # when
    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookCreate"]
    assert not data["errors"]
    _, id = graphene.Node.from_global_id(data["webhook"]["id"])
    new_webhook = Webhook.objects.filter(id=id).get()
    events = new_webhook.events.all()
    assert len(events) == 1
    assert WebhookEventTypeAsyncEnum.ORDER_CREATED.value == events[0].event_type


def test_webhook_create_by_staff_invalid_query(
    app_api_client, permission_manage_orders
):
    query = WEBHOOK_CREATE
    variables = {
        "input": {
            "name": "New integration",
            "targetUrl": "https://www.example.com",
            "asyncEvents": [
                WebhookEventTypeAsyncEnum.ORDER_CREATED.name,
            ],
            "query": "invalid_query",
        }
    }
    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    expected_errors = [{"field": "query", "message": "Subscription query is not valid"}]
    content = content["data"]["webhookCreate"]
    assert not content["webhook"]
    assert content["errors"] == expected_errors


SUBSCRIPTION_QUERY_WITH_MULTIPLE_LVL_FIELDS = """
subscription {
  event {
    ... on PaymentListGateways {
      checkout {
        id
      }
    }
  }
  ... on CheckoutFilterShippingMethods {
    checkout {
      id
    }
    shippingMethods {
      name
      id
    }
  }
}"""


def test_webhook_create_by_staff_invalid_query_multiple_level_fields(
    app_api_client, permission_manage_orders
):
    query = WEBHOOK_CREATE
    variables = {
        "input": {
            "name": "New integration",
            "targetUrl": "https://www.example.com",
            "asyncEvents": [
                WebhookEventTypeAsyncEnum.ORDER_CREATED.name,
            ],
            "query": SUBSCRIPTION_QUERY_WITH_MULTIPLE_LVL_FIELDS,
        }
    }
    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    expected_errors = [{"field": "query", "message": "Subscription query is not valid"}]
    content = content["data"]["webhookCreate"]
    assert not content["webhook"]
    assert content["errors"] == expected_errors
