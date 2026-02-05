import graphene

from ....tests.utils import assert_no_permission, get_graphql_content
from ...mutations.app_problem_dismiss import MAX_ITEMS_LIMIT

APP_PROBLEM_DISMISS_MUTATION = """
    mutation AppProblemDismiss($input: AppProblemDismissInput!) {
        appProblemDismiss(input: $input) {
            errors {
                field
                code
                message
            }
        }
    }
"""


# --- App caller tests (byApp) ---


def test_app_problem_dismiss_by_ids_as_app(app_api_client, app, app_problem_generator):
    # given
    p1 = app_problem_generator(app, key="k1", message="Problem 1")
    p2 = app_problem_generator(app, key="k2", message="Problem 2")
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
    assert p1.dismissed_by_user_email is None  # Dismissed by app, no email
    assert p1.dismissed_by_user is None
    assert p2.dismissed is False


def test_app_problem_dismiss_by_keys_as_app(app_api_client, app, app_problem_generator):
    # given
    p1 = app_problem_generator(app, key="same-key", message="Problem 1")
    p2 = app_problem_generator(app, key="same-key", message="Problem 2")
    p3 = app_problem_generator(app, key="other-key", message="Problem 3")
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


def test_app_problem_dismiss_by_ids_and_keys_as_app_fails(
    app_api_client, app, app_problem_generator
):
    # given - cannot specify both ids and keys
    p1 = app_problem_generator(app, key="k1", message="Problem 1")
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
    assert data["errors"][0]["message"] == "Cannot specify both 'ids' and 'keys'."


# --- Staff caller tests (byUserWithIds / byUserWithKeys) ---


def test_app_problem_dismiss_by_ids_as_staff(
    staff_api_client, app, permission_manage_apps, app_problem_generator
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = app_problem_generator(app, key="k1")
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
    assert p1.dismissed_by_user_email == staff_api_client.user.email
    assert p1.dismissed_by_user == staff_api_client.user


def test_app_problem_dismiss_by_keys_as_staff(
    staff_api_client, app, permission_manage_apps, app_problem_generator
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = app_problem_generator(app, key="k1")
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
    assert p1.dismissed_by_user_email == staff_api_client.user.email
    assert p1.dismissed_by_user == staff_api_client.user


# --- Validation error tests ---


def test_app_problem_dismiss_multiple_inputs_fails(
    app_api_client, app, app_problem_generator
):
    # given
    p1 = app_problem_generator(app)
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
    assert (
        data["errors"][0]["message"]
        == "Must provide exactly one of 'byApp', 'byUserWithIds', or 'byUserWithKeys'."
    )


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
    assert (
        data["errors"][0]["message"]
        == "Must provide one of 'byApp', 'byUserWithIds', or 'byUserWithKeys'."
    )


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
    assert data["errors"][0]["message"] == "Must provide either 'ids' or 'keys'."


def test_app_caller_cannot_use_by_user_with_ids(
    app_api_client, app, app_problem_generator
):
    # given - app caller tries to use byUserWithIds
    p1 = app_problem_generator(app)
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
    assert (
        data["errors"][0]["message"]
        == "App callers cannot use this input. Use 'byApp' instead."
    )


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
    assert (
        data["errors"][0]["message"]
        == "App callers cannot use this input. Use 'byApp' instead."
    )


def test_user_caller_cannot_use_by_app(
    staff_api_client, app, permission_manage_apps, app_problem_generator
):
    # given - staff caller tries to use byApp
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = app_problem_generator(app)
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
    assert data["errors"][0]["message"] == "Only app callers can use 'byApp'."


# --- Permission tests ---


def test_app_problem_dismiss_without_permission(
    staff_api_client, app, app_problem_generator
):
    # given
    p1 = app_problem_generator(app)
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


def test_app_problem_dismiss_idempotent(app_api_client, app, app_problem_generator):
    # given - problem already dismissed
    p1 = app_problem_generator(app, key="k1", dismissed=True)
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


def test_app_cannot_dismiss_other_apps_problems(
    app_api_client, app, app_with_token, app_problem_generator
):
    # given - p1 belongs to a different app
    other_app = app_with_token
    p1 = app_problem_generator(other_app, key="k1")
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
    assert (
        data["errors"][0]["message"]
        == "Cannot dismiss problems belonging to other apps."
    )
    p1.refresh_from_db()
    assert p1.dismissed is False


def test_staff_can_dismiss_problems_from_multiple_apps(
    staff_api_client, app, app_with_token, permission_manage_apps, app_problem_generator
):
    # given - problems from 2 different apps
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    p1 = app_problem_generator(app, key="k1", message="Problem from app 1")
    p2 = app_problem_generator(app_with_token, key="k2", message="Problem from app 2")
    variables = {
        "input": {
            "byUserWithIds": {
                "ids": [
                    graphene.Node.to_global_id("AppProblem", p1.id),
                    graphene.Node.to_global_id("AppProblem", p2.id),
                ]
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then - both problems should be dismissed
    data = content["data"]["appProblemDismiss"]
    assert not data["errors"]
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.dismissed is True
    assert p1.dismissed_by_user_email == staff_api_client.user.email
    assert p1.dismissed_by_user == staff_api_client.user
    assert p2.dismissed is True
    assert p2.dismissed_by_user_email == staff_api_client.user.email
    assert p2.dismissed_by_user == staff_api_client.user


# --- Max items limit tests ---


def test_app_problem_dismiss_by_app_with_too_many_ids_fails(app_api_client, app):
    # given
    ids = [
        graphene.Node.to_global_id("AppProblem", i) for i in range(MAX_ITEMS_LIMIT + 1)
    ]
    variables = {"input": {"byApp": {"ids": ids}}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "ids"
    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["message"] == "Cannot specify more than 100 IDs."


def test_app_problem_dismiss_by_app_with_too_many_keys_fails(app_api_client, app):
    # given
    keys = [f"key-{i}" for i in range(MAX_ITEMS_LIMIT + 1)]
    variables = {"input": {"byApp": {"keys": keys}}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "keys"
    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["message"] == "Cannot specify more than 100 keys."


def test_app_problem_dismiss_by_user_with_too_many_ids_fails(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    ids = [
        graphene.Node.to_global_id("AppProblem", i) for i in range(MAX_ITEMS_LIMIT + 1)
    ]
    variables = {"input": {"byUserWithIds": {"ids": ids}}}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "ids"
    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["message"] == "Cannot specify more than 100 IDs."


def test_app_problem_dismiss_by_user_with_too_many_keys_fails(
    staff_api_client, app, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    keys = [f"key-{i}" for i in range(MAX_ITEMS_LIMIT + 1)]
    variables = {
        "input": {
            "byUserWithKeys": {
                "keys": keys,
                "app": graphene.Node.to_global_id("App", app.id),
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_DISMISS_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemDismiss"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "keys"
    assert data["errors"][0]["code"] == "INVALID"
    assert data["errors"][0]["message"] == "Cannot specify more than 100 keys."
