from django.contrib.auth.hashers import make_password

from ...webhooks import (
    validate_auth_user,
    validate_hmac_signature,
    validate_merchant_account,
)


def test_validate_hmac_signature(adyen_plugin, notification_with_hmac_signature):
    hmac_key = "8E60EDDCA27F96095AD5882EF0AA3B05844864710EC089B7967F796AC44AE76E"
    plugin = adyen_plugin()
    config = plugin.config
    config.connection_params["webhook_hmac"] = hmac_key
    assert validate_hmac_signature(notification_with_hmac_signature, config) is True


def test_validate_hmac_signature_missing_key_in_saleor(
    adyen_plugin, notification_with_hmac_signature
):
    plugin = adyen_plugin()
    config = plugin.config
    assert validate_hmac_signature(notification_with_hmac_signature, config) is False


def test_validate_hmac_signature_missing_key_in_notification(
    adyen_plugin, notification
):
    hmac_key = "8E60EDDCA27F96095AD5882EF0AA3B05844864710EC089B7967F796AC44AE76E"
    plugin = adyen_plugin()
    config = plugin.config
    config.connection_params["webhook_hmac"] = hmac_key
    assert validate_hmac_signature(notification(), config) is False


def test_validate_hmac_signature_without_keys(adyen_plugin, notification):
    plugin = adyen_plugin()
    config = plugin.config
    assert validate_hmac_signature(notification(), config) is True


def test_validate_auth_user(adyen_plugin):
    plugin = adyen_plugin()
    config = plugin.config
    config.connection_params["webhook_user"] = "admin@example.com"
    password = make_password("admin")
    config.connection_params["webhook_user_password"] = password
    is_valid = validate_auth_user(
        headers={"Authorization": "Basic YWRtaW5AZXhhbXBsZS5jb206YWRtaW4="},
        gateway_config=config,
    )
    assert is_valid is True


def validate_auth_user_when_header_is_missing(adyen_plugin):
    plugin = adyen_plugin()
    config = plugin.config
    config.connection_params["webhook_user"] = "admin@example.com"
    password = make_password("admin")
    config.connection_params["webhook_user_password"] = password
    is_valid = validate_auth_user(headers={}, gateway_config=config)
    assert is_valid is False


def test_validate_auth_user_when_user_is_missing(adyen_plugin):
    plugin = adyen_plugin()
    config = plugin.config
    is_valid = validate_auth_user(
        headers={"Authorization": "Basic YWRtaW5AZXhhbXBsZS5jb206YWRtaW4="},
        gateway_config=config,
    )
    assert is_valid is False


def test_validate_auth_user_when_auth_is_disabled(adyen_plugin):
    plugin = adyen_plugin()
    config = plugin.config
    is_valid = validate_auth_user(headers={}, gateway_config=config)
    assert is_valid is True


def test_validate_merchant_account(adyen_plugin, notification_with_hmac_signature):
    plugin = adyen_plugin()
    config = plugin.config
    notification_with_hmac_signature[
        "merchantAccountCode"
    ] = config.connection_params.get("merchant_account")
    assert validate_merchant_account(notification_with_hmac_signature, config) is True


def test_validate_merchant_account_invalid_merchant_account(
    adyen_plugin, notification_with_hmac_signature
):
    plugin = adyen_plugin()
    config = plugin.config
    notification_with_hmac_signature["merchantAccountCode"] = "test"
    assert validate_merchant_account(notification_with_hmac_signature, config) is False
