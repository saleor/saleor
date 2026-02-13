from .....app.models import AppProblem
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_CREATE_MUTATION = """
    mutation AppProblemCreate($input: AppProblemCreateInput!) {
        appProblemCreate(input: $input) {
            appProblem {
                id
                message
                key
                count
                isCritical
                updatedAt
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_app_problem_create(app_api_client, app):
    # given
    variables = {"input": {"message": "Something went wrong", "key": "error-1"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problem_data = data["appProblem"]
    assert problem_data["message"] == variables["input"]["message"]
    assert problem_data["key"] == variables["input"]["key"]
    assert problem_data["count"] == 1
    assert problem_data["isCritical"] is False

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.message == variables["input"]["message"]
    assert db_problem.key == variables["input"]["key"]
    assert db_problem.count == 1


def test_app_problem_create_by_staff_user_fails(
    staff_api_client, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"input": {"message": "Something went wrong", "key": "err"}}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)
