from unittest.mock import Mock, patch

import graphene
from django.db import IntegrityError

from .....app.models import App
from .....webhook.models import Webhook
from ....tests.utils import assert_no_permission, get_graphql_content

WEBHOOK_DELETE_BY_APP = """
    mutation webhookDelete($id: ID!) {
      webhookDelete(id: $id) {
        errors {
          field
          message
          code
        }
      }
    }
"""


def test_webhook_delete_by_app(app_api_client, webhook):
    query = WEBHOOK_DELETE_BY_APP
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = app_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)
    assert Webhook.objects.count() == 0


def test_webhook_delete_by_app_and_webhook_assigned_to_other_app(
    app_api_client, webhook
):
    second_app = App.objects.create(name="second")
    webhook.app = second_app
    webhook.save()

    query = WEBHOOK_DELETE_BY_APP
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = app_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)

    webhook.refresh_from_db()
    assert Webhook.objects.count() == 1


def test_webhook_delete_by_app_and_missing_webhook(app_api_client, webhook):
    query = WEBHOOK_DELETE_BY_APP
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    webhook.delete()

    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    errors = content["data"]["webhookDelete"]["errors"]
    assert errors[0]["code"] == "NOT_FOUND"


def test_webhook_delete_by_inactive_app(app_api_client, webhook):
    app = webhook.app
    app.is_active = False
    app.save()
    query = WEBHOOK_DELETE_BY_APP
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}
    response = app_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)


@patch("saleor.webhook.models.Webhook.delete")
def test_webhook_delete_deactivates_before_deletion(
    mocked_delete, app_api_client, webhook
):
    # given
    query = WEBHOOK_DELETE_BY_APP
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}

    # when
    response = app_api_client.post_graphql(query, variables=variables)
    get_graphql_content(response)

    # then
    webhook.refresh_from_db()
    assert webhook.is_active is False


@patch("saleor.webhook.models.Webhook.delete")
def test_webhook_delete_raises_integrity_error(mocked_delete, app_api_client, webhook):
    # given
    query = WEBHOOK_DELETE_BY_APP
    mocked_delete.side_effect = IntegrityError(Mock(return_value={"as": "sa"}))
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}

    # when
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    # then
    webhook.refresh_from_db()
    errors = content["data"]["webhookDelete"]["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["message"] == "Webhook couldn't be deleted at this time due to "
        "running task.Webhook deactivated. "
        "Try deleting Webhook later"
    )
    assert errors[0]["code"] == "DELETE_FAILED"
    assert webhook.is_active is False


def test_webhook_delete_when_app_doesnt_exist(app_api_client, app):
    app.delete()

    query = WEBHOOK_DELETE_BY_APP
    webhook_id = graphene.Node.to_global_id("Webhook", 1)
    variables = {"id": webhook_id}
    response = app_api_client.post_graphql(query, variables=variables)
    assert_no_permission(response)
