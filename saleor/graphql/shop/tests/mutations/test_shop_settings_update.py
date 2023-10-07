from unittest.mock import ANY

import pytest

from .....core.error_codes import ShopErrorCode
from .....site.models import Site
from ....tests.utils import get_graphql_content

SHOP_SETTINGS_UPDATE_MUTATION = """
    mutation updateSettings($input: ShopSettingsInput!) {
        shopSettingsUpdate(input: $input) {
            shop {
                automaticFulfillmentDigitalProducts
                defaultDigitalMaxDownloads
                defaultDigitalUrlValidDays
                headerText,
                includeTaxesInPrices,
                chargeTaxesOnShipping,
                fulfillmentAutoApprove,
                fulfillmentAllowUnpaid
                enableAccountConfirmationByEmail
                reserveStockDurationAnonymousUser
                reserveStockDurationAuthenticatedUser
                limitQuantityPerCheckout
                allowLoginWithoutConfirmation
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_shop_digital_content_settings_mutation(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    query = SHOP_SETTINGS_UPDATE_MUTATION

    max_downloads = 15
    url_valid_days = 30
    variables = {
        "input": {
            "automaticFulfillmentDigitalProducts": True,
            "defaultDigitalMaxDownloads": max_downloads,
            "defaultDigitalUrlValidDays": url_valid_days,
        }
    }

    assert not site_settings.automatic_fulfillment_digital_products

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["shopSettingsUpdate"]["shop"]
    assert data["automaticFulfillmentDigitalProducts"]
    assert data["defaultDigitalMaxDownloads"]
    assert data["defaultDigitalUrlValidDays"]
    site_settings.refresh_from_db()
    assert site_settings.automatic_fulfillment_digital_products
    assert site_settings.default_digital_max_downloads == max_downloads
    assert site_settings.default_digital_url_valid_days == url_valid_days


def test_shop_settings_mutation(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    query = SHOP_SETTINGS_UPDATE_MUTATION
    assert site_settings.enable_account_confirmation_by_email
    charge_taxes_on_shipping = site_settings.charge_taxes_on_shipping
    new_charge_taxes_on_shipping = not charge_taxes_on_shipping
    variables = {
        "input": {
            "includeTaxesInPrices": False,
            "headerText": "Lorem ipsum",
            "chargeTaxesOnShipping": new_charge_taxes_on_shipping,
            "fulfillmentAllowUnpaid": False,
            "enableAccountConfirmationByEmail": False,
            "allowLoginWithoutConfirmation": True,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]["shop"]

    # then
    assert data["headerText"] == "Lorem ipsum"
    assert data["includeTaxesInPrices"] is False
    assert data["chargeTaxesOnShipping"] == new_charge_taxes_on_shipping
    assert data["fulfillmentAutoApprove"] is True
    assert data["fulfillmentAllowUnpaid"] is False
    assert data["enableAccountConfirmationByEmail"] is False
    assert data["allowLoginWithoutConfirmation"] is True

    site_settings.refresh_from_db()
    assert not site_settings.include_taxes_in_prices
    assert site_settings.charge_taxes_on_shipping == new_charge_taxes_on_shipping
    assert site_settings.enable_account_confirmation_by_email is False
    assert site_settings.allow_login_without_confirmation is True


def test_shop_reservation_settings_mutation(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    query = SHOP_SETTINGS_UPDATE_MUTATION
    variables = {
        "input": {
            "reserveStockDurationAnonymousUser": 42,
            "reserveStockDurationAuthenticatedUser": 24,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]["shop"]
    assert data["reserveStockDurationAnonymousUser"] == 42
    assert data["reserveStockDurationAuthenticatedUser"] == 24
    site_settings.refresh_from_db()
    assert site_settings.reserve_stock_duration_anonymous_user == 42
    assert site_settings.reserve_stock_duration_authenticated_user == 24


def test_shop_reservation_disable_settings_mutation(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    query = SHOP_SETTINGS_UPDATE_MUTATION
    variables = {
        "input": {
            "reserveStockDurationAnonymousUser": None,
            "reserveStockDurationAuthenticatedUser": None,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]["shop"]
    assert data["reserveStockDurationAnonymousUser"] is None
    assert data["reserveStockDurationAuthenticatedUser"] is None
    site_settings.refresh_from_db()
    assert site_settings.reserve_stock_duration_anonymous_user is None
    assert site_settings.reserve_stock_duration_authenticated_user is None


def test_shop_reservation_set_negative_settings_mutation(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    query = SHOP_SETTINGS_UPDATE_MUTATION
    variables = {
        "input": {
            "reserveStockDurationAnonymousUser": -14,
            "reserveStockDurationAuthenticatedUser": -6,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]["shop"]
    assert data["reserveStockDurationAnonymousUser"] is None
    assert data["reserveStockDurationAuthenticatedUser"] is None
    site_settings.refresh_from_db()
    assert site_settings.reserve_stock_duration_anonymous_user is None
    assert site_settings.reserve_stock_duration_authenticated_user is None


@pytest.mark.parametrize("quantity_value", [25, 1, None])
def test_limit_quantity_per_checkout_mutation(
    staff_api_client, site_settings, permission_manage_settings, quantity_value
):
    # given
    query = SHOP_SETTINGS_UPDATE_MUTATION
    variables = {"input": {"limitQuantityPerCheckout": quantity_value}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]["shop"]
    site_settings.refresh_from_db()

    assert data["limitQuantityPerCheckout"] == quantity_value
    assert site_settings.limit_quantity_per_checkout == quantity_value


@pytest.mark.parametrize("quantity_value", [0, -25])
def test_limit_quantity_per_checkout_neg_or_zero_value(
    staff_api_client, site_settings, permission_manage_settings, quantity_value
):
    # given
    query = SHOP_SETTINGS_UPDATE_MUTATION
    variables = {"input": {"limitQuantityPerCheckout": quantity_value}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["shopSettingsUpdate"]["errors"]
    site_settings.refresh_from_db()

    assert len(errors) == 1
    assert errors.pop() == {
        "field": "limitQuantityPerCheckout",
        "message": "Quantity limit cannot be lower than 1.",
        "code": ShopErrorCode.INVALID.name,
    }

    assert site_settings.limit_quantity_per_checkout == 50  # default


def test_shop_customer_set_password_url_update(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    customer_set_password_url = "http://www.example.com/set_pass/"
    variables = {"input": {"customerSetPasswordUrl": customer_set_password_url}}
    assert site_settings.customer_set_password_url != customer_set_password_url

    # when
    response = staff_api_client.post_graphql(
        SHOP_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]
    assert not data["errors"]
    Site.objects.clear_cache()
    site_settings = Site.objects.get_current().settings
    assert site_settings.customer_set_password_url == customer_set_password_url


@pytest.mark.parametrize(
    "customer_set_password_url",
    [
        ("http://not-allowed-storefron.com/pass"),
        ("http://[value-error-in-urlparse@test/pass"),
        ("without-protocole.com/pass"),
    ],
)
def test_shop_customer_set_password_url_update_invalid_url(
    staff_api_client,
    site_settings,
    permission_manage_settings,
    customer_set_password_url,
):
    # given
    variables = {"input": {"customerSetPasswordUrl": customer_set_password_url}}
    assert not site_settings.customer_set_password_url

    # when
    response = staff_api_client.post_graphql(
        SHOP_SETTINGS_UPDATE_MUTATION,
        variables,
        permissions=[permission_manage_settings],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]
    assert data["errors"][0] == {
        "field": "customerSetPasswordUrl",
        "code": ShopErrorCode.INVALID.name,
        "message": ANY,
    }
    site_settings.refresh_from_db()
    assert not site_settings.customer_set_password_url


MUTATION_UPDATE_DEFAULT_MAIL_SENDER_SETTINGS = """
    mutation updateDefaultSenderSettings($input: ShopSettingsInput!) {
      shopSettingsUpdate(input: $input) {
        shop {
          defaultMailSenderName
          defaultMailSenderAddress
        }
        errors {
          field
          message
        }
      }
    }
"""


def test_update_default_sender_settings(staff_api_client, permission_manage_settings):
    # given
    query = MUTATION_UPDATE_DEFAULT_MAIL_SENDER_SETTINGS

    variables = {
        "input": {
            "defaultMailSenderName": "Dummy Name",
            "defaultMailSenderAddress": "dummy@example.com",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["shopSettingsUpdate"]["shop"]
    assert data["defaultMailSenderName"] == "Dummy Name"
    assert data["defaultMailSenderAddress"] == "dummy@example.com"


@pytest.mark.parametrize(
    "sender_name",
    (
        "\nDummy Name",
        "\rDummy Name",
        "Dummy Name\r",
        "Dummy Name\n",
        "Dummy\rName",
        "Dummy\nName",
    ),
)
def test_update_default_sender_settings_invalid_name(
    staff_api_client, permission_manage_settings, sender_name
):
    # given
    query = MUTATION_UPDATE_DEFAULT_MAIL_SENDER_SETTINGS

    variables = {"input": {"defaultMailSenderName": sender_name}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)

    errors = content["data"]["shopSettingsUpdate"]["errors"]
    assert errors == [
        {"field": "defaultMailSenderName", "message": "New lines are not allowed."}
    ]


@pytest.mark.parametrize(
    "sender_email",
    (
        "\ndummy@example.com",
        "\rdummy@example.com",
        "dummy@example.com\r",
        "dummy@example.com\n",
        "dummy@example\r.com",
        "dummy@example\n.com",
    ),
)
def test_update_default_sender_settings_invalid_email(
    staff_api_client, permission_manage_settings, sender_email
):
    # given
    query = MUTATION_UPDATE_DEFAULT_MAIL_SENDER_SETTINGS

    variables = {"input": {"defaultMailSenderAddress": sender_email}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)

    errors = content["data"]["shopSettingsUpdate"]["errors"]
    assert errors == [
        {"field": "defaultMailSenderAddress", "message": "Enter a valid email address."}
    ]
