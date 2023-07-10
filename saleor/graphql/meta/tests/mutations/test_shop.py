from ....tests.utils import get_graphql_content
from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE

SHOP_SETTINGS_UPDATE_METADATA_MUTATION = """
    mutation updateShopMetadata($input: ShopSettingsInput!) {
        shopSettingsUpdate(input: $input) {
            shop {
            metadata {
                key
                value
            }
            privateMetadata {
                key
                value
            }
            }
        }
    }
"""


def test_shop_settings_update_metadata(staff_api_client, permission_manage_settings):
    # given
    query = SHOP_SETTINGS_UPDATE_METADATA_MUTATION
    metadata = [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}]
    private_metadata = [{"key": PRIVATE_KEY, "value": PRIVATE_VALUE}]
    variables = {
        "input": {
            "metadata": metadata,
            "privateMetadata": private_metadata,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]["shop"]
    assert data["metadata"] == metadata
    assert data["privateMetadata"] == private_metadata
