import graphene

from .....app.types import AppConcurrency
from ....tests.utils import get_graphql_content

QUERY_APP_CONCURRENCY = """
    query ($id: ID!) {
        app(id: $id) {
            id
            concurrency
        }
    }
"""


def test_query_app_returns_default_concurrency(
    app_with_token,
    staff_api_client,
):
    # given
    app = app_with_token
    app_id = graphene.Node.to_global_id("App", app.id)

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_CONCURRENCY,
        variables={"id": app_id},
    )

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["app"]
    assert app_data["concurrency"] == AppConcurrency.LOW.upper()


def test_query_app_returns_concurrency(
    app_with_token,
    staff_api_client,
):
    # given
    app = app_with_token
    app.concurrency = AppConcurrency.HIGH
    app.save(update_fields=["concurrency"])
    app_id = graphene.Node.to_global_id("App", app.id)

    # when
    response = staff_api_client.post_graphql(
        QUERY_APP_CONCURRENCY,
        variables={"id": app_id},
    )

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["app"]
    assert app_data["concurrency"] == AppConcurrency.HIGH.upper()
