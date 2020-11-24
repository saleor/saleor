import graphene
import pytest

from ....tests.utils import get_graphql_content


def test_delete_attribute(
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    product_type,
):
    # given
    attribute = color_attribute
    query = """
    mutation deleteAttribute($id: ID!) {
        attributeDelete(id: $id) {
            errors {
                field
                message
            }
            attribute {
                id
            }
        }
    }
    """
    node_id = graphene.Node.to_global_id("Attribute", attribute.id)
    variables = {"id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["attributeDelete"]
    assert data["attribute"]["id"] == variables["id"]
    with pytest.raises(attribute._meta.model.DoesNotExist):
        attribute.refresh_from_db()
