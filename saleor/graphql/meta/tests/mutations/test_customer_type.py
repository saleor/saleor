import graphene

from ....tests.utils import assert_no_permission
from . import PRIVATE_KEY, PUBLIC_KEY
from .test_update_metadata import (
    UPDATE_PUBLIC_METADATA_MUTATION,
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    UPDATE_PRIVATE_METADATA_MUTATION,
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_add_public_metadata_for_customer_type_as_staff(
    staff_api_client, permission_manage_customer_types_and_attributes, customer_type
):
    # given
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_customer_types_and_attributes,
        customer_type_id,
        "CustomerType",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer_type, customer_type_id
    )


def test_add_public_metadata_for_customer_type_as_app(
    app_api_client, permission_manage_customer_types_and_attributes, customer_type
):
    # given
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)

    # when
    response = execute_update_public_metadata_for_item(
        app_api_client,
        permission_manage_customer_types_and_attributes,
        customer_type_id,
        "CustomerType",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], customer_type, customer_type_id
    )


def test_add_public_metadata_for_customer_type_without_permission(
    staff_api_client, customer_type
):
    # given
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)
    variables = {
        "id": customer_type_id,
        "input": [{"key": PUBLIC_KEY, "value": "value"}],
    }
    # when
    response = staff_api_client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % "CustomerType", variables
    )

    # then
    assert_no_permission(response)
    customer_type.refresh_from_db(fields=["metadata"])
    assert customer_type.metadata == {}


def test_add_private_metadata_for_customer_type_as_staff(
    staff_api_client, permission_manage_customer_types_and_attributes, customer_type
):
    # given
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_customer_types_and_attributes,
        customer_type_id,
        "CustomerType",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        customer_type,
        customer_type_id,
    )


def test_add_private_metadata_for_customer_type_as_app(
    app_api_client, permission_manage_customer_types_and_attributes, customer_type
):
    # given
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)

    # when
    response = execute_update_private_metadata_for_item(
        app_api_client,
        permission_manage_customer_types_and_attributes,
        customer_type_id,
        "CustomerType",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        customer_type,
        customer_type_id,
    )


def test_add_private_metadata_for_customer_type_without_permission(
    staff_api_client, customer_type
):
    # given
    customer_type_id = graphene.Node.to_global_id("CustomerType", customer_type.pk)
    variables = {
        "id": customer_type_id,
        "input": [{"key": PRIVATE_KEY, "value": "value"}],
    }
    # when
    response = staff_api_client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % "CustomerType", variables
    )

    # then
    assert_no_permission(response)
    customer_type.refresh_from_db(fields=["private_metadata"])
    assert customer_type.private_metadata == {}
