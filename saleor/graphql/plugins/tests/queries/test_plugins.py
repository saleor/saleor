import copy
from unittest import mock

import graphene
import pytest

from .....plugins.base_plugin import ConfigurationTypeField
from .....plugins.manager import get_plugins_manager
from .....plugins.tests.sample_plugins import ChannelPluginSample, PluginSample
from ....tests.utils import assert_no_permission, get_graphql_content

PLUGINS_QUERY = """
    {
      plugins(first:1){
        edges{
          node{
            name
            description
            id
            globalConfiguration{
              active
              configuration{
                name
                value
                helpText
                type
                label
              }
            }
            channelConfigurations{
              active
              channel{
                id
                slug
              }
              configuration{
                name
                value
                helpText
                type
                label
              }
            }
          }
        }
      }
    }
"""


def test_query_plugin_configurations(staff_api_client_can_manage_plugins, settings):
    # Enable test plugin
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    response = staff_api_client_can_manage_plugins.post_graphql(PLUGINS_QUERY)
    content = get_graphql_content(response)

    plugins = content["data"]["plugins"]["edges"]

    assert len(plugins) == 1
    plugin = plugins[0]["node"]
    manager = get_plugins_manager()
    sample_plugin = manager.get_plugin(PluginSample.PLUGIN_ID)
    configuration_structure = PluginSample.CONFIG_STRUCTURE

    assert plugin["id"] == sample_plugin.PLUGIN_ID
    assert plugin["name"] == sample_plugin.PLUGIN_NAME
    assert plugin["description"] == sample_plugin.PLUGIN_DESCRIPTION

    assert plugin["globalConfiguration"]["active"] == sample_plugin.DEFAULT_ACTIVE
    configuration = plugin["globalConfiguration"]["configuration"]
    for index, configuration_item in enumerate(configuration):
        assert configuration_item["name"] == sample_plugin.configuration[index]["name"]

        if (
            configuration_structure[configuration_item["name"]]["type"]
            == ConfigurationTypeField.STRING
        ):
            assert (
                configuration_item["value"]
                == sample_plugin.configuration[index]["value"]
            )
        elif configuration_item["value"] is None:
            assert not sample_plugin.configuration[index]["value"]
        else:
            assert (
                configuration_item["value"]
                == str(sample_plugin.configuration[index]["value"]).lower()
            )


def test_query_plugin_configurations_for_channel_configurations(
    staff_api_client_can_manage_plugins, settings, channel_PLN
):
    # Enable test plugin
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.ChannelPluginSample"]

    response = staff_api_client_can_manage_plugins.post_graphql(PLUGINS_QUERY)
    content = get_graphql_content(response)

    plugins = content["data"]["plugins"]["edges"]

    assert len(plugins) == 1
    plugin = plugins[0]["node"]
    manager = get_plugins_manager()
    sample_plugin = manager.get_plugin(
        ChannelPluginSample.PLUGIN_ID, channel_slug=channel_PLN.slug
    )
    confiugration_structure = ChannelPluginSample.CONFIG_STRUCTURE

    assert plugin["id"] == sample_plugin.PLUGIN_ID
    assert plugin["name"] == sample_plugin.PLUGIN_NAME
    assert plugin["description"] == sample_plugin.PLUGIN_DESCRIPTION

    assert not plugin["globalConfiguration"]

    assert len(plugin["channelConfigurations"]) == 1

    assert plugin["channelConfigurations"][0]["active"] == sample_plugin.DEFAULT_ACTIVE
    configuration = plugin["channelConfigurations"][0]["configuration"]
    for index, configuration_item in enumerate(configuration):
        assert configuration_item["name"] == sample_plugin.configuration[index]["name"]

        if (
            confiugration_structure[configuration_item["name"]]["type"]
            == ConfigurationTypeField.STRING
        ):
            assert (
                configuration_item["value"]
                == sample_plugin.configuration[index]["value"]
            )
        elif configuration_item["value"] is None:
            assert not sample_plugin.configuration[index]["value"]
        else:
            assert (
                configuration_item["value"]
                == str(sample_plugin.configuration[index]["value"]).lower()
            )


@pytest.mark.parametrize(
    "password, expected_password, api_key, expected_api_key, cert, expected_cert",
    [
        (None, None, None, None, None, None),
        ("ABCDEFGHIJ", "", "123456789", "6789", "long text\n with new\n lines", "ines"),
        ("", None, "", None, "", None),
        (None, None, "1234", "4", None, None),
    ],
)
def test_query_plugins_hides_secret_fields(
    password,
    expected_password,
    api_key,
    expected_api_key,
    cert,
    expected_cert,
    staff_api_client,
    permission_manage_plugins,
    settings,
):
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    manager = get_plugins_manager()
    plugin = manager.get_plugin(PluginSample.PLUGIN_ID)
    configuration = copy.deepcopy(plugin.configuration)
    for conf_field in configuration:
        if conf_field["name"] == "Password":
            conf_field["value"] = password
        if conf_field["name"] == "API private key":
            conf_field["value"] = api_key
        if conf_field["name"] == "certificate":
            conf_field["value"] = cert
    manager.save_plugin_configuration(
        PluginSample.PLUGIN_ID,
        None,
        {
            "active": True,
            "configuration": configuration,
            "name": PluginSample.PLUGIN_NAME,
        },
    )

    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    response = staff_api_client.post_graphql(PLUGINS_QUERY)
    content = get_graphql_content(response)

    plugins = content["data"]["plugins"]["edges"]
    assert len(plugins) == 1
    plugin = plugins[0]["node"]

    for conf_field in plugin["globalConfiguration"]["configuration"]:
        if conf_field["name"] == "Password":
            assert conf_field["value"] == expected_password
        if conf_field["name"] == "API private key":
            assert conf_field["value"] == expected_api_key


@pytest.mark.parametrize(
    "password, expected_password, api_key, expected_api_key, cert, expected_cert",
    [
        (None, None, None, None, None, None),
        ("ABCDEFGHIJ", "", "123456789", "6789", "long text\n with new\n lines", "ines"),
        ("", None, "", None, "", None),
        (None, None, "1234", "4", None, None),
    ],
)
def test_query_plugins_hides_secret_fields_for_channel_configurations(
    password,
    expected_password,
    api_key,
    expected_api_key,
    cert,
    expected_cert,
    staff_api_client,
    permission_manage_plugins,
    settings,
    channel_PLN,
):
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.ChannelPluginSample"]
    manager = get_plugins_manager()
    plugin = manager.get_plugin(
        ChannelPluginSample.PLUGIN_ID, channel_slug=channel_PLN.slug
    )
    configuration = copy.deepcopy(plugin.configuration)
    for conf_field in configuration:
        if conf_field["name"] == "Password":
            conf_field["value"] = password
        if conf_field["name"] == "API private key":
            conf_field["value"] = api_key
        if conf_field["name"] == "certificate":
            conf_field["value"] = cert
    manager.save_plugin_configuration(
        ChannelPluginSample.PLUGIN_ID,
        channel_PLN.slug,
        {
            "active": True,
            "configuration": configuration,
            "name": PluginSample.PLUGIN_NAME,
        },
    )

    staff_api_client.user.user_permissions.add(permission_manage_plugins)
    response = staff_api_client.post_graphql(PLUGINS_QUERY)
    content = get_graphql_content(response)

    plugins = content["data"]["plugins"]["edges"]
    assert len(plugins) == 1
    plugin = plugins[0]["node"]

    assert not plugin["globalConfiguration"]

    assert len(plugin["channelConfigurations"]) == 1

    for conf_field in plugin["channelConfigurations"][0]["configuration"]:
        if conf_field["name"] == "Password":
            assert conf_field["value"] == expected_password
        if conf_field["name"] == "API private key":
            assert conf_field["value"] == expected_api_key


def test_query_plugin_configurations_as_customer_user(user_api_client, settings):
    settings.PLUGINS = ["saleor.plugins.tests.sample_plugins.PluginSample"]
    response = user_api_client.post_graphql(PLUGINS_QUERY)

    assert_no_permission(response)


@pytest.mark.parametrize(
    "plugin_filter_fields, count",
    [
        ({"search": "PluginSample"}, 1),
        ({"search": "description"}, 2),
        ({"active": True}, 3),
        ({"search": "Plugin"}, 3),
        ({"active": False, "search": "Plugin"}, 1),
        ({"type": "GLOBAL"}, 3),
        ({"active": False, "type": "GLOBAL"}, 1),
        ({"active": True, "type": "GLOBAL"}, 2),
        ({"type": "PER_CHANNEL"}, 1),
        ({"active": False, "type": "PER_CHANNEL"}, 0),
        ({"active": True, "type": "PER_CHANNEL"}, 1),
    ],
)
def test_plugins_query_with_filter(
    plugin_filter_fields,
    count,
    staff_api_client_can_manage_plugins,
    settings,
    channel_PLN,
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.ActivePlugin",
        "saleor.plugins.tests.sample_plugins.ChannelPluginSample",
    ]
    plugin_filter = {
        "search": plugin_filter_fields.get("search"),
        "type": plugin_filter_fields.get("type"),
    }
    if plugin_filter_fields.get("active") is not None:
        plugin_filter["statusInChannels"] = {
            "active": plugin_filter_fields.get("active"),
            "channels": [graphene.Node.to_global_id("Channel", channel_PLN.id)],
        }
    query = """
        query ($filter: PluginFilterInput) {
            plugins(first: 5, filter:$filter) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    variables = {"filter": plugin_filter}
    response = staff_api_client_can_manage_plugins.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["plugins"]["totalCount"] == count


QUERY_PLUGIN_WITH_SORT = """
    query ($sort_by: PluginSortingInput!) {
        plugins(first:5, sortBy: $sort_by) {
            edges{
                node{
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "plugin_sort, result_order",
    [
        (
            {"field": "NAME", "direction": "ASC"},
            ["Active", "PluginInactive", "PluginSample"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["PluginSample", "PluginInactive", "Active"],
        ),
        (
            {"field": "IS_ACTIVE", "direction": "ASC"},
            ["PluginInactive", "Active", "PluginSample"],
        ),
        (
            {"field": "IS_ACTIVE", "direction": "DESC"},
            ["Active", "PluginSample", "PluginInactive"],
        ),
    ],
)
def test_query_plugins_with_sort(
    plugin_sort, result_order, staff_api_client_can_manage_plugins, settings
):
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.PluginInactive",
        "saleor.plugins.tests.sample_plugins.ActivePlugin",
    ]
    variables = {"sort_by": plugin_sort}
    response = staff_api_client_can_manage_plugins.post_graphql(
        QUERY_PLUGIN_WITH_SORT, variables
    )
    content = get_graphql_content(response)
    plugins = content["data"]["plugins"]["edges"]

    for order, plugin_name in enumerate(result_order):
        assert plugins[order]["node"]["name"] == plugin_name


def test_cannot_retrieve_hidden_plugins(
    settings, staff_api_client_can_manage_plugins, channel_PLN
):
    """Ensure one cannot see hidden plugins when listing"""
    settings.PLUGINS = [
        "saleor.plugins.tests.sample_plugins.ChannelPluginSample",
        "saleor.plugins.tests.sample_plugins.PluginSample",
        "saleor.plugins.tests.sample_plugins.ActivePlugin",
    ]

    query = """{
        plugins(first: 100) {
            edges { node { id } }
        }
    }"""

    # Should return all plugins when none hidden
    response = staff_api_client_can_manage_plugins.post_graphql(query)
    content = get_graphql_content(response)
    plugin_ids = {
        plugin_data["node"]["id"] for plugin_data in content["data"]["plugins"]["edges"]
    }
    assert plugin_ids == {
        "mirumee.x.plugin.active",
        "channel.plugin.sample",
        "plugin.sample",
    }

    # Hide global plugin
    with mock.patch.object(PluginSample, "HIDDEN", new=True):
        # Hide per-channel plugin
        with mock.patch.object(ChannelPluginSample, "HIDDEN", new=True):
            response = staff_api_client_can_manage_plugins.post_graphql(query)

    # The two hidden plugins should not have been returned
    content = get_graphql_content(response)
    plugin_ids = {
        plugin_data["node"]["id"] for plugin_data in content["data"]["plugins"]["edges"]
    }
    assert plugin_ids == {
        "mirumee.x.plugin.active",
    }
