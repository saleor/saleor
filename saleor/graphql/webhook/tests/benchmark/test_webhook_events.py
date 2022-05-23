import pytest

from ....tests.utils import get_graphql_content

WEBHOOKS_QUERY = """
query {
    apps(first:100) {
        edges {
            node {
                webhooks {
                    id
                    name
                    targetUrl
                    isActive
                    asyncEvents {
                        name
                    }
                    syncEvents {
                        name
                    }
                    events {
                        name
                    }
                }
            }
        }
    }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_webhooks(
    staff_api_client, webhook_events, permission_manage_apps, count_queries
):
    content = get_graphql_content(
        staff_api_client.post_graphql(
            WEBHOOKS_QUERY,
            permissions=[permission_manage_apps],
            check_no_permissions=False,
        )
    )
    assert len(content["data"]["apps"]["edges"]) == 4
