from .....app.models import AppProblem, AppProblemSeverity, AppProblemType
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_CREATE_MUTATION = """
    mutation AppProblemCreate($input: AppProblemCreateInput!) {
        appProblemCreate(input: $input) {
            app {
                id
                problems {
                    ... on AppProblemCustom {
                        message
                        aggregate
                        severity
                    }
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


def test_app_problem_create(app_api_client, app):
    # given
    variables = {"input": {"message": "Something went wrong"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Something went wrong"
    assert problems[0]["aggregate"] == ""
    assert problems[0]["severity"] == "ERROR"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.type == AppProblemType.CUSTOM
    assert db_problem.message == "Something went wrong"
    assert db_problem.severity == AppProblemSeverity.ERROR


def test_app_problem_create_with_aggregate(app_api_client, app):
    # given
    variables = {"input": {"message": "Connection failed", "aggregate": "webhook-123"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Connection failed"
    assert problems[0]["aggregate"] == "webhook-123"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.aggregate == "webhook-123"


def test_app_problem_create_with_warning_severity(app_api_client, app):
    # given
    variables = {"input": {"message": "Degraded performance", "severity": "WARNING"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Degraded performance"
    assert problems[0]["severity"] == "WARNING"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.severity == AppProblemSeverity.WARNING


def test_app_problem_create_with_error_severity(app_api_client, app):
    # given
    variables = {"input": {"message": "Fatal failure", "severity": "ERROR"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    problems = data["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["severity"] == "ERROR"

    db_problem = AppProblem.objects.get(app=app)
    assert db_problem.severity == AppProblemSeverity.ERROR


def test_app_problem_create_by_staff_user_fails(
    staff_api_client, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)
    variables = {"input": {"message": "Something went wrong"}}

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_app_problem_create_multiple(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.CUSTOM,
        message="Existing problem",
    )
    variables = {"input": {"message": "New problem"}}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CREATE_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemCreate"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 2
