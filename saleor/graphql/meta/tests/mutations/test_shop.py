from unittest import mock

import graphene
from django.contrib.sites.models import Site

from ....shop.types import SHOP_ID
from ....tests.utils import get_graphql_content
from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE
from .test_delete_metadata import (
    execute_clear_public_metadata_for_item,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)

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


@mock.patch("saleor.plugins.manager.PluginsManager.shop_metadata_updated")
def test_shop_settings_update_metadata(
    mock_shop_metadata_updated, staff_api_client, permission_manage_settings
):
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
    mock_shop_metadata_updated.assert_called_once()


@mock.patch("saleor.plugins.manager.PluginsManager.shop_metadata_updated")
def test_shop_settings_update_metadata_does_not_trigger_webhook_when_metadata_unchanged(
    mock_shop_metadata_updated, staff_api_client, permission_manage_settings
):
    # given
    site_settings = Site.objects.get_current().settings
    site_settings.metadata = {PUBLIC_KEY: PUBLIC_VALUE}
    site_settings.save(update_fields=["metadata"])

    query = SHOP_SETTINGS_UPDATE_METADATA_MUTATION
    metadata = [{"key": PUBLIC_KEY, "value": PUBLIC_VALUE}]
    variables = {"input": {"metadata": metadata}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]["shop"]
    assert data["metadata"] == metadata
    mock_shop_metadata_updated.assert_not_called()


def test_delete_private_metadata_for_shop(staff_api_client, permission_manage_settings):
    # given
    site_settings = Site.objects.get_current().settings
    shop_id = graphene.Node.to_global_id("Shop", SHOP_ID)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_settings,
        shop_id,
        "Shop",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        site_settings,
        shop_id,
    )


def test_delete_public_metadata_for_shop(staff_api_client, permission_manage_settings):
    # given
    site_settings = Site.objects.get_current().settings
    shop_id = graphene.Node.to_global_id("Shop", SHOP_ID)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_settings,
        shop_id,
        "Shop",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        site_settings,
        shop_id,
    )


def test_add_public_metadata_for_shop(staff_api_client, permission_manage_settings):
    # given
    site_settings = Site.objects.get_current().settings
    shop_id = graphene.Node.to_global_id("Shop", SHOP_ID)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_settings,
        shop_id,
        "Shop",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], site_settings, shop_id
    )


def test_add_private_metadata_for_shop(staff_api_client, permission_manage_settings):
    # given
    site_settings = Site.objects.get_current().settings
    shop_id = graphene.Node.to_global_id("Shop", SHOP_ID)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_settings,
        shop_id,
        "Shop",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        site_settings,
        shop_id,
    )
