from .....app.models import AppProblem, AppProblemType
from ....tests.utils import assert_no_permission, get_graphql_content

APP_PROBLEM_CLEAR_MUTATION = """
    mutation AppProblemClear($aggregate: String) {
        appProblemClear(aggregate: $aggregate) {
            app {
                id
                problems {
                    ... on AppProblemCustom {
                        message
                        aggregate
                    }
                    ... on AppProblemCircuitBreaker {
                        message
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


def test_app_problem_clear_all_custom(app_api_client, app):
    # given
    AppProblem.objects.create(app=app, type=AppProblemType.CUSTOM, message="Problem 1")
    AppProblem.objects.create(
        app=app, type=AppProblemType.CUSTOM, message="Problem 2", aggregate="group-a"
    )

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    assert AppProblem.objects.filter(app=app).count() == 0


def test_app_problem_clear_by_aggregate(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app, type=AppProblemType.CUSTOM, message="Problem 1", aggregate="group-a"
    )
    AppProblem.objects.create(
        app=app, type=AppProblemType.CUSTOM, message="Problem 2", aggregate="group-b"
    )
    variables = {"aggregate": "group-a"}

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    remaining = AppProblem.objects.filter(app=app)
    assert remaining.count() == 1
    assert remaining.first().aggregate == "group-b"


def test_app_problem_clear_does_not_remove_circuit_breaker(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app, type=AppProblemType.CUSTOM, message="Custom problem"
    )
    AppProblem.objects.create(
        app=app, type=AppProblemType.CIRCUIT_BREAKER, message="Breaker tripped"
    )

    # when
    response = app_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION)
    content = get_graphql_content(response)

    # then
    data = content["data"]["appProblemClear"]
    assert not data["errors"]
    remaining = AppProblem.objects.filter(app=app)
    assert remaining.count() == 1
    assert remaining.first().type == AppProblemType.CIRCUIT_BREAKER


def test_app_problem_clear_by_staff_user_fails(
    staff_api_client, permission_manage_apps
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_apps)

    # when
    response = staff_api_client.post_graphql(APP_PROBLEM_CLEAR_MUTATION)

    # then
    assert_no_permission(response)
