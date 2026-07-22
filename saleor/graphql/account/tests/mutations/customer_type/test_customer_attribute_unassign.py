import graphene

from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_ATTRIBUTE_UNASSIGN_MUTATION = """
    mutation CustomerAttributeUnassign(
        $customerTypeId: ID!, $attributeIds: [ID!]!
    ) {
        customerAttributeUnassign(
            customerTypeId: $customerTypeId, attributeIds: $attributeIds
        ) {
            customerType {
                id
                attributes {
                    slug
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_unassign_by_staff(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
    segment_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    customer_type.customer_attributes.add(
        loyalty_customer_attribute, segment_customer_attribute
    )
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_ATTRIBUTE_UNASSIGN_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerAttributeUnassign"]
    assert data["errors"] == []
    assert [attr["slug"] for attr in data["customerType"]["attributes"]] == [
        segment_customer_attribute.slug
    ]
    assert customer_type.customer_attributes.get() == segment_customer_attribute


def test_unassign_by_app(
    app_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    app_api_client.app.permissions.add(permission_manage_customer_types_and_attributes)
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
        ],
    }

    # when
    response = app_api_client.post_graphql(
        CUSTOMER_ATTRIBUTE_UNASSIGN_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerAttributeUnassign"]
    assert data["errors"] == []
    assert customer_type.customer_attributes.count() == 0


def test_unassign_by_staff_no_permission(
    staff_api_client, customer_type, loyalty_customer_attribute
):
    # given
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_ATTRIBUTE_UNASSIGN_MUTATION, variables
    )

    # then
    assert_no_permission(response)
    assert customer_type.customer_attributes.get() == loyalty_customer_attribute


def test_unassign_keeps_attribute_values(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    values_count = loyalty_customer_attribute.values.count()
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_ATTRIBUTE_UNASSIGN_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerAttributeUnassign"]
    assert data["errors"] == []
    loyalty_customer_attribute.refresh_from_db()
    assert loyalty_customer_attribute.values.count() == values_count
