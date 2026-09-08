from unittest.mock import Mock, patch

import graphene
import pytest
from django.db import IntegrityError

from .....app.models import App
from .....webhook.error_codes import WebhookErrorCode
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
        webhook {
          id
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


def test_webhook_delete_by_staff(staff_api_client, webhook, permission_manage_apps):
    # given
    query = WEBHOOK_DELETE_BY_APP
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_apps],
    )

    # then
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


def test_webhook_delete_by_staff_for_removed_app(
    staff_api_client, webhook_removed_app, permission_manage_apps
):
    # given
    query = WEBHOOK_DELETE_BY_APP
    webhook_id = graphene.Node.to_global_id("Webhook", webhook_removed_app.pk)
    variables = {"id": webhook_id}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["webhookDelete"]
    assert app_data["webhook"] is None
    assert app_data["errors"][0]["code"] == WebhookErrorCode.NOT_FOUND.name
    assert app_data["errors"][0]["field"] == "id"


WEBHOOK_DELETE_BY_POINTER = """
    mutation webhookDelete($id: ID, $identifier: String) {
      webhookDelete(id: $id, identifier: $identifier) {
        errors {
          field
          message
          code
        }
        webhook {
          id
        }
      }
    }
"""

STAFF_POINTER_MESSAGE = (
    "Webhook identifier can only be used by an app to reference its own webhook. "
    "Use `id` instead."
)
POINTER_REQUIRED_MESSAGE = "At least one of arguments is required: 'id', 'identifier'."
POINTER_COMBINED_MESSAGE = "Argument 'id' cannot be combined with 'identifier'"


def test_webhook_delete_by_identifier(app_api_client, webhook_with_identifier):
    # given
    variables = {"identifier": webhook_with_identifier.identifier}

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_DELETE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["webhookDelete"]["errors"] == []
    assert Webhook.objects.filter(pk=webhook_with_identifier.pk).exists() is False


@pytest.mark.parametrize(
    ("_case", "client_fixture"),
    [
        ("Unauthenticated user should be rejected", "api_client"),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
        ),
        ("Staff user without the permission should be rejected", "staff_api_client"),
    ],
)
def test_webhook_delete_by_identifier_by_unauthorized_client(
    _case, client_fixture, request, webhook_with_identifier
):
    # given
    client = request.getfixturevalue(client_fixture)
    variables = {"identifier": webhook_with_identifier.identifier}

    # when
    response = client.post_graphql(WEBHOOK_DELETE_BY_POINTER, variables=variables)

    # then
    assert_no_permission(response)
    assert Webhook.objects.filter(pk=webhook_with_identifier.pk).exists() is True


def test_webhook_delete_by_identifier_by_staff(
    staff_api_client, permission_manage_apps, webhook_with_identifier
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"identifier": webhook_with_identifier.identifier}

    # when
    response = staff_api_client.post_graphql(
        WEBHOOK_DELETE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookDelete"]
    assert data["webhook"] is None
    assert data["errors"] == [
        {
            "field": "identifier",
            "message": STAFF_POINTER_MESSAGE,
            "code": WebhookErrorCode.INVALID.name,
        }
    ]
    assert Webhook.objects.filter(pk=webhook_with_identifier.pk).exists() is True


def test_webhook_delete_by_identifier_of_another_app(
    app_api_client, webhook_with_identifier
):
    # given
    other_app = App.objects.create(name="other")
    other_webhook = Webhook.objects.create(
        app=other_app,
        target_url="http://www.example.com/other",
        identifier="other-app-handler",
    )
    variables = {"identifier": other_webhook.identifier}

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_DELETE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookDelete"]
    assert data["webhook"] is None
    assert data["errors"] == [
        {
            "field": "identifier",
            "message": f"Couldn't resolve to a node: {other_webhook.identifier}",
            "code": WebhookErrorCode.NOT_FOUND.name,
        }
    ]
    assert Webhook.objects.filter(pk=other_webhook.pk).exists() is True


def test_webhook_delete_with_both_pointers(app_api_client, webhook_with_identifier):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Webhook", webhook_with_identifier.pk),
        "identifier": webhook_with_identifier.identifier,
    }

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_DELETE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookDelete"]
    assert data["webhook"] is None
    assert data["errors"] == [
        {
            "field": None,
            "message": POINTER_COMBINED_MESSAGE,
            "code": WebhookErrorCode.GRAPHQL_ERROR.name,
        }
    ]
    assert Webhook.objects.filter(pk=webhook_with_identifier.pk).exists() is True


@pytest.mark.parametrize(
    ("_case", "variables"),
    [
        ("identifier omitted", {}),
        ("identifier explicitly null", {"identifier": None}),
        ("identifier blank", {"identifier": ""}),
    ],
)
def test_webhook_delete_without_pointer(
    _case, variables, app_api_client, webhook_with_identifier
):
    # when
    response = app_api_client.post_graphql(
        WEBHOOK_DELETE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookDelete"]
    assert data["webhook"] is None
    assert data["errors"] == [
        {
            "field": None,
            "message": POINTER_REQUIRED_MESSAGE,
            "code": WebhookErrorCode.GRAPHQL_ERROR.name,
        }
    ]
    assert Webhook.objects.filter(pk=webhook_with_identifier.pk).exists() is True


@pytest.mark.parametrize(
    ("_case", "identifier"),
    [
        ("identifier explicitly null", None),
        ("identifier blank", ""),
    ],
)
def test_webhook_delete_by_id_with_falsy_identifier(
    _case, identifier, app_api_client, webhook_with_identifier
):
    # given - a falsy identifier counts as not provided, so `id` still resolves
    variables = {
        "id": graphene.Node.to_global_id("Webhook", webhook_with_identifier.pk),
        "identifier": identifier,
    }

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_DELETE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["webhookDelete"]["errors"] == []
    assert Webhook.objects.filter(pk=webhook_with_identifier.pk).exists() is False


def test_webhook_delete_null_identifier_never_matches_webhook_without_identifier(
    app_api_client, webhook
):
    # given - the app owns a webhook whose identifier is NULL
    assert webhook.identifier is None
    variables = {"identifier": None}

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_DELETE_BY_POINTER, variables=variables
    )

    # then - the NULL-identifier webhook must not be resolved by a null pointer
    content = get_graphql_content(response)
    assert content["data"]["webhookDelete"]["errors"] == [
        {
            "field": None,
            "message": POINTER_REQUIRED_MESSAGE,
            "code": WebhookErrorCode.GRAPHQL_ERROR.name,
        }
    ]
    assert Webhook.objects.filter(pk=webhook.pk).exists() is True
