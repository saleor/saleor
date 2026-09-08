from unittest.mock import patch

import graphene

from ......account.error_codes import CustomerTypeUpdateErrorCode
from ......account.models import CustomerType
from .....tests.utils import assert_no_permission, get_graphql_content

CUSTOMER_TYPE_UPDATE_MUTATION = """
    mutation CustomerTypeUpdate($id: ID!, $input: CustomerTypeUpdateInput!) {
        customerTypeUpdate(id: $id, input: $input) {
            customerType {
                id
                name
                slug
                isDefault
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_update_name_and_slug(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    new_name = "Business"
    new_slug = "business"
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "input": {"name": new_name, "slug": new_slug},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeUpdate"]
    assert data["errors"] == []

    customer_type.refresh_from_db()
    assert customer_type.name == new_name
    assert customer_type.slug == new_slug
    assert data["customerType"]["name"] == customer_type.name
    assert data["customerType"]["slug"] == customer_type.slug


def test_update_name_keeps_slug(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    old_slug = customer_type.slug
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "input": {"name": "Renamed"},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeUpdate"]
    assert data["errors"] == []

    customer_type.refresh_from_db()
    assert customer_type.name == "Renamed"
    assert customer_type.slug == old_slug


def test_update_default_type_is_renamable(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    default_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    new_name = "Standard"
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", default_customer_type.pk),
        "input": {"name": new_name},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeUpdate"]
    assert data["errors"] == []

    default_customer_type.refresh_from_db()
    assert default_customer_type.name == new_name
    assert default_customer_type.is_default is True


def test_update_is_default_transfers_default_flag(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    default_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "input": {"isDefault": True},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeUpdate"]
    assert data["errors"] == []
    assert data["customerType"]["isDefault"] is True

    customer_type.refresh_from_db()
    default_customer_type.refresh_from_db()
    assert customer_type.is_default is True
    assert default_customer_type.is_default is False
    assert CustomerType.objects.filter(is_default=True).count() == 1


def test_update_is_default_true_on_current_default_is_noop(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    default_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", default_customer_type.pk),
        "input": {"isDefault": True},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeUpdate"]
    assert data["errors"] == []

    default_customer_type.refresh_from_db()
    assert default_customer_type.is_default is True
    assert CustomerType.objects.filter(is_default=True).count() == 1


def test_update_cannot_unset_default(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    default_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", default_customer_type.pk),
        "input": {"isDefault": False},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeUpdate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "isDefault"
    assert error["code"] == CustomerTypeUpdateErrorCode.CANNOT_UNSET_DEFAULT.name

    default_customer_type.refresh_from_db()
    assert default_customer_type.is_default is True


def test_update_is_default_false_on_non_default_is_noop(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    default_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "input": {"isDefault": False},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeUpdate"]
    assert data["errors"] == []

    customer_type.refresh_from_db()
    default_customer_type.refresh_from_db()
    assert customer_type.is_default is False
    assert default_customer_type.is_default is True


def test_update_with_duplicated_slug(
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
    default_customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "input": {"slug": default_customer_type.slug},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerTypeUpdate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "slug"
    assert error["code"] == CustomerTypeUpdateErrorCode.UNIQUE.name


def test_update_by_staff_without_permission(staff_api_client, customer_type):
    # given
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "input": {"name": "Renamed"},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.customer_type_updated")
def test_update_triggers_webhook(
    mocked_customer_type_updated,
    staff_api_client,
    permission_manage_customer_types_and_attributes,
    customer_type,
):
    # given
    staff_api_client.user.user_permissions.add(
        permission_manage_customer_types_and_attributes
    )
    variables = {
        "id": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "input": {"name": "Renamed"},
    }

    # when
    response = staff_api_client.post_graphql(CUSTOMER_TYPE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["customerTypeUpdate"]["errors"] == []

    customer_type.refresh_from_db()
    mocked_customer_type_updated.assert_called_once_with(customer_type)
