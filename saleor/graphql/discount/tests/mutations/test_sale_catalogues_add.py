from unittest.mock import patch

import graphene

from .....discount.error_codes import DiscountErrorCode
from .....discount.utils import fetch_catalogue_info
from ....tests.utils import get_graphql_content
from ...mutations.utils import convert_catalogue_info_to_global_ids

SALE_CATALOGUES_ADD_MUTATION = """
    mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
        saleCataloguesAdd(id: $id, input: $input) {
            sale {
                name
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.sale_updated")
def test_sale_add_catalogues(
    updated_webhook_mock,
    staff_api_client,
    sale,
    category,
    product,
    collection,
    variant,
    product_variant_list,
    permission_manage_discounts,
):
    query = SALE_CATALOGUES_ADD_MUTATION
    previous_catalogue = convert_catalogue_info_to_global_ids(
        fetch_catalogue_info(sale)
    )
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["errors"]
    assert product in sale.products.all()
    assert category in sale.categories.all()
    assert collection in sale.collections.all()
    assert set(product_variant_list + [variant]) == set(sale.variants.all())

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue=previous_catalogue, current_catalogue=current_catalogue
    )


def test_sale_add_no_catalogues(
    staff_api_client, new_sale, permission_manage_discounts
):
    # given
    query = SALE_CATALOGUES_ADD_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Sale", new_sale.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["errors"]
    assert not new_sale.products.exists()
    assert not new_sale.categories.exists()
    assert not new_sale.collections.exists()
    assert not new_sale.variants.exists()


def test_sale_remove_no_catalogues(
    staff_api_client,
    sale,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    # given
    sale.products.add(product)
    sale.collections.add(collection)
    sale.categories.add(category)
    sale.variants.add(*product_variant_list)

    query = SALE_CATALOGUES_ADD_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["errors"]
    assert sale.products.exists()
    assert sale.categories.exists()
    assert sale.collections.exists()
    assert sale.variants.exists()


def test_sale_add_catalogues_with_product_without_variants(
    staff_api_client, sale, category, product, collection, permission_manage_discounts
):
    query = SALE_CATALOGUES_ADD_MUTATION
    product.variants.all().delete()
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)

    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    error = content["data"]["saleCataloguesAdd"]["errors"][0]

    assert error["code"] == DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.name
    assert error["message"] == "Cannot manage products without variants."
