import graphene
import pytest

from .....attribute.models import AttributeValue
from .....page.models import Page
from ....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import get_graphql_content

PAGE_BULK_DELETE_MUTATION = """
    mutation pageBulkDelete($ids: [ID!]!) {
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


def test_page_bulk_delete_with_file_attribute(
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
    associate_attribute_values_to_instance(page, {page_file_attribute.pk: [value]})

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

    assert not Page.objects.filter(id__in=[page.id for page in page_list]).exists()


def test_page_delete_removes_reference_to_product(
    product_type_page_reference_attribute,
    page,
    product_type,
    product,
    staff_api_client,
    permission_manage_pages,
):
    query = PAGE_BULK_DELETE_MUTATION

    product_type.product_attributes.add(product_type_page_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page.title,
        slug=f"{product.pk}_{page.pk}",
        reference_page=page,
    )

    associate_attribute_values_to_instance(
        product, {product_type_page_reference_attribute.pk: [attr_value]}
    )

    reference_id = graphene.Node.to_global_id("Page", page.pk)

    variables = {"ids": [reference_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageBulkDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()

    assert not data["errors"]


def test_page_delete_removes_reference_to_product_variant(
    product_type_page_reference_attribute,
    staff_api_client,
    page,
    variant,
    permission_manage_pages,
):
    query = PAGE_BULK_DELETE_MUTATION

    product_type = variant.product.product_type
    product_type.variant_attributes.set([product_type_page_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page.title,
        slug=f"{variant.pk}_{page.pk}",
        reference_page=page,
    )

    associate_attribute_values_to_instance(
        variant, {product_type_page_reference_attribute.pk: [attr_value]}
    )

    reference_id = graphene.Node.to_global_id("Page", page.pk)

    variables = {"ids": [reference_id]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageBulkDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(page._meta.model.DoesNotExist):
        page.refresh_from_db()

    assert not data["errors"]


def test_page_delete_removes_reference_to_page(
    page_type_page_reference_attribute,
    staff_api_client,
    page_list,
    page_type,
    permission_manage_pages,
):
    page = page_list[0]
    page_ref = page_list[1]

    query = PAGE_BULK_DELETE_MUTATION

    page_type.page_attributes.add(page_type_page_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=page_type_page_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{page_ref.pk}",
        reference_page=page_ref,
    )

    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.pk: [attr_value]}
    )

    reference_id = graphene.Node.to_global_id("Page", page_ref.pk)

    variables = {"ids": [reference_id]}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    content = get_graphql_content(response)
    data = content["data"]["pageBulkDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(page_ref._meta.model.DoesNotExist):
        page_ref.refresh_from_db()

    assert not data["errors"]


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
