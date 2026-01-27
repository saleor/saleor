import graphene

from .....app.models import AppProblem, AppProblemType
from ....tests.utils import get_graphql_content

QUERY_APP_PROBLEMS = """
    query ($id: ID) {
        app(id: $id) {
            id
            problems {
                ... on AppProblemCircuitBreaker {
                    message
                    createdAt
                }
                ... on AppProblemCustom {
                    message
                    createdAt
                    aggregate
                }
            }
        }
    }
"""


def test_app_problems_empty(app_api_client, app):
    # given
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["app"]
    assert data["problems"] == []


def test_app_problems_returns_problems(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app, type=AppProblemType.CUSTOM, message="Custom issue"
    )
    AppProblem.objects.create(
        app=app, type=AppProblemType.CIRCUIT_BREAKER, message="Breaker tripped"
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 2


def test_app_problems_union_resolution(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.CUSTOM,
        message="Custom issue",
        aggregate="my-group",
    )
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.CIRCUIT_BREAKER,
        message="Breaker tripped",
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    # Find each type
    custom_problems = [p for p in problems if "aggregate" in p]
    breaker_problems = [p for p in problems if "aggregate" not in p]

    assert len(custom_problems) == 1
    assert custom_problems[0]["message"] == "Custom issue"
    assert custom_problems[0]["aggregate"] == "my-group"

    assert len(breaker_problems) == 1
    assert breaker_problems[0]["message"] == "Breaker tripped"


def test_app_problems_ordered_by_created_at_desc(app_api_client, app):
    # given
    AppProblem.objects.create(app=app, type=AppProblemType.CUSTOM, message="First")
    AppProblem.objects.create(app=app, type=AppProblemType.CUSTOM, message="Second")
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 2
    # Most recent first
    assert problems[0]["message"] == "Second"
    assert problems[1]["message"] == "First"


def test_app_problems_cascade_delete(app, db):
    # given
    AppProblem.objects.create(
        app=app, type=AppProblemType.CUSTOM, message="To be deleted"
    )
    assert AppProblem.objects.count() == 1

    # when
    app.delete()

    # then
    assert AppProblem.objects.count() == 0
