import graphene

from ....page.models import Page
from ...tests.utils import assert_no_permission, get_graphql_content

PAGE_TYPE_BULK_DELETE_MUTATION = """
    mutation PageTypeBulkDelete($ids: [ID!]!) {
        pageTypeBulkDelete(ids: $ids) {
            count
            pageErrors {
                code
                field
                message
            }
        }
    }
"""


def test_page_type_bulk_delete_by_staff(
    staff_api_client, page_type_list, permission_manage_page_types_and_attributes
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )

    page_type_count = len(page_type_list)

    pages_pks = list(
        Page.objects.filter(page_type__in=page_type_list).values_list("pk", flat=True)
    )

    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", page_type.pk)
            for page_type in page_type_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_BULK_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeBulkDelete"]

    assert not data["pageErrors"]
    assert data["count"] == page_type_count

    assert not Page.objects.filter(pk__in=pages_pks)


def test_page_type_bulk_delete_by_staff_no_perm(
    staff_api_client, page_type_list, permission_manage_page_types_and_attributes
):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", page_type.pk)
            for page_type in page_type_list
        ]
    }

    # when
    response = staff_api_client.post_graphql(PAGE_TYPE_BULK_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_page_type_bulk_delete_by_app(
    app_api_client, page_type_list, permission_manage_page_types_and_attributes
):
    # given
    app_api_client.app.permissions.add(permission_manage_page_types_and_attributes)

    page_type_count = len(page_type_list)

    pages_pks = list(
        Page.objects.filter(page_type__in=page_type_list).values_list("pk", flat=True)
    )

    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", page_type.pk)
            for page_type in page_type_list
        ]
    }

    # when
    response = app_api_client.post_graphql(PAGE_TYPE_BULK_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeBulkDelete"]

    assert not data["pageErrors"]
    assert data["count"] == page_type_count

    assert not Page.objects.filter(pk__in=pages_pks)


def test_page_type_bulk_delete_by_app_no_perm(
    app_api_client, page_type_list, permission_manage_page_types_and_attributes
):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", page_type.pk)
            for page_type in page_type_list
        ]
    }

    # when
    response = app_api_client.post_graphql(PAGE_TYPE_BULK_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)
