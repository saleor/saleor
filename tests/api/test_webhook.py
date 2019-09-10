import graphene

from saleor.account.models import ServiceAccount
from saleor.webhook.models import Webhook

from .utils import assert_no_permission, get_graphql_content

WEBHOOK_CREATE_BY_SERVICE_ACCOUNT = """
    mutation webhookCreate($target_url: String, $event: String){
      webhookCreate(input:{targetUrl:$target_url, event:$event}){
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


def test_webhook_create_by_service_account(service_account_api_client):
    query = WEBHOOK_CREATE_BY_SERVICE_ACCOUNT
    variables = {"target_url": "https://www.example.com", "event": "Sample Order"}
    response = service_account_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    new_webhook = Webhook.objects.get()
    assert new_webhook.target_url == "https://www.example.com"
    assert new_webhook.event == "Sample Order"


def test_webhook_create_inactive_service_account(
    service_account_api_client, service_account
):
    service_account.is_active = False
    service_account.save()
    query = WEBHOOK_CREATE_BY_SERVICE_ACCOUNT
    variables = {"target_url": "https://www.example.com", "event": "Sample Order"}
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_create_without_service_account(
    service_account_api_client, service_account
):
    service_account_api_client.service_account = None
    service_account_api_client.service_token = None
    query = WEBHOOK_CREATE_BY_SERVICE_ACCOUNT
    variables = {"target_url": "https://www.example.com", "event": "Sample Order"}
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_create_service_account_doesnt_exist(
    service_account_api_client, service_account
):
    service_account.delete()

    query = WEBHOOK_CREATE_BY_SERVICE_ACCOUNT
    variables = {"target_url": "https://www.example.com", "event": "Sample Order"}
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


WEBHOOK_CREATE_BY_STAFF = """
    mutation webhookCreate($target_url: String, $event: String, $service_account: ID){
      webhookCreate(input:{
            targetUrl:$target_url, event:$event, serviceAccount: $service_account}){
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
    staff_api_client, service_account, permission_manage_webhooks
):
    query = WEBHOOK_CREATE_BY_STAFF
    service_account_id = graphene.Node.to_global_id(
        "ServiceAccount", service_account.pk
    )
    variables = {
        "target_url": "https://www.example.com",
        "event": "Sample Order",
        "service_account": service_account_id,
    }
    staff_api_client.user.user_permissions.add(permission_manage_webhooks)
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    new_webhook = Webhook.objects.get()
    assert new_webhook.target_url == "https://www.example.com"
    assert new_webhook.event == "Sample Order"
    assert new_webhook.service_account == service_account


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
        "event": "Sample Order",
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
        "event": "Sample Order",
        "service_account": service_account_id,
    }
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
    assert Webhook.objects.count() == 0


WEBHOOK_DELETE_BY_SERVICE_ACCOUNT = """
    mutation webhookDelete($id: ID!){
      webhookDelete(id: $id){
        errors{
          field
          message
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
    errors = content["data"]["webhookDelete"]["errors"]
    assert errors[0]["field"] == "id"


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
    mutation webhookUpdate($id: ID!, $event: String,   $is_active: Boolean){
      webhookUpdate(id: $id, input:{event: $event, isActive: $is_active}){
        errors{
          field
          message
        }
        webhook{
          event
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
    variables = {"id": webhook_id, "event": "TestEvent", "is_active": False}
    response = service_account_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


def test_webhook_update_by_staff(
    staff_api_client, service_account, webhook, permission_manage_webhooks
):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id, "event": "TestEvent", "is_active": False}
    staff_api_client.user.user_permissions.add(permission_manage_webhooks)
    response = staff_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    webhook.refresh_from_db()
    assert webhook.is_active is False
    assert webhook.event == "TestEvent"


def test_webhook_update_by_staff_without_permission(
    staff_api_client, service_account, webhook
):
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id, "event": "TestEvent", "is_active": False}
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
            event
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


QUERY_WEBHOOK = """
    query webhook($id: ID!){
      webhook(id: $id){
        id
        isActive
        event
      }
    }
"""


def test_query_webhook_by_staff(staff_api_client, webhook, permission_manage_webhooks):
    query = QUERY_WEBHOOK
    webhook.id = None
    webhook.save()

    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    staff_api_client.user.user_permissions.add(permission_manage_webhooks)
    response = staff_api_client.post_graphql(query, variables=variables)

    content = get_graphql_content(response)
    webhook_response = content["data"]["webhook"]
    assert webhook_response["id"] == webhook_id
    assert webhook_response["isActive"] == webhook.is_active
    assert webhook_response["event"] == webhook.event


def test_query_webhook_by_staff_without_permission(staff_api_client, webhook):
    query = QUERY_WEBHOOK
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = staff_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
