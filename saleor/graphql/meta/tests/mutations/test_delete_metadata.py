import base64

import graphene

from .....core.error_codes import MetadataErrorCode
from .....core.models import ModelWithMetadata
from .....tests import race_condition
from ....tests.utils import get_graphql_content
from . import PUBLIC_KEY, PUBLIC_KEY2, PUBLIC_VALUE, PUBLIC_VALUE2
from .test_update_metadata import item_contains_proper_public_metadata

DELETE_PUBLIC_METADATA_MUTATION = """
mutation DeletePublicMetadata($id: ID!, $keys: [String!]!) {
    deleteMetadata(
        id: $id
        keys: $keys
    ) {
        errors{
            field
            code
        }
        item {
            metadata{
                key
                value
            }
            ...on %s{
                id
            }
        }
    }
}
"""


def execute_clear_public_metadata_for_item(
    client,
    permissions,
    item_id,
    item_type,
    key=PUBLIC_KEY,
):
    variables = {
        "id": item_id,
        "keys": [key],
    }
    response = client.post_graphql(
        DELETE_PUBLIC_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def execute_clear_public_metadata_for_multiple_items(
    client, permissions, item_id, item_type, key=PUBLIC_KEY, key2=PUBLIC_KEY2
):
    variables = {
        "id": item_id,
        "keys": [key, key2],
    }

    response = client.post_graphql(
        DELETE_PUBLIC_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def item_without_public_metadata(
    item_from_response,
    item,
    item_id,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_value_from_metadata(key) != value


def item_without_multiple_public_metadata(
    item_from_response,
    item,
    item_id,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
    key2=PUBLIC_KEY2,
    value2=PUBLIC_VALUE2,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return all(
        [
            item.get_value_from_metadata(key) != value,
            item.get_value_from_metadata(key2) != value2,
        ]
    )


def test_delete_public_metadata_for_non_exist_item(
    staff_api_client, permission_manage_payments
):
    # given
    payment_id = "Payment: 0"
    payment_id = base64.b64encode(str.encode(payment_id)).decode("utf-8")

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_payments, payment_id, "Checkout"
    )

    # then
    errors = response["data"]["deleteMetadata"]["errors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


def test_delete_public_metadata_for_item_without_meta(
    api_client, permission_group_manage_users
):
    # given
    group = permission_group_manage_users
    assert not issubclass(type(group), ModelWithMetadata)
    group_id = graphene.Node.to_global_id("Group", group.pk)

    # when
    # We use "User" type inside mutation for valid graphql query with fragment
    # without this we are not able to reuse DELETE_PUBLIC_METADATA_MUTATION
    response = execute_clear_public_metadata_for_item(
        api_client, None, group_id, "User"
    )

    # then
    errors = response["data"]["deleteMetadata"]["errors"]
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == MetadataErrorCode.NOT_FOUND.name


def test_delete_public_metadata_for_not_exist_key(api_client, checkout):
    # given
    checkout.metadata_storage.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    checkout.metadata_storage.save(update_fields=["metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout", key="Not-exits"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )


def test_delete_public_metadata_for_one_key(api_client, checkout):
    # given
    checkout.metadata_storage.store_value_in_metadata(
        {PUBLIC_KEY: PUBLIC_VALUE, "to_clear": PUBLIC_VALUE},
    )
    checkout.metadata_storage.save(update_fields=["metadata"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        api_client, None, checkout_id, "Checkout", key="to_clear"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
    )
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        checkout.metadata_storage,
        checkout_id,
        key="to_clear",
    )


def test_delete_public_metadata_another_key_updated_in_meantime(
    staff_api_client, order, permission_manage_orders
):
    # given
    key_to_remove = "to_clear"
    order.store_value_in_metadata(
        {PUBLIC_KEY: PUBLIC_VALUE, key_to_remove: PUBLIC_VALUE},
    )
    order.save(update_fields=["metadata"])
    order_id = graphene.Node.to_global_id("Order", order.pk)

    new_value = "updated_value"

    def update_metadata(*args, **kwargs):
        order.store_value_in_metadata({PUBLIC_KEY: new_value})
        order.save(update_fields=["metadata"])

    # when
    with race_condition.RunBefore(
        "saleor.graphql.meta.mutations.delete_metadata.delete_metadata_keys",
        update_metadata,
    ):
        response = execute_clear_public_metadata_for_item(
            staff_api_client,
            permission_manage_orders,
            order_id,
            "Order",
            key=key_to_remove,
        )

    # then
    order.refresh_from_db()
    assert item_contains_proper_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        order,
        order_id,
        key=PUBLIC_KEY,
        value=new_value,
    )
    assert order.get_value_from_metadata(key_to_remove) is None
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        order,
        order_id,
        key=key_to_remove,
    )
