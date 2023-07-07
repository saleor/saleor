from ....tests.utils import get_graphql_content
from .utils import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

SHOP_METADATA_QUERY = """
    query {
        shop {
            metadata {
            key
            value
            }
            metafield(key: "key")
            metafields(keys: ["key"])
            privateMetadata {
            key
            value
            }
            privateMetafield(key: "private_key")
            privateMetafields(keys: ["private_key"])
        }
}
"""


def test_shop_metadata_query_as_user(
    user_api_client, site_settings, permission_manage_settings
):
    # given
    site_settings.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    site_settings.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    site_settings.save()
    # when
    response = user_api_client.post_graphql(
        SHOP_METADATA_QUERY, permissions=[permission_manage_settings]
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


def test_shop_metadata_query_as_staff_user(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    site_settings.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    site_settings.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    site_settings.save()
    # when
    response = staff_api_client.post_graphql(
        SHOP_METADATA_QUERY, permissions=[permission_manage_settings]
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
