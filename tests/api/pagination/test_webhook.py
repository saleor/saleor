import pytest

from saleor.app.models import App
from saleor.webhook.models import Webhook

from ..utils import get_graphql_content


@pytest.fixture
def webhooks_for_pagination(db):
    apps = App.objects.bulk_create(
        [App(name="App1", is_active=True), App(name="App2", is_active=True)]
    )

    return Webhook.objects.bulk_create(
        [
            Webhook(
                name="Webhook1",
                app=apps[1],
                target_url="http://www.example.com/test4",
                is_active=False,
            ),
            Webhook(
                name="WebhookWebhook1",
                app=apps[0],
                target_url="http://www.example.com/test2",
            ),
            Webhook(
                name="WebhookWebhook2",
                app=apps[1],
                target_url="http://www.example.com/test1",
            ),
            Webhook(
                name="Webhook2",
                app=apps[1],
                target_url="http://www.example.com/test3",
                is_active=False,
            ),
            Webhook(
                name="Webhook3", app=apps[0], target_url="http://www.example.com/test",
            ),
        ]
    )


QUERY_WEBHOOKS_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: WebhookSortingInput, $filter: WebhookFilterInput
    ){
        webhooks(
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            edges {
                node {
                    name
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


@pytest.mark.parametrize(
    "sort_by, webhooks_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["Webhook1", "Webhook2", "Webhook3"]),
        (
            {"field": "NAME", "direction": "DESC"},
            ["WebhookWebhook2", "WebhookWebhook1", "Webhook3"],
        ),
        (
            {"field": "APP", "direction": "ASC"},
            ["Webhook3", "WebhookWebhook1", "Webhook1"],
        ),
        (
            {"field": "SERVICE_ACCOUNT", "direction": "ASC"},
            ["Webhook3", "WebhookWebhook1", "Webhook1"],
        ),
        (
            {"field": "TARGET_URL", "direction": "ASC"},
            ["Webhook3", "WebhookWebhook2", "WebhookWebhook1"],
        ),
    ],
)
def test_webhooks_pagination_with_sorting(
    sort_by,
    webhooks_order,
    staff_api_client,
    permission_manage_webhooks,
    webhooks_for_pagination,
):
    page_size = 3

    variables = {"first": page_size, "after": None, "sortBy": sort_by}
    response = staff_api_client.post_graphql(
        QUERY_WEBHOOKS_PAGINATION, variables, permissions=[permission_manage_webhooks],
    )
    content = get_graphql_content(response)
    webhooks_nodes = content["data"]["webhooks"]["edges"]
    assert webhooks_order[0] == webhooks_nodes[0]["node"]["name"]
    assert webhooks_order[1] == webhooks_nodes[1]["node"]["name"]
    assert webhooks_order[2] == webhooks_nodes[2]["node"]["name"]
    assert len(webhooks_nodes) == page_size


@pytest.mark.parametrize(
    "filter_by, webhooks_order",
    [
        ({"search": "WebhookWebhook"}, ["WebhookWebhook1", "WebhookWebhook2"]),
        ({"search": "Webhook1"}, ["Webhook1", "WebhookWebhook1"]),
        ({"isActive": True}, ["WebhookWebhook1", "WebhookWebhook2"]),
    ],
)
def test_webhooks_pagination_with_filtering(
    filter_by,
    webhooks_order,
    staff_api_client,
    permission_manage_webhooks,
    webhooks_for_pagination,
):
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(
        QUERY_WEBHOOKS_PAGINATION, variables, permissions=[permission_manage_webhooks],
    )
    content = get_graphql_content(response)
    webhooks_nodes = content["data"]["webhooks"]["edges"]
    assert webhooks_order[0] == webhooks_nodes[0]["node"]["name"]
    assert webhooks_order[1] == webhooks_nodes[1]["node"]["name"]
    assert len(webhooks_nodes) == page_size
