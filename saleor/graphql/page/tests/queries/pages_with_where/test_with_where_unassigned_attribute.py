import graphene
import pytest

from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content

PAGE_UNASSIGN_ATTR_MUTATION = """
    mutation PageAttributeUnassign($pageTypeId: ID!, $attributeIds: [ID!]!) {
        pageAttributeUnassign(
            pageTypeId: $pageTypeId, attributeIds: $attributeIds
        ) {
            errors {
                field
                code
                message
            }
        }
    }
"""

QUERY_PAGES_WITH_WHERE_AND_ATTRIBUTES = """
    query ($where: PageWhereInput) {
        pages(first: 5, where: $where) {
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
def test_page_not_filterable_by_attribute_after_unassign(
    filter_by_value,
    staff_api_client,
    page_list,
    page_type,
    size_page_attribute,
    permission_manage_page_types_and_attributes,
):
    # given
    # a page type has attribute assiged and page has attribute value assigned
    staff_api_client.user.user_permissions.add(
        permission_manage_page_types_and_attributes
    )
    page_type.page_attributes.add(size_page_attribute)
    page = page_list[0]
    attr_value = size_page_attribute.values.first()
    associate_attribute_values_to_instance(page, {size_page_attribute.pk: [attr_value]})

    attribute_filter = {"slug": size_page_attribute.slug}
    if filter_by_value:
        attribute_filter["value"] = {"slug": {"eq": attr_value.slug}}
    where_variables = {"where": {"attributes": [attribute_filter]}}

    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE_AND_ATTRIBUTES, where_variables
    )
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == 1

    # unassign attribute from the page type
    unassign_variables = {
        "pageTypeId": graphene.Node.to_global_id("PageType", page_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", size_page_attribute.pk)
        ],
    }
    response = staff_api_client.post_graphql(
        PAGE_UNASSIGN_ATTR_MUTATION, unassign_variables
    )
    content = get_graphql_content(response)
    assert content["data"]["pageAttributeUnassign"]["errors"] == []

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE_AND_ATTRIBUTES, where_variables
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert pages_nodes == []
