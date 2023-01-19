import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import WebhookEventTypeAsyncEnum

WEBHOOK_UPDATE = """
    mutation webhookUpdate ($id: ID!, $input: WebhookUpdateInput!) {
      webhookUpdate(id: $id, input: $input) {
        errors {
          field
          message
        }
        webhook {
          syncEvents {
            eventType
          }
          asyncEvents {
            eventType
          }
          isActive
        }
      }
    }
"""


def test_webhook_update_not_allowed_by_app(app_api_client, app, webhook):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "input": {
            "asyncEvents": [WebhookEventTypeAsyncEnum.ORDER_CREATED.name],
            "isActive": False,
        },
    }
    response = app_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_update_by_staff(
    staff_api_client, app, webhook, permission_manage_apps
):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "input": {
            "asyncEvents": [
                WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.name,
                WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.name,
            ],
            "isActive": False,
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    webhook.refresh_from_db()
    assert webhook.is_active is False
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.value


def test_webhook_update_by_staff_without_permission(staff_api_client, app, webhook):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "input": {
            "asyncEvents": [
                WebhookEventTypeAsyncEnum.ORDER_CREATED.name,
                WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.name,
            ],
            "isActive": False,
        },
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_update_inherit_events_from_query(
    staff_api_client,
    app,
    webhook,
    permission_manage_apps,
    subscription_order_updated_webhook,
):
    # given
    query = WEBHOOK_UPDATE
    subscription_query = subscription_order_updated_webhook.subscription_query
    initial_event = webhook.events.all()[0].event_type
    assert WebhookEventTypeAsyncEnum.ORDER_CREATED.value == initial_event

    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "input": {"query": subscription_query},
    }
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    webhook.refresh_from_db()

    # then
    data = content["data"]["webhookUpdate"]
    assert not data["errors"]
    events = webhook.events.all()
    assert len(events) == 1
    assert WebhookEventTypeAsyncEnum.ORDER_UPDATED.value == events[0].event_type
