import graphene

from .....graphql.tests.utils import get_graphql_content
from .....product.error_codes import ProductErrorCode

PRODUCT_VARIANT_SET_DEFAULT_MUTATION = """
    mutation Prod($productId: ID!, $variantId: ID!) {
        productVariantSetDefault(productId: $productId, variantId: $variantId) {
            product {
                defaultVariant {
                    id
                }
            }
            errors {
                code
                field
            }
        }
    }
"""


def test_product_variant_set_default(
    staff_api_client, permission_manage_products, product_with_two_variants
):
    assert not product_with_two_variants.default_variant

    first_variant = product_with_two_variants.variants.first()
    first_variant_id = graphene.Node.to_global_id("ProductVariant", first_variant.pk)

    variables = {
        "productId": graphene.Node.to_global_id(
            "Product", product_with_two_variants.pk
        ),
        "variantId": first_variant_id,
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_SET_DEFAULT_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    product_with_two_variants.refresh_from_db()
    assert product_with_two_variants.default_variant == first_variant
    content = get_graphql_content(response)
    data = content["data"]["productVariantSetDefault"]
    assert not data["errors"]
    assert data["product"]["defaultVariant"]["id"] == first_variant_id


def test_product_variant_set_default_invalid_id(
    staff_api_client, permission_manage_products, product_with_two_variants
):
    assert not product_with_two_variants.default_variant

    first_variant = product_with_two_variants.variants.first()

    variables = {
        "productId": graphene.Node.to_global_id(
            "Product", product_with_two_variants.pk
        ),
        "variantId": graphene.Node.to_global_id("Product", first_variant.pk),
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_SET_DEFAULT_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    product_with_two_variants.refresh_from_db()
    assert not product_with_two_variants.default_variant
    content = get_graphql_content(response)
    data = content["data"]["productVariantSetDefault"]
    assert data["errors"][0]["code"] == ProductErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["field"] == "variantId"


def test_product_variant_set_default_not_products_variant(
    staff_api_client,
    permission_manage_products,
    product_with_two_variants,
    product_with_single_variant,
):
    assert not product_with_two_variants.default_variant

    foreign_variant = product_with_single_variant.variants.first()

    variables = {
        "productId": graphene.Node.to_global_id(
            "Product", product_with_two_variants.pk
        ),
        "variantId": graphene.Node.to_global_id("ProductVariant", foreign_variant.pk),
    }

    response = staff_api_client.post_graphql(
        PRODUCT_VARIANT_SET_DEFAULT_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    product_with_two_variants.refresh_from_db()
    assert not product_with_two_variants.default_variant
    content = get_graphql_content(response)
    data = content["data"]["productVariantSetDefault"]
    assert data["errors"][0]["code"] == ProductErrorCode.NOT_PRODUCTS_VARIANT.name
    assert data["errors"][0]["field"] == "variantId"
