from unittest.mock import patch

import graphene

from ......account.error_codes import CustomerTypeDeleteErrorCode
from ......account.models import CustomerType
from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TYPE_DELETE_MUTATION = """
    mutation CustomerTypeDelete($id: ID!) {
        customerTypeDelete(id: $id) {
            customerType {
                id
                name
                slug
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_delete_by_staff_with_permission(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeDelete"]
    assert data["errors"] == []
    assert data["customerType"]["slug"] == customer_type.slug
    assert not CustomerType.objects.filter(pk=customer_type.pk).exists()


def test_delete_reassigns_users_to_default(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    default_customer_type,
    customer_user,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    customer_user.customer_type = customer_type
    customer_user.save(update_fields=["customer_type"])
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeDelete"]
    assert data["errors"] == []
    assert not CustomerType.objects.filter(pk=customer_type.pk).exists()

    customer_user.refresh_from_db()
    assert customer_user.customer_type == default_customer_type


def test_delete_default_type_is_forbidden(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    default_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", default_customer_type.pk)
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeDelete"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "id"
    assert error["code"] == CustomerTypeDeleteErrorCode.CANNOT_DELETE_DEFAULT.name
    assert CustomerType.objects.filter(pk=default_customer_type.pk).exists()


def test_delete_by_staff_without_permission(staff_api_client, customer_type):
    # given
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_DELETE_MUTATION, variables)

    # then
    assert_no_permission(response)
    assert CustomerType.objects.filter(pk=customer_type.pk).exists()


@patch("saleor.plugins.manager.PluginsManager.customer_type_deleted")
def test_delete_triggers_webhook(
    mocked_customer_type_deleted,
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {"id": graphene.Node.to_global_id("CustomerType", customer_type.pk)}

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_DELETE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["customerTypeDelete"]["errors"] == []
    mocked_customer_type_deleted.assert_called_once_with(customer_type)
