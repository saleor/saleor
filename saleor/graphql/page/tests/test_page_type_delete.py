from unittest.mock import patch

import graphene
import pytest

from ....attribute.utils import associate_attribute_values_to_instance
from ....page.models import Page
from ...tests.utils import assert_no_permission, get_graphql_content

DELETE_PAGE_TYPE_MUTATION = """
    mutation DeletePageType($id: ID!) {
        pageTypeDelete(id: $id) {
            pageType {
                id
                name
                slug
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_page_type_delete_by_staff(
    staff_api_client, page_type, page, permission_manage_page_types_and_attributes
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )

    pages_pks = list(page_type.pages.values_list("pk", flat=True))

    assert pages_pks

    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {"id": page_type_id}

    # when
    response = staff_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeDelete"]

    assert not data["errors"]
    assert data["pageType"]["id"] == page_type_id

    with pytest.raises(page_type._meta.model.DoesNotExist):
        page_type.refresh_from_db()

    # ensure that corresponding pages has been removed
    assert not Page.objects.filter(pk__in=pages_pks)


def test_page_type_delete_by_staff_no_perm(
    staff_api_client, page_type, page, permission_manage_page_types_and_attributes
):
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {"id": page_type_id}

    # when
    response = staff_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_page_type_delete_by_app(
    app_api_client, page_type, page, permission_manage_page_types_and_attributes
):
    # given
    app_api_client.app.permissions.add(permission_manage_page_types_and_attributes)

    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    pages_pks = list(page_type.pages.values_list("pk", flat=True))

    assert pages_pks

    variables = {"id": page_type_id}

    # when
    response = app_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeDelete"]

    assert not data["errors"]
    assert data["pageType"]["id"] == page_type_id

    with pytest.raises(page_type._meta.model.DoesNotExist):
        page_type.refresh_from_db()

    # ensure that corresponding pages has been removed
    assert not Page.objects.filter(pk__in=pages_pks)


def test_page_type_delete_by_app_no_perm(
    app_api_client, page_type, page, permission_manage_page_types_and_attributes
):
    # given
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {"id": page_type_id}

    # when
    response = app_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.attribute.signals.delete_from_storage_task.delay")
def test_page_type_delete_with_file_attributes(
    delete_from_storage_task_mock,
    staff_api_client,
    page_type,
    page,
    page_file_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )
    page_type = page.page_type
    page_type.page_attributes.add(page_file_attribute)

    value = page_file_attribute.values.first()
    associate_attribute_values_to_instance(page, page_file_attribute, value)
    page_type_id = graphene.Node.to_global_id("PageType", page_type.pk)

    variables = {"id": page_type_id}

    # when
    response = staff_api_client.post_graphql(DELETE_PAGE_TYPE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeDelete"]

    assert not data["errors"]
    assert data["pageType"]["id"] == page_type_id

    with pytest.raises(page_type._meta.model.DoesNotExist):
        page_type.refresh_from_db()
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()

    delete_from_storage_task_mock.assert_called_once_with(value.file_url)
