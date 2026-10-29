import graphene
import pytest

from .....tests.utils import get_graphql_content

PRODUCT_UNASSIGN_ATTR_MUTATION = """
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

PRODUCTS_WHERE_QUERY_WITH_ATTRIBUTES = """
    query($where: ProductWhereInput!, $channel: String) {
      products(first: 10, where: $where, channel: $channel) {
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
def test_product_not_filterable_by_attribute_after_unassign(
    filter_by_value,
    staff_api_client,
    product_list,
    product_type,
    color_attribute,
    channel_USD,
    permission_manage_product_types_and_attributes,
):
    # given
    # a product type has attribute assigned and every product in product_list
    # has attribute value assigned by the fixture
    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )
    assert product_type.product_attributes.first() == color_attribute
    attr_value = color_attribute.values.first()

    attribute_filter = {"slug": color_attribute.slug}
    if filter_by_value:
        attribute_filter["value"] = {"slug": {"eq": attr_value.slug}}
    where_variables = {
        "where": {"attributes": [attribute_filter]},
        "channel": channel_USD.slug,
    }

    response = staff_api_client.post_graphql(
        PRODUCTS_WHERE_QUERY_WITH_ATTRIBUTES, where_variables
    )
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == len(product_list)

    # unassign attribute from the product type
    unassign_variables = {
        "productTypeId": graphene.Node.to_global_id("ProductType", product_type.pk),
        "attributeIds": [graphene.Node.to_global_id("Attribute", color_attribute.pk)],
    }
    response = staff_api_client.post_graphql(
        PRODUCT_UNASSIGN_ATTR_MUTATION, unassign_variables
    )
    content = get_graphql_content(response)
    assert content["data"]["productAttributeUnassign"]["errors"] == []

    # when
    response = staff_api_client.post_graphql(
        PRODUCTS_WHERE_QUERY_WITH_ATTRIBUTES, where_variables
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert products_nodes == []
