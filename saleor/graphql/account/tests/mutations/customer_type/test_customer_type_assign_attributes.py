import graphene

from ......account.error_codes import CustomerTypeAssignAttributesErrorCode
from ......attribute.models import AttributeCustomerType
from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION = """
    mutation CustomerTypeAssignAttributes(
        $customerTypeId: ID!, $attributeIds: [ID!]!
    ) {
        customerTypeAssignAttributes(
            customerTypeId: $customerTypeId, attributeIds: $attributeIds
        ) {
            customerType {
                id
                attributes {
                    id
                    slug
                }
            }
            errors {
                field
                code
                message
                attributes
            }
        }
    }
"""


def test_assign_by_staff(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    attribute_id = graphene.Node.to_global_id(
        "Attribute", loyalty_customer_attribute.pk
    )
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [attribute_id],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert data["errors"] == []
    assert [attr["slug"] for attr in data["customerType"]["attributes"]] == [
        loyalty_customer_attribute.slug
    ]
    assert customer_type.customer_attributes.get() == loyalty_customer_attribute


def test_assign_by_app(
    app_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    app_api_client.app.permissions.add(permission_manage_customer_types_and_attributes)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", loyalty_customer_attribute.pk
    )
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [attribute_id],
    }

    # when
    response = app_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert data["errors"] == []
    assert customer_type.customer_attributes.get() == loyalty_customer_attribute


def test_assign_by_staff_no_permission(
    staff_api_client, customer_type, loyalty_customer_attribute
):
    # given
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    assert_no_permission(response)
    assert customer_type.customer_attributes.count() == 0


def test_assign_not_customer_attribute(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    size_page_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    attribute_id = graphene.Node.to_global_id("Attribute", size_page_attribute.pk)
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [attribute_id],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributeIds"
    assert error["code"] == CustomerTypeAssignAttributesErrorCode.INVALID.name
    assert error["message"] == "Only customer attributes can be assigned."
    assert error["attributes"] == [attribute_id]
    assert customer_type.customer_attributes.count() == 0


def test_assign_attribute_already_assigned(
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
    attribute_id = graphene.Node.to_global_id(
        "Attribute", loyalty_customer_attribute.pk
    )
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [attribute_id],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributeIds"
    assert (
        error["code"]
        == CustomerTypeAssignAttributesErrorCode.ATTRIBUTE_ALREADY_ASSIGNED.name
    )
    assert error["attributes"] == [attribute_id]


def test_assign_invalid_object_type_as_customer_type_id(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "customerTypeId": graphene.Node.to_global_id("Order", customer_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "customerTypeId"
    assert error["code"] == CustomerTypeAssignAttributesErrorCode.GRAPHQL_ERROR.name


def test_assign_more_than_limit(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    attribute_ids = [
        graphene.Node.to_global_id("Attribute", index) for index in range(101)
    ]
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": attribute_ids,
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributeIds"
    assert error["code"] == CustomerTypeAssignAttributesErrorCode.INVALID.name
    assert (
        error["message"]
        == "Cannot assign more than 100 attributes in a single mutation."
    )


def test_assign_sets_sort_order(
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
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [
            graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk),
            graphene.Node.to_global_id("Attribute", segment_customer_attribute.pk),
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert data["errors"] == []
    assignments = AttributeCustomerType.objects.filter(customer_type=customer_type)
    assert assignments.count() == 2
    assert {assignment.attribute_id for assignment in assignments} == {
        loyalty_customer_attribute.pk,
        segment_customer_attribute.pk,
    }


def test_assign_nonexistent_attribute(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    attribute_id = graphene.Node.to_global_id("Attribute", -1)
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [attribute_id],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributeIds"
    assert error["code"] == CustomerTypeAssignAttributesErrorCode.NOT_FOUND.name
    assert error["message"] == "Some of the attributes do not exist."
    assert error["attributes"] == [attribute_id]
    assert customer_type.customer_attributes.count() == 0


def test_assign_nonexistent_attribute_does_not_assign_valid_ones(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    valid_attribute_id = graphene.Node.to_global_id(
        "Attribute", loyalty_customer_attribute.pk
    )
    missing_attribute_id = graphene.Node.to_global_id("Attribute", -1)
    variables = {
        "customerTypeId": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributeIds": [valid_attribute_id, missing_attribute_id],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_TYPE_ASSIGN_ATTRIBUTES_MUTATION, variables
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeAssignAttributes"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributeIds"
    assert error["code"] == CustomerTypeAssignAttributesErrorCode.NOT_FOUND.name
    assert error["message"] == "Some of the attributes do not exist."
    assert error["attributes"] == [missing_attribute_id]
    assert customer_type.customer_attributes.count() == 0
