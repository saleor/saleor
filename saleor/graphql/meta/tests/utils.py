from ...tests.utils import get_graphql_content

PRIVATE_KEY = "private_key"
PRIVATE_VALUE = "private_vale"

PUBLIC_KEY = "key"
PUBLIC_KEY2 = "key2"
PUBLIC_VALUE = "value"
PUBLIC_VALUE2 = "value2"


def item_contains_proper_public_metadata(
    item_from_response,
    item,
    item_id,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_value_from_metadata(key) == value


def item_contains_multiple_proper_public_metadata(
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
            item.get_value_from_metadata(key) == value,
            item.get_value_from_metadata(key2) == value2,
        ]
    )


def item_contains_proper_private_metadata(
    item_from_response,
    item,
    item_id,
    key=PRIVATE_KEY,
    value=PRIVATE_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_value_from_private_metadata(key) == value


def item_contains_multiple_proper_private_metadata(
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
            item.get_value_from_private_metadata(key) == value,
            item.get_value_from_private_metadata(key2) == value2,
        ]
    )


UPDATE_PUBLIC_METADATA_MUTATION = """
mutation UpdatePublicMetadata($id: ID!, $input: [MetadataInput!]!) {
    updateMetadata(
        id: $id
        input: $input
    ) {
        metadataErrors{
            field
            code
            message
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


def execute_update_public_metadata_for_item(
    client,
    permissions,
    item_id,
    item_type,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
):
    variables = {
        "id": item_id,
        "input": [{"key": key, "value": value}],
    }

    response = client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def execute_update_public_metadata_for_multiple_items(
    client,
    permissions,
    item_id,
    item_type,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
    key2=PUBLIC_KEY2,
    value2=PUBLIC_VALUE2,
):
    variables = {
        "id": item_id,
        "input": [{"key": key, "value": value}, {"key": key2, "value": value2}],
    }

    response = client.post_graphql(
        UPDATE_PUBLIC_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


UPDATE_PRIVATE_METADATA_MUTATION = """
mutation UpdatePrivateMetadata($id: ID!, $input: [MetadataInput!]!) {
    updatePrivateMetadata(
        id: $id
        input: $input
    ) {
        metadataErrors{
            field
            code
        }
        item {
            privateMetadata{
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


def execute_update_private_metadata_for_item(
    client,
    permissions,
    item_id,
    item_type,
    key=PRIVATE_KEY,
    value=PRIVATE_VALUE,
):
    variables = {
        "id": item_id,
        "input": [{"key": key, "value": value}],
    }

    response = client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def execute_update_private_metadata_for_multiple_items(
    client,
    permissions,
    item_id,
    item_type,
    key=PUBLIC_KEY,
    value=PUBLIC_VALUE,
    key2=PUBLIC_KEY2,
    value2=PUBLIC_VALUE2,
):
    variables = {
        "id": item_id,
        "input": [{"key": key, "value": value}, {"key": key2, "value": value2}],
    }

    response = client.post_graphql(
        UPDATE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


DELETE_PUBLIC_METADATA_MUTATION = """
mutation DeletePublicMetadata($id: ID!, $keys: [String!]!) {
    deleteMetadata(
        id: $id
        keys: $keys
    ) {
        metadataErrors{
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


DELETE_PRIVATE_METADATA_MUTATION = """
mutation DeletePrivateMetadata($id: ID!, $keys: [String!]!) {
    deletePrivateMetadata(
        id: $id
        keys: $keys
    ) {
        metadataErrors{
            field
            code
        }
        item {
            privateMetadata{
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


def execute_clear_private_metadata_for_item(
    client,
    permissions,
    item_id,
    item_type,
    key=PRIVATE_KEY,
):
    variables = {
        "id": item_id,
        "keys": [key],
    }

    response = client.post_graphql(
        DELETE_PRIVATE_METADATA_MUTATION % item_type,
        variables,
        permissions=[permissions] if permissions else None,
    )
    response = get_graphql_content(response)
    return response


def execute_clear_private_metadata_for_multiple_items(
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


def item_without_private_metadata(
    item_from_response,
    item,
    item_id,
    key=PRIVATE_KEY,
    value=PRIVATE_VALUE,
):
    if item_from_response["id"] != item_id:
        return False
    item.refresh_from_db()
    return item.get_value_from_private_metadata(key) != value


def item_without_multiple_private_metadata(
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
            item.get_value_from_private_metadata(key) != value,
            item.get_value_from_private_metadata(key2) != value2,
        ]
    )


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
