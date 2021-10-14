import graphene
import pytest

from .....app.models import App
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_apps_for_federation_query_count(
    staff_api_client,
    permission_manage_apps,
    django_assert_num_queries,
    count_queries,
):
    apps = App.objects.bulk_create(
        [
            App(name="app 1"),
            App(name="app 2"),
            App(name="app 3"),
        ]
    )

    query = """
        query GetAppInFederation($representations: [_Any]) {
            _entities(representations: $representations) {
                __typename
                ... on App {
                    id
                    name
                }
            }
        }
    """

    variables = {
        "representations": [
            {
                "__typename": "App",
                "id": graphene.Node.to_global_id("App", apps[0].pk),
            },
        ],
    }

    with django_assert_num_queries(4):
        response = staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_apps],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 1

    variables = {
        "representations": [
            {
                "__typename": "App",
                "id": graphene.Node.to_global_id("App", app.pk),
            }
            for app in apps
        ],
    }

    with django_assert_num_queries(4):
        response = staff_api_client.post_graphql(
            query,
            variables,
            permissions=[permission_manage_apps],
            check_no_permissions=False,
        )
        content = get_graphql_content(response)
        assert len(content["data"]["_entities"]) == 3
