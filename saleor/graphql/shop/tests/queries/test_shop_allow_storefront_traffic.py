from ....tests.utils import get_graphql_content

SHOP_ALLOW_STOREFRONT_TRAFFIC_QUERY = """
    query {
        shop { allowStorefrontTraffic }
    }
"""


def test_shop_allow_storefront_traffic_defaults_to_true(api_client, site_settings):
    # given: freshly created site settings (default)
    # then: the model default is True
    assert site_settings.allow_storefront_traffic is True

    # when: read through the API (public, no auth needed)
    response = api_client.post_graphql(SHOP_ALLOW_STOREFRONT_TRAFFIC_QUERY)
    content = get_graphql_content(response)

    # then
    assert content["data"]["shop"]["allowStorefrontTraffic"] is True


def test_shop_allow_storefront_traffic_reflects_stored_value(
    staff_api_client, site_settings
):
    # given
    site_settings.allow_storefront_traffic = False
    site_settings.save(update_fields=["allow_storefront_traffic"])

    # when: staff client is authenticated, so enforcement never triggers here
    response = staff_api_client.post_graphql(SHOP_ALLOW_STOREFRONT_TRAFFIC_QUERY)
    content = get_graphql_content(response)

    # then
    assert content["data"]["shop"]["allowStorefrontTraffic"] is False
