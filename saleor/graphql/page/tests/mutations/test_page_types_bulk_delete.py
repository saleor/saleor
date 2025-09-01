from unittest import mock

import graphene
import pytest

from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....page.models import Page
from .....product.search import update_products_search_vector
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


@mock.patch("saleor.graphql.page.bulk_mutations.get_webhooks_for_event")
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


def test_page_type_bulk_delete_sets_search_index_dirty_in_product_with_page_reference(
    staff_api_client,
    page_type_list,
    product,
    product_type_page_reference_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    # Set up page reference attribute
    attribute = product_type_page_reference_attribute
    product.product_type.product_attributes.add(attribute)

    # Use the first page type and create a page with a specific title
    page_type = page_type_list[0]
    page = Page.objects.filter(page_type=page_type).first()
    page.title = "Brand"
    page.save(update_fields=["title"])

    attr_value = AttributeValue.objects.create(
        attribute=attribute,
        name=page.title,
        slug=f"{product.pk}_{page.pk}",
        reference_page=page,
    )

    associate_attribute_values_to_instance(product, {attribute.pk: [attr_value]})

    # Ensure product search index is initially clean
    product.search_index_dirty = False
    product.save(update_fields=["search_index_dirty"])
    update_products_search_vector([product.id])
    product.refresh_from_db()
    assert page.title.lower() in product.search_vector

    # when
    variables = {
        "ids": [
            graphene.Node.to_global_id("PageType", page_type.pk)
            for page_type in page_type_list
        ]
    }
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )
    response = staff_api_client.post_graphql(PAGE_TYPE_BULK_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["pageTypeBulkDelete"]

    assert not data["errors"]
    assert data["count"] == len(page_type_list)

    # Check that page types were deleted
    for page_type in page_type_list:
        with pytest.raises(page_type._meta.model.DoesNotExist):
            page_type.refresh_from_db()

    # Check that page was deleted (cascade from page type)
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()

    # Check that attribute value was deleted
    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()

    # Check that product search_index_dirty flag was set to True
    product.refresh_from_db(fields=["search_index_dirty"])
    assert product.search_index_dirty is True

    # Verify search vector no longer contains the deleted page title
    update_products_search_vector([product.id])
    product.refresh_from_db()
    assert page.title.lower() not in product.search_vector
