import re

import graphene
import pytest
from django_countries import countries

from ..... import __version__
from .....permission.enums import get_permissions_codename
from .....shipping import PostalCodeRuleInclusionType
from .....shipping.models import ShippingMethod
from ....account.enums import CountryCodeEnum
from ....core.utils import str_to_enum
from ....tests.utils import assert_no_permission, get_graphql_content
from ...types import SHOP_ID

SHOP_ID_QUERY = """
    query {
        shop {
            id
        }
    }
"""


def test_shop_id_query(api_client):
    # when
    response = api_client.post_graphql(SHOP_ID_QUERY)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["id"] == graphene.Node.to_global_id("Shop", SHOP_ID)


COUNTRIES_QUERY = """
    query {
        shop {
            countries%(attributes)s {
                code
                country
            }
        }
    }
"""


def test_query_countries(user_api_client):
    # when
    response = user_api_client.post_graphql(COUNTRIES_QUERY % {"attributes": ""})

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["countries"]) == len(countries)


@pytest.mark.parametrize(
    "language_code, expected_value",
    (
        ("", "Afghanistan"),
        ("(languageCode: EN)", "Afghanistan"),
        ("(languageCode: PL)", "Afganistan"),
        ("(languageCode: DE)", "Afghanistan"),
    ),
)
def test_query_countries_with_translation(
    language_code, expected_value, user_api_client
):
    # when
    response = user_api_client.post_graphql(
        COUNTRIES_QUERY % {"attributes": language_code}
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["countries"]) == len(countries)
    assert data["countries"][0]["code"] == "AF"
    assert data["countries"][0]["country"] == expected_value


LIMIT_INFO_QUERY = """
    {
      shop {
        limits {
          currentUsage {
            channels
          }
          allowedUsage {
            channels
          }
        }
      }
    }
"""


def test_cannot_get_shop_limit_info_when_not_staff(user_api_client):
    # given
    query = LIMIT_INFO_QUERY

    # when
    response = user_api_client.post_graphql(query)

    # then
    assert_no_permission(response)


def test_get_shop_limit_info_returns_null_by_default(staff_api_client):
    # given
    query = LIMIT_INFO_QUERY

    # when
    response = staff_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    assert content["data"] == {
        "shop": {
            "limits": {
                "currentUsage": {"channels": None},
                "allowedUsage": {"channels": None},
            }
        }
    }


API_VERSION_QUERY = """
    query {
        shop {
            version
        }
    }
"""


def test_version_query_as_anonymous_user(api_client):
    # when
    response = api_client.post_graphql(API_VERSION_QUERY)

    # then
    assert_no_permission(response)


def test_version_query_as_customer(user_api_client):
    # when
    response = user_api_client.post_graphql(API_VERSION_QUERY)

    # then
    assert_no_permission(response)


def test_version_query_as_app(app_api_client):
    # when
    response = app_api_client.post_graphql(API_VERSION_QUERY)

    # then
    content = get_graphql_content(response)
    assert content["data"]["shop"]["version"] == __version__


def test_version_query_as_staff_user(staff_api_client):
    # when
    response = staff_api_client.post_graphql(API_VERSION_QUERY)

    # then
    content = get_graphql_content(response)
    assert content["data"]["shop"]["version"] == __version__


def test_schema_version_query(api_client):
    # given
    query = """
        query {
            shop {
                schemaVersion
            }
        }
    """
    m = re.match(r"^(\d+)\.(\d+)\.\d+", __version__)
    assert m is not None
    major, minor = m.groups()

    # when
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)

    # then
    assert content["data"]["shop"]["schemaVersion"] == f"{major}.{minor}"


CHANNEL_CURRENCIES_QUERY = """
    query {
        shop {
            channelCurrencies
        }
    }
"""


def test_fetch_channel_currencies(
    staff_api_client, channel_PLN, channel_USD, other_channel_USD
):
    # given
    query = CHANNEL_CURRENCIES_QUERY

    # when
    response = staff_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    assert set(content["data"]["shop"]["channelCurrencies"]) == {
        channel_PLN.currency_code,
        channel_USD.currency_code,
    }


def test_fetch_channel_currencies_by_app(
    app_api_client, channel_PLN, channel_USD, other_channel_USD
):
    # given
    query = CHANNEL_CURRENCIES_QUERY

    # when
    response = app_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    assert set(content["data"]["shop"]["channelCurrencies"]) == {
        channel_PLN.currency_code,
        channel_USD.currency_code,
    }


def test_fetch_channel_currencies_by_customer(api_client, channel_PLN, channel_USD):
    # given
    query = CHANNEL_CURRENCIES_QUERY

    # when
    response = api_client.post_graphql(query)

    # then
    assert_no_permission(response)


def test_query_name(user_api_client, site_settings):
    # given
    query = """
    query {
        shop {
            name
            description
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["description"] == site_settings.description
    assert data["name"] == site_settings.site.name


def test_query_company_address(user_api_client, site_settings, address):
    query = """
    query {
        shop{
            companyAddress{
                city
                streetAddress1
                postalCode
            }
        }
    }
    """
    # given
    site_settings.company_address = address
    site_settings.save()

    # when
    response = user_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    company_address = data["companyAddress"]
    assert company_address["city"] == address.city
    assert company_address["streetAddress1"] == address.street_address_1
    assert company_address["postalCode"] == address.postal_code


def test_query_domain(user_api_client, site_settings, settings):
    # given
    query = """
    query {
        shop {
            domain {
                host
                sslEnabled
                url
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["domain"]["host"] == site_settings.site.domain
    assert data["domain"]["sslEnabled"] == settings.ENABLE_SSL
    assert data["domain"]["url"]


def test_query_languages(settings, user_api_client):
    # given
    query = """
    query {
        shop {
            languages {
                code
                language
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["languages"]) == len(settings.LANGUAGES)


def test_query_permissions(staff_api_client):
    # given
    query = """
    query {
        shop {
            permissions {
                code
                name
            }
        }
    }
    """
    permissions_codenames = set(get_permissions_codename())

    # when
    response = staff_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    permissions = data["permissions"]
    permissions_codes = {permission.get("code") for permission in permissions}
    assert len(permissions_codes) == len(permissions_codenames)
    for code in permissions_codes:
        assert code in [str_to_enum(code) for code in permissions_codenames]


def test_query_charge_taxes_on_shipping(api_client, site_settings):
    # given
    query = """
    query {
        shop {
            chargeTaxesOnShipping
        }
    }"""

    # when
    response = api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    charge_taxes_on_shipping = site_settings.charge_taxes_on_shipping
    assert data["chargeTaxesOnShipping"] == charge_taxes_on_shipping


def test_query_digital_content_settings(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    query = """
    query {
        shop {
            automaticFulfillmentDigitalProducts
            defaultDigitalMaxDownloads
            defaultDigitalUrlValidDays
        }
    }"""

    max_download = 2
    url_valid_days = 3
    site_settings.automatic_fulfillment_digital_products = True
    site_settings.default_digital_max_downloads = max_download
    site_settings.default_digital_url_valid_days = url_valid_days
    site_settings.save()

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    automatic_fulfillment = site_settings.automatic_fulfillment_digital_products
    assert data["automaticFulfillmentDigitalProducts"] == automatic_fulfillment
    assert data["defaultDigitalMaxDownloads"] == max_download
    assert data["defaultDigitalUrlValidDays"] == url_valid_days


QUERY_RETRIEVE_DEFAULT_MAIL_SENDER_SETTINGS = """
    {
      shop {
        defaultMailSenderName
        defaultMailSenderAddress
      }
    }
"""


def test_query_default_mail_sender_settings(
    staff_api_client, site_settings, permission_manage_settings
):
    # given
    site_settings.default_mail_sender_name = "Mirumee Labs Info"
    site_settings.default_mail_sender_address = "hello@example.com"
    site_settings.save(
        update_fields=["default_mail_sender_name", "default_mail_sender_address"]
    )

    query = QUERY_RETRIEVE_DEFAULT_MAIL_SENDER_SETTINGS

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["shop"]
    assert data["defaultMailSenderName"] == "Mirumee Labs Info"
    assert data["defaultMailSenderAddress"] == "hello@example.com"


def test_query_default_mail_sender_settings_not_set(
    staff_api_client, site_settings, permission_manage_settings, settings
):
    # given
    site_settings.default_mail_sender_name = ""
    site_settings.default_mail_sender_address = None
    site_settings.save(
        update_fields=["default_mail_sender_name", "default_mail_sender_address"]
    )

    settings.DEFAULT_FROM_EMAIL = "default@example.com"

    query = QUERY_RETRIEVE_DEFAULT_MAIL_SENDER_SETTINGS

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["shop"]
    assert data["defaultMailSenderName"] == ""
    assert data["defaultMailSenderAddress"] is None


def test_query_default_country(user_api_client, settings):
    # given
    settings.DEFAULT_COUNTRY = "US"
    query = """
    query {
        shop {
            defaultCountry {
                code
                country
            }
        }
    }
    """

    # when
    response = user_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["defaultCountry"]
    assert data["code"] == settings.DEFAULT_COUNTRY
    assert data["country"] == "United States of America"


AVAILABLE_EXTERNAL_AUTHENTICATIONS_QUERY = """
    query{
        shop {
            availableExternalAuthentications{
                id
                name
            }
        }
    }
"""


@pytest.mark.parametrize(
    "external_auths",
    [
        [{"id": "auth1", "name": "Auth-1"}],
        [{"id": "auth1", "name": "Auth-1"}, {"id": "auth2", "name": "Auth-2"}],
        [],
    ],
)
def test_query_available_external_authentications(
    external_auths, user_api_client, monkeypatch
):
    # given
    monkeypatch.setattr(
        "saleor.plugins.manager.PluginsManager.list_external_authentications",
        lambda self, active_only: external_auths,
    )
    query = AVAILABLE_EXTERNAL_AUTHENTICATIONS_QUERY

    # when
    response = user_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availableExternalAuthentications"]
    assert data == external_auths


AVAILABLE_PAYMENT_GATEWAYS_QUERY = """
    query Shop($currency: String){
        shop {
            availablePaymentGateways(currency: $currency) {
                id
                name
            }
        }
    }
"""


def test_query_available_payment_gateways(user_api_client, sample_gateway, channel_USD):
    # given
    query = AVAILABLE_PAYMENT_GATEWAYS_QUERY

    # when
    response = user_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availablePaymentGateways"]
    assert {gateway["id"] for gateway in data} == {
        "mirumee.payments.dummy",
        "sampleDummy.active",
    }
    assert {gateway["name"] for gateway in data} == {
        "Dummy",
        "SampleDummy",
    }


def test_query_available_payment_gateways_specified_currency_USD(
    user_api_client, sample_gateway, channel_USD
):
    # given
    query = AVAILABLE_PAYMENT_GATEWAYS_QUERY

    # when
    response = user_api_client.post_graphql(query, {"currency": "USD"})

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availablePaymentGateways"]
    assert {gateway["id"] for gateway in data} == {
        "mirumee.payments.dummy",
        "sampleDummy.active",
    }
    assert {gateway["name"] for gateway in data} == {
        "Dummy",
        "SampleDummy",
    }


def test_query_available_payment_gateways_specified_currency_EUR(
    user_api_client, sample_gateway, channel_USD
):
    # given
    query = AVAILABLE_PAYMENT_GATEWAYS_QUERY

    # when
    response = user_api_client.post_graphql(query, {"currency": "EUR"})

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availablePaymentGateways"]
    assert data[0]["id"] == "sampleDummy.active"
    assert data[0]["name"] == "SampleDummy"


AVAILABLE_SHIPPING_METHODS_QUERY = """
    query Shop($channel: String!, $address: AddressInput){
        shop {
            availableShippingMethods(channel: $channel, address: $address) {
                id
                name
            }
        }
    }
"""


def test_query_available_shipping_methods_no_address(
    staff_api_client, shipping_method, shipping_method_channel_PLN, channel_USD
):
    # given
    query = AVAILABLE_SHIPPING_METHODS_QUERY

    # when
    response = staff_api_client.post_graphql(query, {"channel": channel_USD.slug})

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availableShippingMethods"]
    assert len(data) > 0
    assert {ship_meth["id"] for ship_meth in data} == {
        graphene.Node.to_global_id("ShippingMethod", ship_meth.pk)
        for ship_meth in ShippingMethod.objects.filter(
            shipping_zone__channels__slug=channel_USD.slug,
            channel_listings__channel__slug=channel_USD.slug,
        )
    }


def test_query_available_shipping_methods_no_channel_shipping_zones(
    staff_api_client, shipping_method, shipping_method_channel_PLN, channel_USD
):
    # given
    query = AVAILABLE_SHIPPING_METHODS_QUERY
    channel_USD.shipping_zones.clear()

    # when
    response = staff_api_client.post_graphql(query, {"channel": channel_USD.slug})

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availableShippingMethods"]
    assert len(data) == 0


def test_query_available_shipping_methods_for_given_address(
    staff_api_client,
    channel_USD,
    shipping_method,
    shipping_zone_without_countries,
    address,
):
    # given
    query = AVAILABLE_SHIPPING_METHODS_QUERY
    shipping_method_count = ShippingMethod.objects.count()
    variables = {
        "channel": channel_USD.slug,
        "address": {"country": CountryCodeEnum.US.name},
    }

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availableShippingMethods"]
    assert len(data) == shipping_method_count - 1
    assert graphene.Node.to_global_id(
        "ShippingMethodType",
        shipping_zone_without_countries.shipping_methods.first().pk,
    ) not in {ship_meth["id"] for ship_meth in data}


def test_query_available_shipping_methods_for_excluded_postal_code(
    staff_api_client, channel_USD, shipping_method
):
    # given
    query = AVAILABLE_SHIPPING_METHODS_QUERY
    variables = {
        "channel": channel_USD.slug,
        "address": {"country": CountryCodeEnum.PL.name, "postalCode": "53-601"},
    }
    shipping_method.postal_code_rules.create(
        start="53-600", end="54-600", inclusion_type=PostalCodeRuleInclusionType.EXCLUDE
    )

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availableShippingMethods"]
    assert graphene.Node.to_global_id("ShippingMethodType", shipping_method.pk) not in {
        ship_meth["id"] for ship_meth in data
    }


def test_query_available_shipping_methods_for_included_postal_code(
    staff_api_client, channel_USD, shipping_method
):
    # given
    query = AVAILABLE_SHIPPING_METHODS_QUERY
    variables = {
        "channel": channel_USD.slug,
        "address": {"country": CountryCodeEnum.PL.name, "postalCode": "53-601"},
    }
    shipping_method.postal_code_rules.create(
        start="53-600", end="54-600", inclusion_type=PostalCodeRuleInclusionType.INCLUDE
    )

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availableShippingMethods"]
    assert graphene.Node.to_global_id("ShippingMethod", shipping_method.pk) in {
        ship_meth["id"] for ship_meth in data
    }


def test_staff_notification_query(
    staff_api_client,
    staff_user,
    permission_manage_settings,
    staff_notification_recipient,
):
    # given
    query = """
        {
            shop {
                staffNotificationRecipients {
                    active
                    email
                    user {
                        firstName
                        lastName
                        email
                    }
                }
            }
        }
    """

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )

    # then
    content = get_graphql_content(response)

    assert content["data"]["shop"]["staffNotificationRecipients"] == [
        {
            "active": True,
            "email": staff_user.email,
            "user": {
                "firstName": staff_user.first_name,
                "lastName": staff_user.last_name,
                "email": staff_user.email,
            },
        }
    ]


COUNTRY_FILTER_QUERY = """
    query($filter: CountryFilterInput!) {
        shop {
            countries(filter: $filter){
            code
            }
        }
    }

"""


def test_query_countries_filter_shiping_zones_attached_true(
    user_api_client, shipping_zones
):
    # given
    variables = {"filter": {"attachedToShippingZones": True}}
    fixture_countries_code_set = {zone.countries[0].code for zone in shipping_zones}

    # when
    response = user_api_client.post_graphql(COUNTRY_FILTER_QUERY, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["shop"]["countries"]
    countries_codes_results = {country["code"] for country in data}

    # then
    assert countries_codes_results == fixture_countries_code_set
    assert len(data) == len(shipping_zones)


def test_query_countries_filter_shiping_zones_attached_false(
    user_api_client, shipping_zones
):
    # given
    variables = {"filter": {"attachedToShippingZones": False}}
    fixture_countries_code_set = {zone.countries[0].code for zone in shipping_zones}

    # when
    response = user_api_client.post_graphql(COUNTRY_FILTER_QUERY, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["shop"]["countries"]
    countries_codes_results = {country["code"] for country in data}

    # then
    assert not any(
        code in countries_codes_results for code in fixture_countries_code_set
    )
    assert len(data) == (len(countries) - len(shipping_zones))


def test_query_countries_filter_shiping_zones_attached_none(
    user_api_client, shipping_zones
):
    # given
    variables = {"filter": {"attachedToShippingZones": None}}

    # when
    response = user_api_client.post_graphql(COUNTRY_FILTER_QUERY, variables=variables)
    content = get_graphql_content(response)

    data = content["data"]["shop"]["countries"]

    # then
    assert len(data) == len(countries)


def test_query_allow_login_without_confirmation(
    staff_api_client, permission_manage_settings, site_settings
):
    # given
    query = """
    query {
        shop {
            allowLoginWithoutConfirmation
        }
    }
    """

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["shop"]["allowLoginWithoutConfirmation"] == (
        site_settings.allow_login_without_confirmation
    )
