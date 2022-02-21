from unittest import mock

import graphene
import pytest
from freezegun import freeze_time

from .....attribute.utils import associate_attribute_values_to_instance
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_page_payload
from ....tests.utils import get_graphql_content

PAGE_DELETE_MUTATION = """
    mutation DeletePage($id: ID!) {
        pageDelete(id: $id) {
            page {
                title
                id
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_page_delete_mutation(staff_api_client, page, permission_manage_pages):
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()


@freeze_time("1914-06-28 10:50")
@mock.patch("saleor.plugins.webhook.plugin._get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_delete_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    page,
    permission_manage_pages,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    variables = {"id": graphene.Node.to_global_id("Page", page.id)}
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()
    expected_data = generate_page_payload(page, staff_api_client.user)
    mocked_webhook_trigger.assert_called_once_with(
        expected_data, WebhookEventAsyncType.PAGE_DELETED, [any_webhook]
    )


@mock.patch("saleor.attribute.signals.delete_from_storage_task.delay")
def test_page_delete_with_file_attribute(
    delete_from_storage_task_mock,
    staff_api_client,
    page,
    permission_manage_pages,
    page_file_attribute,
):
    # given
    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)
    existing_value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(page, page_file_attribute, existing_value)

    variables = {"id": graphene.Node.to_global_id("Page", page.id)}

    # when
    response = staff_api_client.post_graphql(
        PAGE_DELETE_MUTATION, variables, permissions=[permission_manage_pages]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageDelete"]
    assert data["page"]["title"] == page.title
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()
    with pytest.raises(existing_value._meta.model.DoesNotExist):
        existing_value.refresh_from_db()
    delete_from_storage_task_mock.assert_called_once_with(existing_value.file_url)
