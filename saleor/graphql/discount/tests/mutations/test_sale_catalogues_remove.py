from unittest.mock import patch

import graphene

from .....discount.utils import fetch_catalogue_info
from ....tests.utils import get_graphql_content
from ...mutations.utils import convert_catalogue_info_to_global_ids

SALE_CATALOGUES_REMOVE_MUTATION = """
    mutation saleCataloguesRemove($id: ID!, $input: CatalogueInput!) {
        saleCataloguesRemove(id: $id, input: $input) {
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
def test_sale_remove_catalogues(
    updated_webhook_mock,
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

    query = SALE_CATALOGUES_REMOVE_MUTATION
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

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    current_catalogue = convert_catalogue_info_to_global_ids(fetch_catalogue_info(sale))

    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesRemove"]
    product_variants = list(sale.variants.all())

    assert not data["errors"]
    assert product not in sale.products.all()
    assert category not in sale.categories.all()
    assert collection not in sale.collections.all()
    assert not any(v in product_variants for v in product_variant_list)

    updated_webhook_mock.assert_called_once_with(
        sale, previous_catalogue=previous_catalogue, current_catalogue=current_catalogue
    )
