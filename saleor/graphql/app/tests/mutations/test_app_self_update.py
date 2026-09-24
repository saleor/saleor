from unittest import mock

import pytest

from .....app.models import DEPRECATION_REASON_MAX_LENGTH
from ....tests.utils import assert_no_permission, get_graphql_content

APP_SELF_UPDATE_MUTATION = """
    mutation AppSelfUpdate($input: AppSelfUpdateInput!) {
        appSelfUpdate(input: $input) {
            app {
                id
                deprecationReason
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_sets_deprecation_reason(app_api_client, app):
    # given
    reason = "Replaced by the new payments app."
    assert app.deprecation_reason is None
    variables = {"input": {"deprecationReason": reason}}

    # when
    response = app_api_client.post_graphql(APP_SELF_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appSelfUpdate"]
    assert len(data["errors"]) == 0
    assert data["app"]["deprecationReason"] == reason

    app.refresh_from_db(fields=("deprecation_reason",))
    assert app.deprecation_reason == reason


@pytest.mark.parametrize("blank_value", ["", "   "])
def test_blank_value_clears_deprecation_reason(app_api_client, app, blank_value):
    # given
    app.deprecation_reason = "Sunsetting in January."
    app.save(update_fields=["deprecation_reason"])
    variables = {"input": {"deprecationReason": blank_value}}

    # when
    response = app_api_client.post_graphql(APP_SELF_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appSelfUpdate"]
    assert len(data["errors"]) == 0
    assert data["app"]["deprecationReason"] is None

    app.refresh_from_db(fields=("deprecation_reason",))
    assert app.deprecation_reason is None


@pytest.mark.parametrize("input_data", [{}, {"deprecationReason": None}])
def test_omitted_or_null_leaves_deprecation_reason_untouched(
    app_api_client, app, input_data
):
    """Guards the contract that future fields on this input won't wipe each other.

    Explicit `null` must behave like omitting the field, because clients
    commonly serialize unset fields as nulls. Only a blank string clears.
    """
    # given
    reason = "Sunsetting in January."
    app.deprecation_reason = reason
    app.save(update_fields=["deprecation_reason"])
    variables = {"input": input_data}

    # when
    response = app_api_client.post_graphql(APP_SELF_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appSelfUpdate"]
    assert len(data["errors"]) == 0
    assert data["app"]["deprecationReason"] == reason

    app.refresh_from_db(fields=("deprecation_reason",))
    assert app.deprecation_reason == reason


def test_over_long_deprecation_reason_is_truncated_not_rejected(app_api_client, app):
    # given
    reason = "x" * (DEPRECATION_REASON_MAX_LENGTH + 100)
    expected = "x" * (DEPRECATION_REASON_MAX_LENGTH - 3) + "..."
    variables = {"input": {"deprecationReason": reason}}

    # when
    response = app_api_client.post_graphql(APP_SELF_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appSelfUpdate"]
    assert len(data["errors"]) == 0
    assert data["app"]["deprecationReason"] == expected

    app.refresh_from_db(fields=("deprecation_reason",))
    assert app.deprecation_reason == expected
    assert len(app.deprecation_reason) == DEPRECATION_REASON_MAX_LENGTH


def test_value_at_max_length_is_stored_verbatim(app_api_client, app):
    # given
    reason = "x" * DEPRECATION_REASON_MAX_LENGTH
    variables = {"input": {"deprecationReason": reason}}

    # when
    response = app_api_client.post_graphql(APP_SELF_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appSelfUpdate"]
    assert len(data["errors"]) == 0
    assert data["app"]["deprecationReason"] == reason


def test_value_is_stripped(app_api_client, app):
    # given
    reason = "Replaced by the new payments app."
    variables = {"input": {"deprecationReason": f"  {reason}  "}}

    # when
    response = app_api_client.post_graphql(APP_SELF_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appSelfUpdate"]
    assert len(data["errors"]) == 0
    assert data["app"]["deprecationReason"] == reason


@mock.patch("saleor.plugins.manager.PluginsManager.app_updated")
def test_does_not_fire_app_updated_webhook(mocked_app_updated, app_api_client, app):
    """App lifecycle events are self-only, so the app would only notify itself."""
    # given
    variables = {"input": {"deprecationReason": "Replaced by the new payments app."}}

    # when
    response = app_api_client.post_graphql(APP_SELF_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["appSelfUpdate"]["errors"]) == 0
    assert mocked_app_updated.call_count == 0


@pytest.mark.parametrize(
    "api_client_fixture",
    ["staff_api_client", "superuser_api_client", "user_api_client", "api_client"],
)
def test_no_user_can_set_deprecation_reason(
    request, api_client_fixture, app, permission_manage_apps
):
    """Only the app itself may deprecate itself.

    No requestor that is not an app can do it - not staff (even holding
    MANAGE_APPS), not a superuser, not a customer, not an anonymous caller.
    `appUpdate` has no such field either.
    """
    # given
    assert app.deprecation_reason is None
    api_client = request.getfixturevalue(api_client_fixture)
    if api_client.user:
        api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"input": {"deprecationReason": "Deprecated by a user."}}

    # when
    response = api_client.post_graphql(APP_SELF_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)
    app.refresh_from_db(fields=("deprecation_reason",))
    assert app.deprecation_reason is None
