import graphene

from .....discount import VoucherType
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


VOUCHER_REMOVE_CATALOGUES_WITH_CATALOGUE = """
    mutation voucherCataloguesRemove($id: ID!, $catalogue: VoucherCatalogueInput) {
        voucherCataloguesRemove(id: $id, catalogue: $catalogue) {
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_remove_catalogue_exclusions(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    product,
    variant,
    collection,
    category,
    product_type_list,
):
    # given
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["type"])
    voucher.product_types.add(product_type_list[0])
    voucher.excluded_products.add(product)
    voucher.excluded_variants.add(variant)
    voucher.excluded_collections.add(collection)
    voucher.excluded_categories.add(category)
    voucher.excluded_product_types.add(product_type_list[1], product_type_list[2])
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "catalogue": {
            "productTypes": [
                graphene.Node.to_global_id("ProductType", product_type_list[0].pk)
            ],
            "excludedProducts": [graphene.Node.to_global_id("Product", product.pk)],
            "excludedVariants": [
                graphene.Node.to_global_id("ProductVariant", variant.pk)
            ],
            "excludedCollections": [
                graphene.Node.to_global_id("Collection", collection.pk)
            ],
            "excludedCategories": [graphene.Node.to_global_id("Category", category.pk)],
            "excludedProductTypes": [
                graphene.Node.to_global_id("ProductType", product_type_list[1].pk)
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_REMOVE_CATALOGUES_WITH_CATALOGUE,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["voucherCataloguesRemove"]["errors"] == []
    assert voucher.product_types.exists() is False
    assert voucher.excluded_products.exists() is False
    assert voucher.excluded_variants.exists() is False
    assert voucher.excluded_collections.exists() is False
    assert voucher.excluded_categories.exists() is False
    assert list(voucher.excluded_product_types.all()) == [product_type_list[2]]
