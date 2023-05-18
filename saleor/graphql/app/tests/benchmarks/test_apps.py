import graphene
import pytest

from .....app.models import App, AppToken
from .....webhook.models import Webhook
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


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_apps_with_tokens_and_webhooks(
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

    webhooks = []
    app_tokens = []
    for app in apps:
        for i in range(3):
            webhooks.append(
                Webhook(
                    app=app,
                    target_url=f"http://www.example.com/{i}",
                    name=f"webhook{i}",
                )
            )
            app_tokens.append(
                AppToken(
                    app=app, name=f"token{i}", auth_token=f"auth_token-{app.name}-{i}"
                )
            )
    Webhook.objects.bulk_create(webhooks)
    AppToken.objects.bulk_create(app_tokens)

    query = """
        query apps {
            apps(first:100) {
                edges {
                    node {
                        id
                        tokens {
                            name
                            authToken
                        }
                        webhooks {
                            id
                            targetUrl
                        }
                    }
                }
            }
        }
    """

    response = staff_api_client.post_graphql(
        query,
        {},
        permissions=[permission_manage_apps],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    assert len(content["data"]["apps"]["edges"]) == 3
