import graphene

from ....tests.utils import get_graphql_content

VOUCHER_REMOVE_CATALOGUES = """
    mutation voucherCataloguesRemove($id: ID!, $input: CatalogueInput!) {
        voucherCataloguesRemove(id: $id, input: $input) {
            voucher {
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


def test_voucher_remove_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)
    voucher.variants.add(*product_variant_list)

    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        VOUCHER_REMOVE_CATALOGUES, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesRemove"]
    voucher_variants = list(voucher.variants.all())

    assert not data["errors"]
    assert product not in voucher.products.all()
    assert category not in voucher.categories.all()
    assert collection not in voucher.collections.all()
    assert not any(v in voucher_variants for v in product_variant_list)
