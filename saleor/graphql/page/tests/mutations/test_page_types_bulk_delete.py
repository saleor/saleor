from unittest import mock

import graphene
import pytest

from .....page.models import Page
from ....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import assert_no_permission, get_graphql_content

PAGE_TYPE_BULK_DELETE_MUTATION = """
    mutation PageTypeBulkDelete($ids: [ID!]!) {
        pageTypeBulkDelete(ids: $ids) {
            count
            errors {
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

    assert not data["errors"]
    assert data["count"] == page_type_count

    assert not Page.objects.filter(pk__in=pages_pks)


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_page_type_bulk_delete_trigger_webhooks(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    page_type_list,
    permission_manage_page_types_and_attributes,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )

    page_type_count = len(page_type_list)
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

    assert not data["errors"]
    assert data["count"] == page_type_count
    assert mocked_webhook_trigger.call_count == page_type_count


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

    assert not data["errors"]
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


def test_page_type_bulk_delete_with_file_attribute(
    app_api_client,
    page_type_list,
    page_file_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    app_api_client.app.permissions.add(permission_manage_page_types_and_attributes)

    page_type = page_type_list[1]

    page_type_count = len(page_type_list)

    page = Page.objects.filter(page_type=page_type.pk)[0]

    value = page_file_attribute.values.first()
    page_type.page_attributes.add(page_file_attribute)
    associate_attribute_values_to_instance(page, {page_file_attribute.pk: [value]})

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

    assert not data["errors"]
    assert data["count"] == page_type_count

    with pytest.raises(page_type._meta.model.DoesNotExist):
        page_type.refresh_from_db()
    with pytest.raises(value._meta.model.DoesNotExist):
        value.refresh_from_db()

    assert not Page.objects.filter(pk__in=pages_pks)


def test_page_type_bulk_delete_by_app_with_invalid_ids(
    app_api_client, page_type_list, permission_manage_page_types_and_attributes
):
    # given
    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", page_type.pk)
            for page_type in page_type_list
        ]
    }
    variables["ids"][0] = "invalid_id"

    # when
    response = app_api_client.post_graphql(
        PAGE_TYPE_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_page_types_and_attributes],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["pageTypeBulkDelete"]["errors"][0]

    assert errors["code"] == "GRAPHQL_ERROR"
