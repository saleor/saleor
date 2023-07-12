from ....tests.utils import assert_no_permission, get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

SHOP_PRIVATE_AND_PUBLIC_METADATA_QUERY = """
    query shopMetadata($key: String!, $privateKey: String!) {
        shop {
            metadata {
                key
                value
            }
            metafield(key: $key)
            metafields(keys: [$key])
            privateMetadata {
                key
                value
            }
            privateMetafield(key: $privateKey)
            privateMetafields(keys: [$privateKey])
        }
}
"""

SHOP_PUBLIC_METADATA_QUERY = """
    query shopMetadata($key: String!) {
        shop {
            metadata {
                key
                value
            }
            metafield(key: $key)
            metafields(keys: [$key])
        }
}
"""


def test_customer_user_has_no_permission_to_shop_private_metadata(
    user_api_client, site_settings
):
    # given
    site_settings.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    site_settings.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    site_settings.save()

    # when
    response = user_api_client.post_graphql(
        SHOP_PRIVATE_AND_PUBLIC_METADATA_QUERY,
        variables={"key": PUBLIC_KEY, "privateKey": PRIVATE_KEY},
    )

    # then
    assert_no_permission(response)


def test_customer_user_has_access_to_shop_public_metadata(
    user_api_client, site_settings
):
    # given
    site_settings.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    site_settings.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    site_settings.save()

    # when
    response = user_api_client.post_graphql(
        SHOP_PUBLIC_METADATA_QUERY,
        variables={"key": PUBLIC_KEY},
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["metadata"][0]["key"] == PUBLIC_KEY
    assert data["metadata"][0]["value"] == PUBLIC_VALUE
    assert data["metafield"] == PUBLIC_VALUE
    assert data["metafields"] == {PUBLIC_KEY: PUBLIC_VALUE}


def test_shop_metadata_query_as_staff_user(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    site_settings.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    site_settings.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    site_settings.save()
    # when
    response = staff_api_client.post_graphql(
        SHOP_PRIVATE_AND_PUBLIC_METADATA_QUERY,
        permissions=[permission_manage_settings],
        variables={"key": PUBLIC_KEY, "privateKey": PRIVATE_KEY},
    )
    content = get_graphql_content(response)

    data = content["data"]["shop"]
    # then
    assert data["metadata"][0]["key"] == PUBLIC_KEY
    assert data["metadata"][0]["value"] == PUBLIC_VALUE
    assert data["metafield"] == PUBLIC_VALUE
    assert data["metafields"] == {PUBLIC_KEY: PUBLIC_VALUE}

    assert data["privateMetadata"][0]["key"] == PRIVATE_KEY
    assert data["privateMetadata"][0]["value"] == PRIVATE_VALUE
    assert data["privateMetafield"] == PRIVATE_VALUE
    assert data["privateMetafields"] == {PRIVATE_KEY: PRIVATE_VALUE}
