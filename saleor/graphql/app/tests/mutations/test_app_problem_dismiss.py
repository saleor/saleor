import graphene
from django.utils import timezone

from .....app.models import AppProblem
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_DISMISS_MUTATION = """
    mutation AppProblemDismiss($input: AppProblemDismissInput!) {
        appProblemDismiss(input: $input) {
            app {
                id
                problems {
                    id
                    message
                    key
                    dismissed
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def _create_problem(app, key="test-key", message="Test problem", dismissed=False):
    return AppProblem.objects.create(
        app=app,
        message=message,
        key=key,
        updated_at=timezone.now(),
        dismissed=dismissed,
    )


# --- App caller tests (byApp) ---


def test_app_problem_dismiss_by_ids_as_app(app_api_client, app):
    # given
    p1 = _create_problem(app, key="k1", message="Problem 1")
    p2 = _create_problem(app, key="k2", message="Problem 2")
    variables = {
        "input": {
            "byApp": {
                "ids": [graphene.Node.to_global_id("AppProblem", p1.id)],
            }
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.dismissed is True
    assert p1.dismissed_by_user is None
    assert p2.dismissed is False


def test_app_problem_dismiss_by_keys_as_app(app_api_client, app):
    # given
    p1 = _create_problem(app, key="same-key", message="Problem 1")
    p2 = _create_problem(app, key="same-key", message="Problem 2")
    p3 = _create_problem(app, key="other-key", message="Problem 3")
    variables = {"input": {"byApp": {"keys": ["same-key"]}}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    p2.refresh_from_db()
    p3.refresh_from_db()
    assert p1.dismissed is True
    assert p2.dismissed is True
    assert p3.dismissed is False


def test_app_problem_dismiss_by_ids_and_keys_as_app_fails(app_api_client, app):
    # given - cannot specify both ids and keys
    p1 = _create_problem(app, key="k1", message="Problem 1")
    variables = {
        "input": {
            "byApp": {
                "ids": [graphene.Node.to_global_id("AppProblem", p1.id)],
                "keys": ["k2"],
            }
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "byApp"
    assert data["errors"][0]["code"] == "INVALID"


# --- Staff caller tests (byUserWithIds / byUserWithKeys) ---


def test_app_problem_dismiss_by_ids_as_staff(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = _create_problem(app, key="k1")
    variables = {
        "input": {
            "byUserWithIds": {
                "ids": [graphene.Node.to_global_id("AppProblem", p1.id)],
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    assert p1.dismissed is True
    assert p1.dismissed_by_user == staff_api_client.user


def test_app_problem_dismiss_by_keys_as_staff(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = _create_problem(app, key="k1")
    variables = {
        "input": {
            "byUserWithKeys": {
                "keys": ["k1"],
                "app": graphene.Node.to_global_id("App", app.id),
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    assert p1.dismissed is True
    assert p1.dismissed_by_user == staff_api_client.user


# --- Validation error tests ---


def test_app_problem_dismiss_multiple_inputs_fails(app_api_client, app):
    # given
    p1 = _create_problem(app)
    variables = {
        "input": {
            "byApp": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]},
            "byUserWithIds": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]},
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "input"
    assert data["errors"][0]["code"] == "INVALID"


def test_app_problem_dismiss_no_input_fails(app_api_client, app):
    # given
    variables = {"input": {}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "input"
    assert data["errors"][0]["code"] == "REQUIRED"


def test_app_problem_dismiss_empty_by_app_fails(app_api_client, app):
    # given - byApp provided but without ids or keys
    variables = {"input": {"byApp": {}}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "byApp"
    assert data["errors"][0]["code"] == "REQUIRED"


def test_app_caller_cannot_use_by_user_with_ids(app_api_client, app):
    # given - app caller tries to use byUserWithIds
    p1 = _create_problem(app)
    variables = {
        "input": {
            "byUserWithIds": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]}
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "byUserWithIds"
    assert data["errors"][0]["code"] == "INVALID"


def test_app_caller_cannot_use_by_user_with_keys(app_api_client, app):
    # given - app caller tries to use byUserWithKeys
    variables = {
        "input": {
            "byUserWithKeys": {
                "keys": ["k1"],
                "app": graphene.Node.to_global_id("App", app.id),
            }
        }
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "byUserWithKeys"
    assert data["errors"][0]["code"] == "INVALID"


def test_user_caller_cannot_use_by_app(staff_api_client, app, permission_manage_apps):
    # given - staff caller tries to use byApp
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = _create_problem(app)
    variables = {
        "input": {"byApp": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]}}
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "byApp"
    assert data["errors"][0]["code"] == "INVALID"


# --- Permission tests ---


def test_app_problem_dismiss_without_permission(staff_api_client, app):
    # given
    p1 = _create_problem(app)
    variables = {
        "input": {
            "byUserWithIds": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]}
        }
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)

    # then
    assert_no_permission(response)


# --- Idempotency and edge cases ---


def test_app_problem_dismiss_idempotent(app_api_client, app):
    # given - problem already dismissed
    p1 = _create_problem(app, key="k1", dismissed=True)
    variables = {
        "input": {"byApp": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]}}
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    assert p1.dismissed is True


def test_app_cannot_dismiss_other_apps_problems(app_api_client, app, app_with_token):
    # given - p1 belongs to a different app
    other_app = app_with_token
    p1 = _create_problem(other_app, key="k1")
    variables = {
        "input": {"byApp": {"ids": [graphene.Node.to_global_id("AppProblem", p1.id)]}}
    }

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then - error returned
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "ids"
    assert data["errors"][0]["code"] == "INVALID"
    p1.refresh_from_db()
    assert p1.dismissed is False
