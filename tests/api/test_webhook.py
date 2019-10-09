import graphene

from saleor.account.models import ServiceAccount
from saleor.graphql.webhook.enums import WebhookEventTypeEnum
from saleor.webhook.models import Webhook

from .utils import assert_no_permission, get_graphql_content

WEBHOOK_CREATE_BY_SERVICE_ACCOUNT = """
    mutation webhookCreate($name: String, $target_url: String,
            $events: [WebhookEventTypeEnum]){
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


def test_webhook_create_by_service_account(
    service_account_api_client, service_account, permission_manage_orders
):
    service_account.permissions.add(permission_manage_orders)
    query = WEBHOOK_CREATE_BY_SERVICE_ACCOUNT
    variables = {
        "name": "New integration",
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
    }
    response = service_account_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    new_webhook = Webhook.objects.get()
    assert new_webhook.name == "New integration"
    assert new_webhook.target_url == "https://www.example.com"
    events = new_webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


def test_webhook_create_inactive_service_account(
    service_account_api_client, service_account, permission_manage_orders
):
    service_account.permissions.add(permission_manage_orders)
    service_account.is_active = False
    service_account.save()
    query = WEBHOOK_CREATE_BY_SERVICE_ACCOUNT
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "name": "",
    }

    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_create_without_service_account(
    service_account_api_client, service_account
):
    service_account_api_client.service_account = None
    service_account_api_client.service_token = None
    query = WEBHOOK_CREATE_BY_SERVICE_ACCOUNT
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "name": "",
    }
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_create_service_account_doesnt_exist(
    service_account_api_client, service_account
):
    service_account.delete()

    query = WEBHOOK_CREATE_BY_SERVICE_ACCOUNT
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "name": "",
    }
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


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


def test_webhook_create_by_staff(
    staff_api_client,
    service_account,
    permission_manage_webhooks,
    permission_manage_orders,
):
    query = WEBHOOK_CREATE_BY_STAFF
    service_account.permissions.add(permission_manage_orders)
    service_account_id = graphene.Node.to_global_id(
        "ServiceAccount", service_account.pk
    )
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
    assert new_webhook.service_account == service_account
    events = new_webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


def test_webhook_create_by_staff_with_inactive_service_account(
    staff_api_client, service_account
):
    service_account.is_active = False
    query = WEBHOOK_CREATE_BY_STAFF
    service_account_id = graphene.Node.to_global_id(
        "ServiceAccount", service_account.pk
    )
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "service_account": service_account_id,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


def test_webhook_create_by_staff_without_permission(staff_api_client, service_account):
    query = WEBHOOK_CREATE_BY_STAFF
    service_account_id = graphene.Node.to_global_id(
        "ServiceAccount", service_account.pk
    )
    variables = {
        "target_url": "https://www.example.com",
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "service_account": service_account_id,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


WEBHOOK_DELETE_BY_SERVICE_ACCOUNT = """
    mutation webhookDelete($id: ID!){
      webhookDelete(id: $id){
        webhookErrors{
          field
          message
          code
        }
      }
    }
"""


def test_webhook_delete_by_service_account(service_account_api_client, webhook):
    query = WEBHOOK_DELETE_BY_SERVICE_ACCOUNT
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = service_account_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    assert Webhook.objects.count() == 0


def test_webhook_delete_by_service_account_with_wrong_webhook(
    service_account_api_client, webhook
):
    second_service_account = ServiceAccount.objects.create(name="second")
    webhook.service_account = second_service_account
    webhook.save()

    query = WEBHOOK_DELETE_BY_SERVICE_ACCOUNT
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = service_account_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)

    webhook.refresh_from_db()
    assert Webhook.objects.count() == 1


def test_webhook_delete_by_service_account_wrong_webhook(
    service_account_api_client, webhook
):
    query = WEBHOOK_DELETE_BY_SERVICE_ACCOUNT
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    webhook.delete()

    response = service_account_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    errors = content["data"]["webhookDelete"]["webhookErrors"]
    assert errors[0]["code"] == "GRAPHQL_ERROR"


def test_webhook_delete_by_inactive_service_account(
    service_account_api_client, webhook
):
    service_account = webhook.service_account
    service_account.is_active = False
    service_account.save()
    query = WEBHOOK_DELETE_BY_SERVICE_ACCOUNT
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_delete_service_account_doesnt_exist(
    service_account_api_client, service_account
):
    service_account.delete()

    query = WEBHOOK_DELETE_BY_SERVICE_ACCOUNT
    webhook_id = graphene.Node.to_global_id("Webhook", 1)
    variables = {"id": webhook_id}
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


WEBHOOK_UPDATE = """
    mutation webhookUpdate(
        $id: ID!, $events: [WebhookEventTypeEnum], $is_active: Boolean){
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


def test_webhook_update_not_allowed_by_service_account(
    service_account_api_client, service_account, webhook
):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "is_active": False,
    }
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_update_by_staff(
    staff_api_client, service_account, webhook, permission_manage_webhooks
):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "is_active": False,
    }
    staff_api_client.user.user_permissions.add(permission_manage_webhooks)
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    webhook.refresh_from_db()
    assert webhook.is_active is False
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


def test_webhook_update_by_staff_without_permission(
    staff_api_client, service_account, webhook
):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "events": [WebhookEventTypeEnum.ORDER_CREATED.name],
        "is_active": False,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


QUERY_WEBHOOKS = """
    query webhooks{
      webhooks(first:5){
        edges{
          node{
            serviceAccount{
              id
            }
            targetUrl
            id
            events{
              eventType
            }
          }
        }
      }
    }
"""


def test_query_webhooks_by_staff(staff_api_client, webhook, permission_manage_webhooks):
    query = QUERY_WEBHOOKS
    webhook.id = None
    webhook.save()

    staff_api_client.user.user_permissions.add(permission_manage_webhooks)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    webhooks = content["data"]["webhooks"]["edges"]
    assert len(webhooks) == 2


def test_query_webhooks_by_staff_without_permission(staff_api_client, webhook):
    query = QUERY_WEBHOOKS
    response = staff_api_client.post_graphql(query)
    assert_no_permission(response)


def test_query_webhooks_by_service_account(service_account_api_client, webhook):
    second_sa = ServiceAccount.objects.create(
        name="Sample service account", is_active=True
    )
    second_webhook = Webhook.objects.create(
        service_account=second_sa, target_url="http://www.example.com/test"
    )
    second_webhook.events.create(event_type="order_created")

    query = QUERY_WEBHOOKS
    response = service_account_api_client.post_graphql(query)
    content = get_graphql_content(response)
    webhooks = content["data"]["webhooks"]["edges"]
    assert len(webhooks) == 1
    webhook_data = webhooks[0]
    webhook_id = webhook_data["node"]["id"]
    _, webhook_id = graphene.Node.from_global_id(webhook_id)
    assert webhook_id == str(webhook.id)


def test_query_webhooks_by_service_account_without_permissions(
    service_account_api_client
):
    second_sa = ServiceAccount.objects.create(
        name="Sample service account", is_active=True
    )
    second_webhook = Webhook.objects.create(
        service_account=second_sa, target_url="http://www.example.com/test"
    )
    second_webhook.events.create(event_type="order_created")

    query = QUERY_WEBHOOKS
    response = service_account_api_client.post_graphql(query)
    content = get_graphql_content(response)
    webhooks = content["data"]["webhooks"]["edges"]
    assert len(webhooks) == 0


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


def test_query_webhook_by_staff(staff_api_client, webhook, permission_manage_webhooks):
    query = QUERY_WEBHOOK

    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    staff_api_client.user.user_permissions.add(permission_manage_webhooks)
    response = staff_api_client.post_graphql(query, variables=variables)

    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response["id"] == webhook_id
    assert webhook_response["isActive"] == webhook.is_active
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


def test_query_webhook_by_staff_without_permission(staff_api_client, webhook):
    query = QUERY_WEBHOOK
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_query_webhook_by_service_account(service_account_api_client, webhook):
    query = QUERY_WEBHOOK

    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = service_account_api_client.post_graphql(query, variables=variables)

    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response["id"] == webhook_id
    assert webhook_response["isActive"] == webhook.is_active
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeEnum.ORDER_CREATED.value


def test_query_webhook_by_service_account_without_permission(
    service_account_api_client
):
    second_sa = ServiceAccount.objects.create(
        name="Sample service account", is_active=True
    )
    webhook = Webhook.objects.create(
        service_account=second_sa, target_url="http://www.example.com/test"
    )
    webhook.events.create(event_type="order_created")

    query = QUERY_WEBHOOK
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = service_account_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response is None
