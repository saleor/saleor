import graphene

from .....app.models import AppProblem, AppProblemSeverity, AppProblemType
from ....tests.utils import get_graphql_content

QUERY_APP_PROBLEMS = """
    query ($id: ID) {
        app(id: $id) {
            id
            problems {
                ... on AppProblemOwn {
                    message
                    createdAt
                    aggregate
                    severity
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
        app=app, type=AppProblemType.OWN, message="Custom issue 1"
    )
    AppProblem.objects.create(
        app=app, type=AppProblemType.OWN, message="Custom issue 2"
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
        type=AppProblemType.OWN,
        message="Custom issue",
        aggregate="my-group",
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["message"] == "Custom issue"
    assert problems[0]["aggregate"] == "my-group"


def test_app_problems_ordered_by_created_at_desc(app_api_client, app):
    # given
    AppProblem.objects.create(app=app, type=AppProblemType.OWN, message="First")
    AppProblem.objects.create(app=app, type=AppProblemType.OWN, message="Second")
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


def test_app_problems_returns_severity(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.OWN,
        message="Warning issue",
        severity=AppProblemSeverity.WARNING,
    )
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.OWN,
        message="Error issue",
        severity=AppProblemSeverity.ERROR,
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 2
    severities = {p["message"]: p["severity"] for p in problems}
    assert severities["Warning issue"] == "WARNING"
    assert severities["Error issue"] == "ERROR"


def test_app_problems_default_severity_is_error(app_api_client, app):
    # given
    AppProblem.objects.create(
        app=app,
        type=AppProblemType.OWN,
        message="Default severity",
    )
    variables = {"id": graphene.Node.to_global_id("App", app.id)}

    # when
    response = app_api_client.post_graphql(QUERY_APP_PROBLEMS, variables)
    content = get_graphql_content(response)

    # then
    problems = content["data"]["app"]["problems"]
    assert len(problems) == 1
    assert problems[0]["severity"] == "ERROR"


def test_app_problems_cascade_delete(app, db):
    # given
    AppProblem.objects.create(app=app, type=AppProblemType.OWN, message="To be deleted")
    assert AppProblem.objects.count() == 1

    # when
    app.delete()

    # then
    assert AppProblem.objects.count() == 0
