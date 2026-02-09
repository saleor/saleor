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
    assert data["errors"][0]["code"] == AppProblemDismissErrorCode.INVALID.name
    assert data["errors"][0]["message"] == "Cannot specify more than 100 items."
