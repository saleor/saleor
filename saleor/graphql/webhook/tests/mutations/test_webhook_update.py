import json
from unittest.mock import patch

import graphene
import pytest

from .....app.models import App
from .....webhook.models import Webhook
from ....core.enums import WebhookErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import WebhookEventTypeAsyncEnum

WEBHOOK_UPDATE = """
    mutation webhookUpdate ($id: ID!, $input: WebhookUpdateInput!) {
      webhookUpdate(id: $id, input: $input) {
        errors {
          field
          message
          code
        }
        webhook {
          identifier
          syncEvents {
            eventType
          }
          asyncEvents {
            eventType
          }
          isActive
          customHeaders
        }
      }
    }
"""


def test_webhook_update_by_app(app_api_client, app, webhook):
    # given
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    custom_headers = {"x-key": "Value", "authorization-key": "Value"}
    variables = {
        "id": webhook_id,
        "input": {
            "asyncEvents": [WebhookEventTypeAsyncEnum.ORDER_CREATED.name],
            "isActive": False,
            "customHeaders": json.dumps(custom_headers),
        },
    }
    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)
    content = get_graphql_content(response)
    webhook.refresh_from_db()

    # then
    assert webhook.is_active is False
    assert webhook.filterable_channel_slugs == []
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeAsyncEnum.ORDER_CREATED.value

    data = content["data"]["webhookUpdate"]
    assert not data["errors"]
    assert len(data["webhook"]["asyncEvents"]) == 1
    assert (
        data["webhook"]["asyncEvents"][0]["eventType"]
        == WebhookEventTypeAsyncEnum.ORDER_CREATED.name
    )
    assert data["webhook"]["isActive"] is False
    assert data["webhook"]["customHeaders"] == json.dumps(custom_headers)


def test_webhook_update_identifier(app_api_client, webhook):
    # given
    identifier = "order-created-handler"
    assert webhook.identifier is None
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id, "input": {"identifier": identifier}}

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert not data["errors"]
    assert data["webhook"]["identifier"] == identifier
    webhook.refresh_from_db()
    assert webhook.identifier == identifier


def test_webhook_update_blank_identifier_clears_it(app_api_client, webhook):
    # given
    webhook.identifier = "order-created-handler"
    webhook.save(update_fields=["identifier"])
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id, "input": {"identifier": "   "}}

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)

    # then - blank clears the identifier back to NULL
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert not data["errors"]
    assert data["webhook"]["identifier"] is None
    webhook.refresh_from_db()
    assert webhook.identifier is None


def test_webhook_update_duplicate_identifier_for_same_app(app_api_client, app, webhook):
    # given - the app owns another webhook already using the target identifier
    identifier = "order-created-handler"
    Webhook.objects.create(
        app=app, target_url="https://www.example.com/other", identifier=identifier
    )
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id, "input": {"identifier": identifier}}

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)

    # then - rejected and the webhook keeps its previous (unset) identifier
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert data["errors"] == [
        {
            "field": None,
            "message": "Webhook with this App and Identifier already exists.",
            "code": WebhookErrorCode.UNIQUE.name,
        }
    ]
    webhook.refresh_from_db()
    assert webhook.identifier is None


def test_webhook_update_by_other_app(app_api_client, webhook):
    # given
    other_app = App.objects.create(name="other")
    webhook.app = other_app
    webhook.save()
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id, "input": {"isActive": False}}

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)
    content = get_graphql_content(response)
    errors = content["data"]["webhookUpdate"]["errors"]
    webhook.refresh_from_db()

    # then
    assert errors[0]["code"] == "NOT_FOUND"
    assert webhook.is_active is True


def test_webhook_update_by_inactive_app(app_api_client, webhook):
    # given
    app = webhook.app
    app.is_active = False
    app.save()
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id, "input": {"isActive": False}}

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)

    # then
    assert_no_permission(response)


def test_webhook_update_app_cant_change_webhooks_ownership(
    app_api_client, app, webhook
):
    # given
    other_app = App.objects.create(name="other")
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    other_app_id = graphene.Node.to_global_id("App", other_app.pk)
    variables = {"id": webhook_id, "input": {"app": other_app_id, "isActive": False}}

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)
    content = get_graphql_content(response)
    errors = content["data"]["webhookUpdate"]["errors"]
    webhook.refresh_from_db()

    # then
    assert len(errors) == 0
    assert webhook.app_id == app.id
    assert webhook.is_active is False


def test_webhook_update_by_app_and_missing_webhook(app_api_client, webhook):
    # given
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {"id": webhook_id, "input": {"isActive": False}}
    webhook.delete()

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)
    content = get_graphql_content(response)

    # then
    errors = content["data"]["webhookUpdate"]["errors"]
    assert errors[0]["code"] == "NOT_FOUND"


def test_webhook_update_when_app_doesnt_exist(app_api_client, app):
    # given
    app.delete()
    webhook_id = graphene.Node.to_global_id("Webhook", 1)
    variables = {"id": webhook_id, "input": {"isActive": False}}

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)

    # then
    assert_no_permission(response)


def test_webhook_update_by_staff(staff_api_client, webhook, permission_manage_apps):
    # given
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    custom_headers = {"x-key": "Value", "authorization-key": "Value"}
    variables = {
        "id": webhook_id,
        "input": {
            "asyncEvents": [
                WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.name,
                WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.name,
            ],
            "isActive": False,
            "customHeaders": json.dumps(custom_headers),
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)
    webhook.refresh_from_db()

    # then
    assert webhook.is_active is False
    assert webhook.filterable_channel_slugs == []
    assert webhook.custom_headers == {"x-key": "Value", "authorization-key": "Value"}
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.value

    data = content["data"]["webhookUpdate"]
    assert not data["errors"]
    assert (
        data["webhook"]["asyncEvents"][0]["eventType"]
        == WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.name
    )
    assert data["webhook"]["isActive"] is False
    assert data["webhook"]["customHeaders"] == json.dumps(custom_headers)


def test_webhook_update_by_staff_for_removed_app(
    staff_api_client, webhook_removed_app, permission_manage_apps
):
    # given
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook_removed_app.pk)
    custom_headers = {"x-key": "Value", "authorization-key": "Value"}
    variables = {
        "id": webhook_id,
        "input": {
            "asyncEvents": [
                WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.name,
                WebhookEventTypeAsyncEnum.CUSTOMER_CREATED.name,
            ],
            "isActive": False,
            "customHeaders": json.dumps(custom_headers),
        },
    }
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    response = staff_api_client.post_graphql(query, variables=variables)

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["webhookUpdate"]
    assert app_data["webhook"] is None
    assert app_data["errors"][0]["code"] == WebhookErrorCode.NOT_FOUND.name
    assert app_data["errors"][0]["field"] == "id"


def test_webhook_update_by_staff_without_permission(staff_api_client, app, webhook):
    # given
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

    # when
    response = staff_api_client.post_graphql(query, variables=variables)

    # then
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


def test_webhook_update_invalid_custom_headers(
    staff_api_client,
    webhook,
    permission_manage_apps,
):
    # given
    query = WEBHOOK_UPDATE
    custom_headers = {"DisallowedKey": "Value"}
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {
        "id": webhook_id,
        "input": {
            "customHeaders": json.dumps(custom_headers),
        },
    }

    # when
    response = staff_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookUpdate"]
    assert not data["webhook"]
    error = data["errors"][0]
    assert error["field"] == "customHeaders"
    assert (
        error["message"] == '"DisallowedKey" does not match allowed key pattern: '
        '"X-*", "Authorization*", or "BrokerProperties".'
    )
    assert error["code"] == WebhookErrorCode.INVALID_CUSTOM_HEADERS.name


def test_webhook_update_notify_user_with_another_event(app_api_client, webhook):
    # given
    query = WEBHOOK_UPDATE
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    variables = {
        "id": webhook_id,
        "input": {
            "name": "NOTIFY_USER with another event fails to save",
            "targetUrl": "https://www.example.com",
            "asyncEvents": [
                WebhookEventTypeAsyncEnum.ORDER_CREATED.name,
                WebhookEventTypeAsyncEnum.NOTIFY_USER.name,
            ],
        },
    }

    # when
    response = app_api_client.post_graphql(query, variables=variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["webhookUpdate"]
    assert not data["webhook"]
    error = data["errors"][0]
    assert error["field"] == "asyncEvents"
    assert error["code"] == WebhookErrorCode.INVALID_NOTIFY_WITH_SUBSCRIPTION.name


FILTERABLE_SUBSCRIPTION = """
subscription {
  orderCreated(channels: [%s]) {
    order {
      id
      number
      lines {
        id
        variant {
          id
        }
      }
    }
  }
}
"""


@pytest.mark.parametrize(
    ("channel_slugs", "previous_slugs"),
    [
        (["channel-1", "channel-2"], ["previous-channel"]),
        (["channel-1"], ["previous-channel"]),
        (["channel-1"], ["channel-1"]),
        (["channel-1", "channel-2"], []),
        ([], ["previous-channel"]),
    ],
)
def test_webhook_update_filterable_channel_slugs(
    channel_slugs, previous_slugs, app_api_client, app, webhook
):
    # given
    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    webhook.filterable_channel_slugs = previous_slugs
    webhook.save()
    variables = {
        "id": webhook_id,
        "input": {
            "query": FILTERABLE_SUBSCRIPTION
            % ",".join([f'"{slug}"' for slug in channel_slugs])
        },
    }

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)
    get_graphql_content(response)
    webhook.refresh_from_db()

    # then
    assert webhook.filterable_channel_slugs == channel_slugs
    events = webhook.events.all()
    assert len(events) == 1
    assert events[0].event_type == WebhookEventTypeAsyncEnum.ORDER_CREATED.value


@pytest.mark.parametrize(
    "channel_slugs",
    [
        ["channel-1", "channel-2"],
        ["channel-1", "channel-2", "channel-3"],
    ],
)
@patch(
    "saleor.graphql.webhook.mutations.webhook_create.MAX_FILTERABLE_CHANNEL_SLUGS_LIMIT"
)
def test_webhook_create_assigns_filterable_channel_slugs_above_max_limit(
    mocked_limit, channel_slugs, app_api_client, webhook
):
    # given
    mocked_limit.__lt__ = lambda self, compare: True

    webhook_id = graphene.Node.to_global_id("Webhook", webhook.pk)
    webhook.filterable_channel_slugs = ["previous-channel"]
    webhook.save()

    variables = {
        "id": webhook_id,
        "input": {
            "query": FILTERABLE_SUBSCRIPTION
            % ",".join([f'"{slug}"' for slug in channel_slugs])
        },
    }

    # when
    response = app_api_client.post_graphql(WEBHOOK_UPDATE, variables=variables)
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["webhookUpdate"]["errors"]) == 1
    error = content["data"]["webhookUpdate"]["errors"][0]
    assert error["field"] == "query"
    assert error["code"] == WebhookErrorCode.INVALID.name


WEBHOOK_UPDATE_BY_POINTER = """
    mutation webhookUpdate($id: ID, $identifier: String, $input: WebhookUpdateInput!) {
      webhookUpdate(id: $id, identifier: $identifier, input: $input) {
        errors {
          field
          message
          code
        }
        webhook {
          id
          identifier
          isActive
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


def test_webhook_update_by_identifier(app_api_client, webhook_with_identifier):
    # given
    assert webhook_with_identifier.is_active is True
    variables = {
        "identifier": webhook_with_identifier.identifier,
        "input": {"isActive": False},
    }

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert data["errors"] == []
    assert data["webhook"]["identifier"] == webhook_with_identifier.identifier
    assert data["webhook"]["isActive"] is False
    webhook_with_identifier.refresh_from_db(fields=("is_active",))
    assert webhook_with_identifier.is_active is False


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
def test_webhook_update_by_identifier_by_unauthorized_client(
    _case, client_fixture, request, webhook_with_identifier
):
    # given
    client = request.getfixturevalue(client_fixture)
    variables = {
        "identifier": webhook_with_identifier.identifier,
        "input": {"isActive": False},
    }

    # when
    response = client.post_graphql(WEBHOOK_UPDATE_BY_POINTER, variables=variables)

    # then
    assert_no_permission(response)
    webhook_with_identifier.refresh_from_db(fields=("is_active",))
    assert webhook_with_identifier.is_active is True


def test_webhook_update_by_identifier_by_staff(
    staff_api_client, permission_manage_apps, webhook_with_identifier
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {
        "identifier": webhook_with_identifier.identifier,
        "input": {"isActive": False},
    }

    # when
    response = staff_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert data["webhook"] is None
    assert data["errors"] == [
        {
            "field": "identifier",
            "message": STAFF_POINTER_MESSAGE,
            "code": WebhookErrorCode.INVALID.name,
        }
    ]
    webhook_with_identifier.refresh_from_db(fields=("is_active",))
    assert webhook_with_identifier.is_active is True


def test_webhook_update_by_identifier_of_another_app(
    app_api_client, webhook_with_identifier
):
    # given
    other_app = App.objects.create(name="other")
    other_webhook = Webhook.objects.create(
        app=other_app,
        target_url="http://www.example.com/other",
        identifier="other-app-handler",
    )
    variables = {"identifier": other_webhook.identifier, "input": {"isActive": False}}

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert data["webhook"] is None
    assert data["errors"] == [
        {
            "field": "identifier",
            "message": f"Couldn't resolve to a node: {other_webhook.identifier}",
            "code": WebhookErrorCode.NOT_FOUND.name,
        }
    ]
    other_webhook.refresh_from_db(fields=("is_active",))
    assert other_webhook.is_active is True


def test_webhook_update_by_identifier_renames_identifier(
    app_api_client, webhook_with_identifier
):
    # given
    new_identifier = "order-created-handler-v2"
    variables = {
        "identifier": webhook_with_identifier.identifier,
        "input": {"identifier": new_identifier},
    }

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert data["errors"] == []
    assert data["webhook"]["identifier"] == new_identifier
    webhook_with_identifier.refresh_from_db(fields=("identifier",))
    assert webhook_with_identifier.identifier == new_identifier


def test_webhook_update_by_identifier_rename_to_taken_identifier(
    app_api_client, app, webhook_with_identifier
):
    # given
    taken_identifier = "already-taken"
    previous_identifier = webhook_with_identifier.identifier
    Webhook.objects.create(
        app=app,
        target_url="http://www.example.com/other",
        identifier=taken_identifier,
    )
    variables = {
        "identifier": previous_identifier,
        "input": {"identifier": taken_identifier},
    }

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["webhookUpdate"]["errors"] == [
        {
            "field": None,
            "message": "Webhook with this App and Identifier already exists.",
            "code": WebhookErrorCode.UNIQUE.name,
        }
    ]
    webhook_with_identifier.refresh_from_db(fields=("identifier",))
    assert webhook_with_identifier.identifier == previous_identifier


def test_webhook_update_with_both_pointers(app_api_client, webhook_with_identifier):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Webhook", webhook_with_identifier.pk),
        "identifier": webhook_with_identifier.identifier,
        "input": {"isActive": False},
    }

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert data["webhook"] is None
    assert data["errors"] == [
        {
            "field": None,
            "message": POINTER_COMBINED_MESSAGE,
            "code": WebhookErrorCode.GRAPHQL_ERROR.name,
        }
    ]
    webhook_with_identifier.refresh_from_db(fields=("is_active",))
    assert webhook_with_identifier.is_active is True


@pytest.mark.parametrize(
    ("_case", "variables"),
    [
        ("identifier omitted", {"input": {"isActive": False}}),
        (
            "identifier explicitly null",
            {"identifier": None, "input": {"isActive": False}},
        ),
        ("identifier blank", {"identifier": "", "input": {"isActive": False}}),
    ],
)
def test_webhook_update_without_pointer(
    _case, variables, app_api_client, webhook_with_identifier
):
    # when
    response = app_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert data["webhook"] is None
    assert data["errors"] == [
        {
            "field": None,
            "message": POINTER_REQUIRED_MESSAGE,
            "code": WebhookErrorCode.GRAPHQL_ERROR.name,
        }
    ]
    webhook_with_identifier.refresh_from_db(fields=("is_active",))
    assert webhook_with_identifier.is_active is True


@pytest.mark.parametrize(
    ("_case", "identifier"),
    [
        ("identifier explicitly null", None),
        ("identifier blank", ""),
    ],
)
def test_webhook_update_by_id_with_falsy_identifier(
    _case, identifier, app_api_client, webhook_with_identifier
):
    # given - a falsy identifier counts as not provided, so `id` still resolves
    variables = {
        "id": graphene.Node.to_global_id("Webhook", webhook_with_identifier.pk),
        "identifier": identifier,
        "input": {"isActive": False},
    }

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["webhookUpdate"]
    assert data["errors"] == []
    assert data["webhook"]["isActive"] is False
    webhook_with_identifier.refresh_from_db(fields=("is_active",))
    assert webhook_with_identifier.is_active is False


def test_webhook_update_null_identifier_never_matches_webhook_without_identifier(
    app_api_client, webhook
):
    # given - the app owns a webhook whose identifier is NULL
    assert webhook.identifier is None
    variables = {"identifier": None, "input": {"isActive": False}}

    # when
    response = app_api_client.post_graphql(
        WEBHOOK_UPDATE_BY_POINTER, variables=variables
    )

    # then - the NULL-identifier webhook must not be resolved by a null pointer
    content = get_graphql_content(response)
    assert content["data"]["webhookUpdate"]["errors"] == [
        {
            "field": None,
            "message": POINTER_REQUIRED_MESSAGE,
            "code": WebhookErrorCode.GRAPHQL_ERROR.name,
        }
    ]
    webhook.refresh_from_db(fields=("is_active",))
    assert webhook.is_active is True
