import graphene
import pytest

from ....tests.utils import get_graphql_content

PRODUCT_ATTRIBUTE_UNASSIGN_MUTATION = """
    mutation ProductAttributeUnassign($productTypeId: ID!, $attributeIds: [ID!]!) {
        productAttributeUnassign(
            productTypeId: $productTypeId, attributeIds: $attributeIds
        ) {
            errors {
                field
                code
                message
            }
        }
    }
"""

VARIANTS_WHERE_QUERY_WITH_ATTRIBUTES = """
    query($where: ProductVariantWhereInput!, $channel: String) {
      productVariants(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            id
            attributes {
              attribute {
                slug
              }
            }
          }
        }
      }
    }
"""


@pytest.mark.parametrize("filter_by_value", [True, False])
def test_variant_not_filterable_by_attribute_after_unassign(
    filter_by_value,
    staff_api_client,
    product,
    product_type,
    size_attribute,
    channel_USD,
    permission_manage_product_types_and_attributes,
):
    # given
    # a product type has variant attribute assigned and the product's variant
    # has attribute value assigned by the fixture
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    assert product_type.variant_attributes.first() == size_attribute
    variant = product.variants.first()
    attr_value = size_attribute.values.first()

    attribute_filter = {"slug": size_attribute.slug}
    if filter_by_value:
        attribute_filter["value"] = {"slug": {"eq": attr_value.slug}}
    where_variables = {
        "where": {"attributes": [attribute_filter]},
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        VARIANTS_WHERE_QUERY_WITH_ATTRIBUTES, where_variables
    )
    content = get_graphql_content(response)
    variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(variants_nodes) == 1

    # unassign attribute from the product type
    unassign_variables = {
        "productTypeId": graphene.Node.to_global_id("ProductType", product_type.pk),
        "attributeIds": [graphene.Node.to_global_id("Attribute", size_attribute.pk)],
    }
    response = staff_api_client.post_graphql(
        PRODUCT_ATTRIBUTE_UNASSIGN_MUTATION, unassign_variables
    )
    content = get_graphql_content(response)
    assert content["data"]["productAttributeUnassign"]["errors"] == []

    # when
    response = staff_api_client.post_graphql(
        VARIANTS_WHERE_QUERY_WITH_ATTRIBUTES, where_variables
    )

    # then
    content = get_graphql_content(response)
    variants_nodes = content["data"]["productVariants"]["edges"]
    assert variants_nodes == []
    # the assigned values were physically deleted by the unassign cascade,
    # unlike for pages and products where they are only hidden
    assert variant.attributevalues.count() == 0
