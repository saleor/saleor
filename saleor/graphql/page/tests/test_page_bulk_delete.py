from unittest import mock

import graphene
import pytest

from ....attribute.utils import associate_attribute_values_to_instance
from ....page.models import Page
from ...tests.utils import get_graphql_content

PAGE_BULK_DELETE_MUTATION = """
    mutation pageBulkDelete($ids: [ID]!) {
        pageBulkDelete(ids: $ids) {
            count
            errors {
                code
                field
                message
            }
        }
    }
"""


def test_delete_pages(staff_api_client, page_list, permission_manage_pages):
    query = PAGE_BULK_DELETE_MUTATION

    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.id) for page in page_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)

    assert content["data"]["pageBulkDelete"]["count"] == len(page_list)
    assert not Page.objects.filter(id__in=[page.id for page in page_list]).exists()


@mock.patch("saleor.attribute.signals.delete_from_storage_task.delay")
def test_page_bulk_delete_with_file_attribute(
    delete_from_storage_task_mock,
    app_api_client,
    page_list,
    page_file_attribute,
    permission_manage_pages,
):
    # given
    app_api_client.app.permissions.add(permission_manage_pages)

    page = page_list[1]
    page_count = len(page_list)
    page_type = page.page_type

    value = page_file_attribute.values.first()
    page_type.page_attributes.add(page_file_attribute)
    associate_attribute_values_to_instance(page, page_file_attribute, value)

    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.pk) for page in page_list]
    }
    # when
    response = app_api_client.post_graphql(PAGE_BULK_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageBulkDelete"]

    assert not data["errors"]
    assert data["count"] == page_count

    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()
    delete_from_storage_task_mock.assert_called_once_with(value.file_url)

    assert not Page.objects.filter(id__in=[page.id for page in page_list]).exists()


def test_bulk_delete_page_with_invalid_ids(
    staff_api_client, page_list, permission_manage_pages
):
    query = PAGE_BULK_DELETE_MUTATION

    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.id) for page in page_list]
    }
    variables["ids"][0] = "invalid_id"
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    errors = content["data"]["pageBulkDelete"]["errors"][0]

    assert errors["code"] == "GRAPHQL_ERROR"
