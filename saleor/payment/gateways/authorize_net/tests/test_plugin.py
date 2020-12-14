def test_get_payment_gateway_for_checkout(
    authorize_net_plugin, checkout_with_single_item, address
):
    checkout_with_single_item.billing_address = address
    checkout_with_single_item.save()
    response = authorize_net_plugin.get_payment_gateway_for_checkout(
        checkout_with_single_item, None
    )
    assert response.id == authorize_net_plugin.PLUGIN_ID
    assert response.name == authorize_net_plugin.PLUGIN_NAME
    config = response.config
    assert len(config) == 4
    assert config[0] == {
        "field": "api_login_id",
        "value": authorize_net_plugin.config.connection_params["api_login_id"],
    }
    assert config[1] == {
        "field": "client_key",
        "value": authorize_net_plugin.config.connection_params["client_key"],
    }
    assert config[2] == {
        "field": "use_sandbox",
        "value": authorize_net_plugin.config.connection_params["use_sandbox"],
    }
    assert config[3] == {
        "field": "store_customer_card",
        "value": authorize_net_plugin.config.store_customer,
    }
