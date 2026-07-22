import graphene

from ......account.error_codes import CustomerTypeReorderAttributesErrorCode
from ......attribute.models import AttributeCustomerType
from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TYPE_REORDER_ATTRIBUTES_MUTATION = """
    mutation CustomerTypeReorderAttributes(
        $customerTypeId: ID!, $moves: [ReorderInput!]!
    ) {
        customerTypeReorderAttributes(
            customerTypeId: $customerTypeId, moves: $moves
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


def test_reorder_by_staff(
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
    assigned_slugs = [
        assignment.attribute.slug
        for assignment in AttributeCustomerType.objects.filter(
            customer_type=customer_type
        )
    ]
    assert assigned_slugs == [
        loyalty_customer_attribute.slug,
        segment_customer_attribute.slug,
    ]
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "moves": [
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", loyalty_customer_attribute.pk
                ),
                "sortOrder": 1,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_REORDER_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeReorderAttributes"]
    assert data["errors"] == []
    assert [attr["slug"] for attr in data["customerType"]["attributes"]] == [
        segment_customer_attribute.slug,
        loyalty_customer_attribute.slug,
    ]


def test_reorder_by_staff_no_permission(
    staff_api_client,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "moves": [
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", loyalty_customer_attribute.pk
                ),
                "sortOrder": 1,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_REORDER_ATTRIBUTES_MUTATION, variables
    )

    # then
    assert_no_permission(response)


def test_reorder_invalid_customer_type(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    customer_type_id = graphene.Node.to_global_id("CustomerType", -1)
    variables = {
        "customerTypeId": customer_type_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", loyalty_customer_attribute.pk
                ),
                "sortOrder": 1,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_REORDER_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeReorderAttributes"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "customerTypeId"
    assert error["code"] == CustomerTypeReorderAttributesErrorCode.NOT_FOUND.name
    assert (
        error["message"] == f"Couldn't resolve to a customer type: {customer_type_id}"
    )


def test_reorder_invalid_attribute_id(
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
    customer_type.customer_attributes.add(loyalty_customer_attribute)
    # segment_customer_attribute is not assigned to the customer type
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "moves": [
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", segment_customer_attribute.pk
                ),
                "sortOrder": 1,
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_REORDER_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeReorderAttributes"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "moves"
    assert error["code"] == CustomerTypeReorderAttributesErrorCode.NOT_FOUND.name
    assert error["message"] == "Couldn't resolve to an attribute."
