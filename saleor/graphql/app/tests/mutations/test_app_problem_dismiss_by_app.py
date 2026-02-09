import graphene

from .....app.error_codes import AppProblemDismissErrorCode
from ....tests.utils import get_graphql_content
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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "Cannot specify both 'ids' and 'keys'."


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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert (
        data["errors"][0]["message"]
        == "Cannot dismiss problems belonging to other apps."
    )
    p1.refresh_from_db()
    assert p1.dismissed is False


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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert (
        data["errors"][0]["message"]
        == "App callers cannot use this input. Use 'byApp' instead."
    )


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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "Cannot specify more than 100 items."


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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "Cannot specify more than 100 items."
