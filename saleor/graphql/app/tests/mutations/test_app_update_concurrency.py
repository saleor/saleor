import graphene

from .....app.types import AppConcurrency
from ....tests.utils import get_graphql_content

APP_UPDATE_CONCURRENCY_MUTATION = """
mutation AppUpdate($id: ID!, $concurrency: AppConcurrencyEnum) {
    appUpdate(id: $id, input: {concurrency: $concurrency}) {
        app {
            id
            concurrency
        }
        errors {
            field
            message
            code
        }
    }
}
"""


def test_update_app_concurrency(
    app_with_token,
    staff_api_client,
    permission_manage_apps,
):
    # given
    app = app_with_token
    app_id = graphene.Node.to_global_id("App", app.id)
    concurrency = AppConcurrency.HIGH

    # when
    response = staff_api_client.post_graphql(
        APP_UPDATE_CONCURRENCY_MUTATION,
        variables={"id": app_id, "concurrency": concurrency.upper()},
        permissions=[permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["appUpdate"]["app"]
    assert app_data["concurrency"] == concurrency.upper()

    app.refresh_from_db()
    assert app.concurrency == concurrency


def test_update_app_concurrency_to_sequential(
    app_with_token,
    staff_api_client,
    permission_manage_apps,
):
    # given
    app = app_with_token
    app.concurrency = AppConcurrency.HIGH
    app.save(update_fields=["concurrency"])
    app_id = graphene.Node.to_global_id("App", app.id)
    concurrency = AppConcurrency.SEQUENTIAL

    # when
    response = staff_api_client.post_graphql(
        APP_UPDATE_CONCURRENCY_MUTATION,
        variables={"id": app_id, "concurrency": concurrency.upper()},
        permissions=[permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    app_data = content["data"]["appUpdate"]["app"]
    assert app_data["concurrency"] == concurrency.upper()

    app.refresh_from_db()
    assert app.concurrency == concurrency
