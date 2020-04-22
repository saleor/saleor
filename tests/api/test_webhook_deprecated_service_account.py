import graphene
import pytest

from saleor.app.models import App
from saleor.graphql.webhook.enums import WebhookEventTypeEnum
from saleor.webhook.models import Webhook

from .test_webhook import QUERY_WEBHOOKS_WITH_SORT
from .utils import assert_no_permission, get_graphql_content

WEBHOOK_CREATE_BY_STAFF = """
    mutation webhookCreate(
        $target_url: String, $events: [WebhookEventTypeEnum], $service_account: ID){
      webhookCreate(input:{
            targetUrl:$target_url, events:$events, serviceAccount: $service_account}){
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


def test_webhook_create_by_staff_and_service_account(
    staff_api_client, app, permission_manage_webhooks, permission_manage_orders,
):
    query = WEBHOOK_CREATE_BY_STAFF
    app.permissions.add(permission_manage_orders)
    service_account_id = graphene.Node.to_global_id("ServiceAccount", app.pk)
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "service_account": service_account_id,
    }
    staff_api_client.user.user_permissions.add(permission_manage_webhooks)
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    new_webhook = Webhook.objects.get()
    assert new_webhook.target_url == "https://www.example.com"
    assert new_webhook.app == app
    events = new_webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


def test_webhook_create_by_staff_with_inactive_service_account(staff_api_client, app):
    app.is_active = False
    query = WEBHOOK_CREATE_BY_STAFF
    service_account_id = graphene.Node.to_global_id("ServiceAccount", app.pk)
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "service_account": service_account_id,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


def test_webhook_create_by_staff_for_sa_without_permission(staff_api_client, app):
    query = WEBHOOK_CREATE_BY_STAFF
    service_account_id = graphene.Node.to_global_id("ServiceAccount", app.pk)
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "service_account": service_account_id,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


@pytest.mark.parametrize(
    "webhooks_sort, result_order",
    [
        (
            {"field": "SERVICE_ACCOUNT", "direction": "ASC"},
            ["hook2", "backup", "hook1"],
        ),
        (
            {"field": "SERVICE_ACCOUNT", "direction": "DESC"},
            ["hook1", "backup", "hook2"],
        ),
    ],
)
def test_query_webhooks_with_sort(
    webhooks_sort, result_order, staff_api_client, permission_manage_webhooks
):
    backupApp = App.objects.create(name="backupApp", is_active=True)
    app = App.objects.create(name="app", is_active=True)
    Webhook.objects.bulk_create(
        [
            Webhook(
                name="hook1", app=backupApp, target_url="http://example.com/activate2",
            ),
            Webhook(name="hook2", app=app, target_url="http://example.com/activate",),
            Webhook(
                name="backup", app=backupApp, target_url="http://example.com/backup",
            ),
        ]
    )
    variables = {"sort_by": webhooks_sort}
    staff_api_client.user.user_permissions.add(permission_manage_webhooks)
    response = staff_api_client.post_graphql(QUERY_WEBHOOKS_WITH_SORT, variables)
    content = get_graphql_content(response)
    webhooks = content["data"]["webhooks"]["edges"]

    for order, webhook_name in enumerate(result_order):
        assert webhooks[order]["node"]["name"] == webhook_name
