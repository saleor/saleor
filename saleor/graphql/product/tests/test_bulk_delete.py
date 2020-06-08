from unittest.mock import patch

import graphene
import pytest

from ....product.models import (
    Attribute,
    AttributeValue,
    Category,
    Collection,
    Product,
    ProductImage,
    ProductType,
    ProductVariant,
)
from ...tests.utils import get_graphql_content


@pytest.fixture
def category_list():
    category_1 = Category.objects.create(name="Category 1", slug="category-1")
    category_2 = Category.objects.create(name="Category 2", slug="category-2")
    category_3 = Category.objects.create(name="Category 3", slug="category-3")
    return category_1, category_2, category_3


@pytest.fixture
def product_type_list():
    product_type_1 = ProductType.objects.create(name="Type 1", slug="type-1")
    product_type_2 = ProductType.objects.create(name="Type 2", slug="type-2")
    product_type_3 = ProductType.objects.create(name="Type 3", slug="type-3")
    return product_type_1, product_type_2, product_type_3


@pytest.fixture
def attribute_value_list(color_attribute):
    value_1 = AttributeValue.objects.create(
        slug="pink", name="Pink", attribute=color_attribute, value="#FF69B4"
    )
    value_2 = AttributeValue.objects.create(
        slug="white", name="White", attribute=color_attribute, value="#FFFFFF"
    )
    value_3 = AttributeValue.objects.create(
        slug="black", name="Black", attribute=color_attribute, value="#000000"
    )
    return value_1, value_2, value_3


def test_delete_attributes(
    staff_api_client, attribute_list, permission_manage_products
):
    query = """
    mutation attributeBulkDelete($ids: [ID]!) {
        attributeBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Attribute", attr.id) for attr in attribute_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeBulkDelete"]["count"] == 3
    assert not Attribute.objects.filter(
        id__in=[attr.id for attr in attribute_list]
    ).exists()


def test_delete_attribute_values(
    staff_api_client, attribute_value_list, permission_manage_products
):
    query = """
    mutation attributeValueBulkDelete($ids: [ID]!) {
        attributeValueBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("AttributeValue", val.id)
            for val in attribute_value_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["attributeValueBulkDelete"]["count"] == 3
    assert not AttributeValue.objects.filter(
        id__in=[val.id for val in attribute_value_list]
    ).exists()


MUTATION_CATEGORY_BULK_DELETE = """
    mutation categoryBulkDelete($ids: [ID]!) {
        categoryBulkDelete(ids: $ids) {
            count
        }
    }
"""


def test_delete_categories(staff_api_client, category_list, permission_manage_products):
    variables = {
        "ids": [
            graphene.Node.to_global_id("Category", category.id)
            for category in category_list
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    assert content["data"]["categoryBulkDelete"]["count"] == 3
    assert not Category.objects.filter(
        id__in=[category.id for category in category_list]
    ).exists()


@patch("saleor.product.utils.update_products_minimal_variant_prices_task")
def test_delete_categories_with_subcategories_and_products(
    mock_update_products_minimal_variant_prices_task,
    staff_api_client,
    category_list,
    permission_manage_products,
    product,
    category,
):
    product.category = category
    category.parent = category_list[0]
    product.save()
    category.save()

    parent_product = Product.objects.get(pk=product.pk)
    parent_product.slug = "parent-product"
    parent_product.id = None
    parent_product.category = category_list[0]
    parent_product.save()

    product_list = [product, parent_product]

    variables = {
        "ids": [
            graphene.Node.to_global_id("Category", category.id)
            for category in category_list
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_CATEGORY_BULK_DELETE,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    assert content["data"]["categoryBulkDelete"]["count"] == 3
    assert not Category.objects.filter(
        id__in=[category.id for category in category_list]
    ).exists()

    mock_update_products_minimal_variant_prices_task.delay.assert_called_once()
    (
        _call_args,
        call_kwargs,
    ) = mock_update_products_minimal_variant_prices_task.delay.call_args

    assert set(call_kwargs["product_ids"]) == set([p.pk for p in product_list])

    for product in product_list:
        product.refresh_from_db()
        assert not product.category
        assert not product.is_published
        assert not product.publication_date


def test_delete_collections(
    staff_api_client, collection_list, permission_manage_products
):
    query = """
    mutation collectionBulkDelete($ids: [ID]!) {
        collectionBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Collection", collection.id)
            for collection in collection_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["collectionBulkDelete"]["count"] == 3
    assert not Collection.objects.filter(
        id__in=[collection.id for collection in collection_list]
    ).exists()


def test_delete_products(staff_api_client, product_list, permission_manage_products):
    query = """
    mutation productBulkDelete($ids: [ID]!) {
        productBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productBulkDelete"]["count"] == 3
    assert not Product.objects.filter(
        id__in=[product.id for product in product_list]
    ).exists()


def test_delete_product_images(
    staff_api_client, product_with_images, permission_manage_products
):
    images = product_with_images.images.all()

    query = """
    mutation productImageBulkDelete($ids: [ID]!) {
        productImageBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductImage", image.id) for image in images
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productImageBulkDelete"]["count"] == 2
    assert not ProductImage.objects.filter(
        id__in=[image.id for image in images]
    ).exists()


def test_delete_product_types(
    staff_api_client, product_type_list, permission_manage_products
):
    query = """
    mutation productTypeBulkDelete($ids: [ID]!) {
        productTypeBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductType", type.id)
            for type in product_type_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productTypeBulkDelete"]["count"] == 3
    assert not ProductType.objects.filter(
        id__in=[type.id for type in product_type_list]
    ).exists()


def test_delete_product_variants(
    staff_api_client, product_variant_list, permission_manage_products
):
    query = """
    mutation productVariantBulkDelete($ids: [ID]!) {
        productVariantBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in product_variant_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    assert content["data"]["productVariantBulkDelete"]["count"] == 3
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in product_variant_list]
    ).exists()
