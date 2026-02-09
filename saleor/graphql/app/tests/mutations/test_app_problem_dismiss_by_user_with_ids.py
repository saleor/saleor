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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "Only app callers can use 'byApp'."


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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "Cannot specify more than 100 items."
