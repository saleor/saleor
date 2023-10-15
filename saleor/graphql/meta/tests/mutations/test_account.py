import graphene
import pytest

from .....account.error_codes import AccountErrorCode
from .....account.models import User
from .....core.error_codes import MetadataErrorCode
from ....tests.utils import assert_no_permission
from . import (
    PRIVATE_KEY,
    PRIVATE_VALUE,
    PUBLIC_KEY,
    PUBLIC_KEY2,
    PUBLIC_VALUE,
    PUBLIC_VALUE2,
)
from .test_delete_metadata import (
    DELETE_PUBLIC_METADATA_MUTATION,
    execute_clear_public_metadata_for_item,
    execute_clear_public_metadata_for_multiple_items,
    item_without_multiple_public_metadata,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    DELETE_PRIVATE_METADATA_MUTATION,
    execute_clear_private_metadata_for_item,
    execute_clear_private_metadata_for_multiple_items,
    item_without_multiple_private_metadata,
    item_without_private_metadata,
)
from .test_update_metadata import (
    UPDATE_PUBLIC_METADATA_MUTATION,
    execute_update_public_metadata_for_item,
    execute_update_public_metadata_for_multiple_items,
    item_contains_multiple_proper_public_metadata,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    UPDATE_PRIVATE_METADATA_MUTATION,
    execute_update_private_metadata_for_item,
    execute_update_private_metadata_for_multiple_items,
    item_contains_multiple_proper_private_metadata,
    item_contains_proper_private_metadata,
)


def test_delete_public_metadata_for_customer_address_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    address = customer_user.addresses.first()
    address.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    address.save(update_fields=["metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_users, address_id, "Address"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], address, address_id
    )


def test_delete_public_metadata_for_customer_address_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    address = customer_user.addresses.first()
    address.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    address.save(update_fields=["metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        app_api_client, permission_manage_users, address_id, "Address"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], address, address_id
    )


def test_delete_public_metadata_for_staff_address_as_another_staff(
    staff_api_client, staff_users, address, permission_manage_staff
):
    # given
    staff_user = staff_users[-1]
    staff_user.addresses.add(address)
    address.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    address.save(update_fields=["metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_staff, address_id, "Address"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], address, address_id
    )


def test_delete_public_metadata_for_staff_address_as_staff(staff_api_client, address):
    # given
    staff_user = staff_api_client.user
    staff_user.addresses.add(address)
    address.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    address.save(update_fields=["metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, None, address_id, "Address"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], address, address_id
    )


def test_delete_public_metadata_for_staff_address_as_app(
    app_api_client, staff_user, address, permission_manage_staff
):
    # given
    staff_user.addresses.add(address)
    address.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    address.save(update_fields=["metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Address", address.pk),
        "keys": [PUBLIC_KEY],
    }

    # when
    response = app_api_client.post_graphql(
        DELETE_PUBLIC_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_delete_public_metadata_for_myself_address(staff_api_client, address):
    # given
    staff = staff_api_client.user
    staff.addresses.add(address)
    address.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    staff.save(update_fields=["metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, None, address_id, "Address"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], address, address_id
    )


def test_delete_private_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_delete_private_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer_user.save(update_fields=["private_metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_delete_multiple_private_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata(
        {PUBLIC_KEY: PUBLIC_VALUE, PUBLIC_KEY2: PUBLIC_VALUE2}
    )
    customer_user.save(update_fields=["metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_private_metadata_for_multiple_items(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_multiple_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_delete_private_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_metadata"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], admin_user, admin_id
    )


def test_delete_private_metadata_for_staff_as_app_no_permission(
    app_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    admin_user.save(update_fields=["private_metadata"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)
    variables = {
        "id": admin_id,
        "keys": [PRIVATE_KEY],
    }

    # when
    response = app_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_myself_as_customer_no_permission(user_api_client):
    # given
    customer = user_api_client.user
    customer.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    customer.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("User", customer.pk),
        "keys": [PRIVATE_KEY],
    }

    # when
    response = user_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "User", variables, permissions=[]
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_myself_as_staff_no_permission(
    staff_api_client, permission_manage_users
):
    # given
    staff = staff_api_client.user
    staff.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    staff.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("User", staff.pk),
        "keys": [PRIVATE_KEY],
    }

    # when
    response = staff_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_users],
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_customer_address_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    address = customer_user.addresses.first()
    address.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    address.save(update_fields=["private_metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_users, address_id, "Address"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], address, address_id
    )


def test_delete_private_metadata_for_customer_address_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    address = customer_user.addresses.first()
    address.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    address.save(update_fields=["private_metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        app_api_client, permission_manage_users, address_id, "Address"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], address, address_id
    )


def test_delete_private_metadata_for_staff_address_as_staff(
    staff_api_client, address, permission_manage_staff
):
    # given
    staff_user = staff_api_client.user
    staff_user.addresses.add(address)
    address.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    address.save(update_fields=["private_metadata"])
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_staff, address_id, "Address"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], address, address_id
    )


def test_delete_private_metadata_for_staff_address_as_app(
    app_api_client, staff_user, address, permission_manage_staff
):
    # given
    staff_user.addresses.add(address)
    address.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    address.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Address", address.pk),
        "keys": [PRIVATE_KEY],
    }

    # when
    response = app_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_delete_private_metadata_for_myself_address_as_staff_no_permission(
    staff_api_client, address, permission_manage_users
):
    # given
    staff = staff_api_client.user
    staff.addresses.add(address)
    staff.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    staff.save(update_fields=["private_metadata"])
    variables = {
        "id": graphene.Node.to_global_id("Address", address.pk),
        "keys": [PRIVATE_KEY],
    }

    # when
    response = staff_api_client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_users],
    )

    # then
    assert_no_permission(response)


def test_delete_public_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], customer_user, customer_id
    )


def test_delete_public_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer_user.save(update_fields=["metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], customer_user, customer_id
    )


def test_delete_multiple_public_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_user.store_value_in_metadata(
        {PUBLIC_KEY: PUBLIC_VALUE, PUBLIC_KEY2: PUBLIC_VALUE2}
    )
    customer_user.save(update_fields=["metadata"])
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_clear_public_metadata_for_multiple_items(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_without_multiple_public_metadata(
        response["data"]["deleteMetadata"]["item"], customer_user, customer_id
    )


def test_delete_public_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    admin_user.save(update_fields=["metadata"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], admin_user, admin_id
    )


def test_delete_public_metadata_for_staff_as_app_no_permission(
    app_api_client, permission_manage_staff, admin_user
):
    # given
    admin_user.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    admin_user.save(update_fields=["metadata"])
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)
    variables = {
        "id": admin_id,
        "keys": [PRIVATE_KEY],
    }

    # when
    response = app_api_client.post_graphql(
        DELETE_PUBLIC_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_delete_public_metadata_for_myself_as_customer(user_api_client):
    # given
    customer = user_api_client.user
    customer.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    customer.save(update_fields=["metadata"])
    customer_id = graphene.Node.to_global_id("User", customer.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        user_api_client, None, customer_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], customer, customer_id
    )


def test_delete_public_metadata_for_myself_as_staff(staff_api_client):
    # given
    staff = staff_api_client.user
    staff.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    staff.save(update_fields=["metadata"])
    staff_id = graphene.Node.to_global_id("User", staff.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, None, staff_id, "User"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], staff, staff_id
    )


def test_update_public_metadata_for_customer_address_by_logged_user(
    user_api_client, address
):
    # given
    user = user_api_client.user
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_public_metadata_for_item(
        user_api_client, None, address_id, "Address", value="NewMetaValue"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_public_metadata_for_customer_address_by_different_logged_user(
    user2_api_client, customer_user
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user2_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_public_metadata_for_customer_address_by_staff_with_perm(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_users,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_public_metadata_for_customer_address_by_app_with_perm(
    app_api_client, customer_user, permission_manage_users
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_public_metadata_for_item(
        app_api_client,
        permission_manage_users,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_public_metadata_for_address_by_non_logged_user(
    api_client, customer_user
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "id": address_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_public_metadata_for_staff_address_by_staff_with_perm(
    staff_api_client, address, staff_users, permission_manage_staff
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_staff,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_public_metadata_for_staff_address_by_staff_without_perm(
    staff_api_client, address, staff_users
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_public_metadata_for_staff_address_by_customer(
    user_api_client, address, staff_users
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_public_metadata_for_staff_address_by_app_with_perm(
    app_api_client, staff_user, address, permission_manage_staff
):
    # given
    staff_user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_update_public_metadata_for_staff_address_by_app_without_perm(
    app_api_client, staff_user, address
):
    # given
    staff_user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Address", variables
    )

    # then
    assert_no_permission(response)


def test_update_public_metadata_for_warehouse_address_by_staff(
    staff_api_client, warehouse, permission_manage_staff
):
    # given
    address = warehouse.address
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_update_public_metadata_for_site_settings_address_by_staff(
    staff_api_client, site_settings, address, permission_manage_staff
):
    # given
    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PUBLIC_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_add_public_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer_user, customer_id
    )


def test_add_public_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_public_metadata_for_item(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer_user, customer_id
    )


def test_change_metadata_for_non_existing_user(app_api_client, customer_user):
    # given the non-existing user ID
    last_id = User.objects.order_by("id").values_list("id", flat=True).last()
    customer_id = graphene.Node.to_global_id("User", last_id + 100)

    # when
    response = execute_update_public_metadata_for_item(
        app_api_client, [], customer_id, "User"
    )

    # then
    assert (
        response["data"]["updateMetadata"]["errors"][0]["code"]
        == AccountErrorCode.NOT_FOUND.name
    )


def test_add_multiple_public_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_public_metadata_for_multiple_items(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_multiple_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer_user, customer_id
    )


def test_add_public_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], admin_user, admin_id
    )


@pytest.mark.parametrize(
    "input",
    [{"key": " ", "value": "test"}, {"key": "   ", "value": ""}],
)
def test_staff_update_metadata_empty_key(
    input, staff_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_staff,
        admin_id,
        "User",
        input["key"],
        input["value"],
    )

    # then
    data = response["data"]["updateMetadata"]
    errors = data["errors"]

    assert not data["item"]
    assert len(errors) == 1
    assert errors[0]["code"] == MetadataErrorCode.REQUIRED.name
    assert errors[0]["field"] == "input"


def test_add_public_metadata_for_myself_as_customer(user_api_client):
    # given
    customer = user_api_client.user
    customer_id = graphene.Node.to_global_id("User", customer.pk)

    # when
    response = execute_update_public_metadata_for_item(
        user_api_client, None, customer_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer, customer_id
    )


def test_add_public_metadata_for_myself_as_staff(staff_api_client):
    # given
    staff = staff_api_client.user
    staff_id = graphene.Node.to_global_id("User", staff.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, None, staff_id, "User"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], staff, staff_id
    )


def test_add_private_metadata_for_customer_as_staff(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_add_private_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_add_multiple_private_metadata_for_customer_as_app(
    app_api_client, permission_manage_users, customer_user
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    # when
    response = execute_update_private_metadata_for_multiple_items(
        app_api_client, permission_manage_users, customer_id, "User"
    )

    # then
    assert item_contains_multiple_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], customer_user, customer_id
    )


def test_add_private_metadata_for_other_staff_as_staff(
    staff_api_client, permission_manage_staff, admin_user
):
    # given
    assert admin_user.pk != staff_api_client.user.pk
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_staff, admin_id, "User"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], admin_user, admin_id
    )


def test_add_public_metadata_for_staff_as_app_no_permission(
    app_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)
    variables = {
        "id": admin_id,
        "input": [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}],
    }

    # when

    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_staff_as_app_no_permission(
    app_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)
    variables = {
        "id": admin_id,
        "input": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_add_private_metadata_for_myself_as_customer_no_permission(user_api_client):
    # given
    customer = user_api_client.user
    variables = {
        "id": graphene.Node.to_global_id("User", customer.pk),
        "input": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}],
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[],
    )

    # then
    assert_no_permission(response)


@pytest.mark.parametrize(
    "input",
    [{"key": " ", "value": "test"}, {"key": "   ", "value": ""}],
)
def test_staff_update_private_metadata_empty_key(
    input, staff_api_client, permission_manage_staff, admin_user
):
    # given
    admin_id = graphene.Node.to_global_id("User", admin_user.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_staff,
        admin_id,
        "User",
        input["key"],
        input["value"],
    )

    # then
    data = response["data"]["updatePrivateMetadata"]
    errors = data["errors"]

    assert not data["item"]
    assert len(errors) == 1
    assert errors[0]["code"] == MetadataErrorCode.REQUIRED.name
    assert errors[0]["field"] == "input"


def test_add_private_metadata_for_myself_as_staff(staff_api_client):
    # given
    staff = staff_api_client.user
    variables = {
        "id": graphene.Node.to_global_id("User", staff.pk),
        "input": [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "User",
        variables,
        permissions=[],
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_customer_address_by_logged_user(
    user_api_client, address
):
    # given
    user = user_api_client.user
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_customer_address_by_different_logged_user(
    user2_api_client, customer_user
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user2_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_customer_address_by_staff_with_perm(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_users,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_customer_address_by_app_with_perm(
    app_api_client, customer_user, permission_manage_users
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client,
        permission_manage_users,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_address_by_non_logged_user(
    api_client, customer_user
):
    # given
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.pk)
    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_staff_address_by_staff_with_perm(
    staff_api_client, address, staff_users, permission_manage_staff
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_staff,
        address_id,
        "Address",
        value="NewMetaValue",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        address,
        address_id,
        value="NewMetaValue",
    )


def test_update_private_metadata_for_staff_address_by_staff_without_perm(
    staff_api_client, address, staff_users
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_staff_address_by_customer(
    user_api_client, address, staff_users
):
    # given
    user = staff_users[-1]
    user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = user_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables, permissions=None
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_staff_address_by_app_with_perm(
    app_api_client, staff_user, address, permission_manage_staff
):
    # given
    staff_user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_staff_address_by_app_without_perm(
    app_api_client, staff_user, address
):
    # given
    staff_user.addresses.add(address)
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = app_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address", variables
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_warehouse_address_by_staff(
    staff_api_client, warehouse, permission_manage_staff
):
    # given
    address = warehouse.address
    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)


def test_update_private_metadata_for_site_settings_address_by_staff(
    staff_api_client, site_settings, address, permission_manage_staff
):
    # given
    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])

    address_id = graphene.Node.to_global_id("Address", address.pk)

    variables = {
        "id": address_id,
        "input": [{"key": PRIVATE_KEY, "value": "NewMetaValue"}],
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "Address",
        variables,
        permissions=[permission_manage_staff],
    )

    # then
    assert_no_permission(response)
