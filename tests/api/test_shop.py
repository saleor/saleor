from unittest.mock import ANY

import graphene
import pytest
from django_countries import countries

from saleor.account.models import Address
from saleor.core.error_codes import ShopErrorCode
from saleor.core.permissions import get_permissions_codename
from saleor.graphql.core.utils import str_to_enum
from saleor.site import AuthenticationBackends
from saleor.site.models import Site
from tests.api.utils import get_graphql_content


def test_query_authorization_keys(
    authorization_key, staff_api_client, permission_manage_settings
):
    query = """
    query {
        shop {
            authorizationKeys {
                name
                key
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["authorizationKeys"][0]["name"] == "FACEBOOK"
    assert data["authorizationKeys"][0]["key"] == authorization_key.key


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
    response = user_api_client.post_graphql(COUNTRIES_QUERY % {"attributes": ""})
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
    response = user_api_client.post_graphql(
        COUNTRIES_QUERY % {"attributes": language_code}
    )
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["countries"]) == len(countries)
    assert data["countries"][0]["code"] == "AF"
    assert data["countries"][0]["country"] == expected_value


def test_query_currencies(user_api_client, settings):
    query = """
    query {
        shop {
            currencies
            defaultCurrency
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["currencies"]) == len(settings.AVAILABLE_CURRENCIES)
    assert data["defaultCurrency"] == settings.DEFAULT_CURRENCY


def test_query_name(user_api_client, site_settings):
    query = """
    query {
        shop {
            name
            description
        }
    }
    """
    response = user_api_client.post_graphql(query)
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
    site_settings.company_address = address
    site_settings.save()
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    company_address = data["companyAddress"]
    assert company_address["city"] == address.city
    assert company_address["streetAddress1"] == address.street_address_1
    assert company_address["postalCode"] == address.postal_code


def test_query_domain(user_api_client, site_settings, settings):
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
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert data["domain"]["host"] == site_settings.site.domain
    assert data["domain"]["sslEnabled"] == settings.ENABLE_SSL
    assert data["domain"]["url"]


def test_query_languages(settings, user_api_client):
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
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    assert len(data["languages"]) == len(settings.LANGUAGES)


def test_query_permissions(staff_api_client):
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
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    permissions = data["permissions"]
    permissions_codes = {permission.get("code") for permission in permissions}
    assert len(permissions_codes) == len(permissions_codenames)
    for code in permissions_codes:
        assert code in [str_to_enum(code) for code in permissions_codenames]


def test_query_navigation(user_api_client, site_settings):
    query = """
    query {
        shop {
            navigation {
                main {
                    name
                }
                secondary {
                    name
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    navigation_data = content["data"]["shop"]["navigation"]
    assert navigation_data["main"]["name"] == site_settings.top_menu.name
    assert navigation_data["secondary"]["name"] == site_settings.bottom_menu.name


def test_query_charge_taxes_on_shipping(api_client, site_settings):
    query = """
    query {
        shop {
            chargeTaxesOnShipping
        }
    }"""
    response = api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]
    charge_taxes_on_shipping = site_settings.charge_taxes_on_shipping
    assert data["chargeTaxesOnShipping"] == charge_taxes_on_shipping


def test_query_digital_content_settings(
    staff_api_client, site_settings, permission_manage_settings
):
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

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )
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
    site_settings.default_mail_sender_name = "Mirumee Labs Info"
    site_settings.default_mail_sender_address = "hello@example.com"
    site_settings.save(
        update_fields=["default_mail_sender_name", "default_mail_sender_address"]
    )

    query = QUERY_RETRIEVE_DEFAULT_MAIL_SENDER_SETTINGS

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)

    data = content["data"]["shop"]
    assert data["defaultMailSenderName"] == "Mirumee Labs Info"
    assert data["defaultMailSenderAddress"] == "hello@example.com"


def test_query_default_mail_sender_settings_not_set(
    staff_api_client, site_settings, permission_manage_settings, settings
):
    site_settings.default_mail_sender_name = ""
    site_settings.default_mail_sender_address = None
    site_settings.save(
        update_fields=["default_mail_sender_name", "default_mail_sender_address"]
    )

    settings.DEFAULT_FROM_EMAIL = "default@example.com"

    query = QUERY_RETRIEVE_DEFAULT_MAIL_SENDER_SETTINGS

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)

    data = content["data"]["shop"]
    assert data["defaultMailSenderName"] == ""
    assert data["defaultMailSenderAddress"] is None


def test_shop_digital_content_settings_mutation(
    staff_api_client, site_settings, permission_manage_settings
):
    query = """
        mutation updateSettings($input: ShopSettingsInput!) {
            shopSettingsUpdate(input: $input) {
                shop {
                    automaticFulfillmentDigitalProducts
                    defaultDigitalMaxDownloads
                    defaultDigitalUrlValidDays
                }
                errors {
                    field,
                    message
                }
            }
        }
    """

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
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)

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
    query = """
        mutation updateSettings($input: ShopSettingsInput!) {
            shopSettingsUpdate(input: $input) {
                shop {
                    headerText,
                    includeTaxesInPrices,
                    chargeTaxesOnShipping
                }
                errors {
                    field,
                    message
                }
            }
        }
    """
    charge_taxes_on_shipping = site_settings.charge_taxes_on_shipping
    new_charge_taxes_on_shipping = not charge_taxes_on_shipping
    variables = {
        "input": {
            "includeTaxesInPrices": False,
            "headerText": "Lorem ipsum",
            "chargeTaxesOnShipping": new_charge_taxes_on_shipping,
        }
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]["shop"]
    assert data["includeTaxesInPrices"] is False
    assert data["headerText"] == "Lorem ipsum"
    assert data["chargeTaxesOnShipping"] == new_charge_taxes_on_shipping
    site_settings.refresh_from_db()
    assert not site_settings.include_taxes_in_prices
    assert site_settings.charge_taxes_on_shipping == new_charge_taxes_on_shipping


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
    query = MUTATION_UPDATE_DEFAULT_MAIL_SENDER_SETTINGS

    variables = {
        "input": {
            "defaultMailSenderName": "Dummy Name",
            "defaultMailSenderAddress": "dummy@example.com",
        }
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
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
    query = MUTATION_UPDATE_DEFAULT_MAIL_SENDER_SETTINGS

    variables = {"input": {"defaultMailSenderName": sender_name}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
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
    query = MUTATION_UPDATE_DEFAULT_MAIL_SENDER_SETTINGS

    variables = {"input": {"defaultMailSenderAddress": sender_email}}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)

    errors = content["data"]["shopSettingsUpdate"]["errors"]
    assert errors == [
        {"field": "defaultMailSenderAddress", "message": "Enter a valid email address."}
    ]


def test_shop_domain_update(staff_api_client, permission_manage_settings):
    query = """
        mutation updateSettings($input: SiteDomainInput!) {
            shopDomainUpdate(input: $input) {
                shop {
                    name
                    domain {
                        host,
                    }
                }
            }
        }
    """
    new_name = "saleor test store"
    variables = {"input": {"domain": "lorem-ipsum.com", "name": new_name}}
    site = Site.objects.get_current()
    assert site.domain != "lorem-ipsum.com"
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    data = content["data"]["shopDomainUpdate"]["shop"]
    assert data["domain"]["host"] == "lorem-ipsum.com"
    assert data["name"] == new_name
    site.refresh_from_db()
    assert site.domain == "lorem-ipsum.com"
    assert site.name == new_name


MUTATION_CUSTOMER_SET_PASSWORD_URL_UPDATE = """
    mutation updateSettings($customerSetPasswordUrl: String!) {
        shopSettingsUpdate(input: {customerSetPasswordUrl: $customerSetPasswordUrl}){
            shop {
                customerSetPasswordUrl
            }
            shopErrors {
                message
                field
                code
            }
        }
    }
"""


def test_shop_customer_set_password_url_update(
    staff_api_client, site_settings, permission_manage_settings
):
    customer_set_password_url = "http://www.example.com/set_pass/"
    variables = {"customerSetPasswordUrl": customer_set_password_url}
    assert site_settings.customer_set_password_url != customer_set_password_url
    response = staff_api_client.post_graphql(
        MUTATION_CUSTOMER_SET_PASSWORD_URL_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]
    assert not data["shopErrors"]
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
    variables = {"customerSetPasswordUrl": customer_set_password_url}
    assert not site_settings.customer_set_password_url
    response = staff_api_client.post_graphql(
        MUTATION_CUSTOMER_SET_PASSWORD_URL_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)
    data = content["data"]["shopSettingsUpdate"]
    assert data["shopErrors"][0] == {
        "field": "customerSetPasswordUrl",
        "code": ShopErrorCode.INVALID.name,
        "message": ANY,
    }
    site_settings.refresh_from_db()
    assert not site_settings.customer_set_password_url


def test_homepage_collection_update(
    staff_api_client, collection, permission_manage_settings
):
    query = """
        mutation homepageCollectionUpdate($collection: ID!) {
            homepageCollectionUpdate(collection: $collection) {
                shop {
                    homepageCollection {
                        id,
                        name
                    }
                }
            }
        }
    """
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    variables = {"collection": collection_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    data = content["data"]["homepageCollectionUpdate"]["shop"]
    assert data["homepageCollection"]["id"] == collection_id
    assert data["homepageCollection"]["name"] == collection.name
    site = Site.objects.get_current()
    assert site.settings.homepage_collection == collection


def test_homepage_collection_update_set_null(
    staff_api_client, collection, site_settings, permission_manage_settings
):
    query = """
        mutation homepageCollectionUpdate($collection: ID) {
            homepageCollectionUpdate(collection: $collection) {
                shop {
                    homepageCollection {
                        id
                    }
                }
            }
        }
    """
    site_settings.homepage_collection = collection
    site_settings.save()
    variables = {"collection": None}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    data = content["data"]["homepageCollectionUpdate"]["shop"]
    assert data["homepageCollection"] is None
    site_settings.refresh_from_db()
    assert site_settings.homepage_collection is None


def test_query_default_country(user_api_client, settings):
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
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["defaultCountry"]
    assert data["code"] == settings.DEFAULT_COUNTRY
    assert data["country"] == "United States of America"


def test_query_geolocalization(user_api_client):
    query = """
        query {
            shop {
                geolocalization {
                    country {
                        code
                    }
                }
            }
        }
    """
    GERMAN_IP = "79.222.222.22"
    response = user_api_client.post_graphql(query, HTTP_X_FORWARDED_FOR=GERMAN_IP)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["geolocalization"]
    assert data["country"]["code"] == "DE"

    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["geolocalization"]
    assert data["country"] is None


def test_query_available_payment_gateways(user_api_client):
    query = """
        query {
            shop {
                availablePaymentGateways {
                    id
                    name
                }
            }
        }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["shop"]["availablePaymentGateways"]
    assert data[0]["id"] == "mirumee.payments.dummy"
    assert data[0]["name"] == "Dummy"


AUTHORIZATION_KEY_ADD = """
mutation AddKey($key: String!, $password: String!, $keyType: AuthorizationKeyType!) {
    authorizationKeyAdd(input: {key: $key, password: $password}, keyType: $keyType) {
        errors {
            field
            message
        }
        authorizationKey {
            name
            key
        }
    }
}
"""


def test_mutation_authorization_key_add_existing(
    staff_api_client, authorization_key, permission_manage_settings
):

    # adding a key of type that already exists should return an error
    assert authorization_key.name == AuthenticationBackends.FACEBOOK
    variables = {"keyType": "FACEBOOK", "key": "key", "password": "secret"}
    response = staff_api_client.post_graphql(
        AUTHORIZATION_KEY_ADD, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    assert content["data"]["authorizationKeyAdd"]["errors"][0]["field"] == "keyType"


def test_mutation_authorization_key_add(staff_api_client, permission_manage_settings):

    # mutation with correct input data should create a new key instance
    variables = {"keyType": "FACEBOOK", "key": "key", "password": "secret"}
    response = staff_api_client.post_graphql(
        AUTHORIZATION_KEY_ADD, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    assert content["data"]["authorizationKeyAdd"]["authorizationKey"]["key"] == "key"


def test_mutation_authorization_key_delete(
    staff_api_client, authorization_key, permission_manage_settings
):

    query = """
    mutation DeleteKey($keyType: AuthorizationKeyType!) {
        authorizationKeyDelete(keyType: $keyType) {
            errors {
                field
                message
            }
            authorizationKey {
                name
                key
            }
        }
    }
    """

    assert authorization_key.name == AuthenticationBackends.FACEBOOK

    # deleting non-existing key should return an error
    variables = {"keyType": "FACEBOOK"}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_settings]
    )
    content = get_graphql_content(response)
    assert content["data"]["authorizationKeyDelete"]["authorizationKey"]


MUTATION_SHOP_ADDRESS_UPDATE = """
    mutation updateShopAddress($input: AddressInput){
        shopAddressUpdate(input: $input){
            errors{
                field
                message
            }
        }
    }
"""


def test_mutation_update_company_address(
    staff_api_client,
    authorization_key,
    permission_manage_settings,
    address,
    site_settings,
):
    variables = {
        "input": {
            "streetAddress1": address.street_address_1,
            "city": address.city,
            "country": address.country.code,
            "postalCode": address.postal_code,
        }
    }

    response = staff_api_client.post_graphql(
        MUTATION_SHOP_ADDRESS_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)
    assert "errors" not in content["data"]

    site_settings.refresh_from_db()
    assert site_settings.company_address
    assert site_settings.company_address.street_address_1 == address.street_address_1
    assert site_settings.company_address.city == address.city
    assert site_settings.company_address.country.code == address.country.code


def test_mutation_update_company_address_remove_address(
    staff_api_client, permission_manage_settings, site_settings, address
):
    site_settings.company_address = address
    site_settings.save(update_fields=["company_address"])
    variables = {"input": None}

    response = staff_api_client.post_graphql(
        MUTATION_SHOP_ADDRESS_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)
    assert "errors" not in content["data"]

    site_settings.refresh_from_db()
    assert not site_settings.company_address
    assert not Address.objects.filter(pk=address.pk).exists()


def test_mutation_update_company_address_remove_address_without_address(
    staff_api_client, permission_manage_settings, site_settings
):
    variables = {"input": None}

    response = staff_api_client.post_graphql(
        MUTATION_SHOP_ADDRESS_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)
    assert "errors" not in content["data"]

    site_settings.refresh_from_db()
    assert not site_settings.company_address


def test_staff_notification_query(
    staff_api_client,
    staff_user,
    permission_manage_settings,
    staff_notification_recipient,
):
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

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_settings]
    )
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


MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE = """
    mutation StaffNotificationRecipient ($input: StaffNotificationRecipientInput!) {
        staffNotificationRecipientCreate(input: $input) {
            staffNotificationRecipient {
                active
                email
                user {
                    id
                    firstName
                    lastName
                    email
                }
            }
            shopErrors {
                field
                message
                code
            }
        }
    }
"""


def test_staff_notification_create_mutation(
    staff_api_client, staff_user, permission_manage_settings
):
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"input": {"user": user_id}}
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": {
            "active": True,
            "email": staff_user.email,
            "user": {
                "id": user_id,
                "firstName": staff_user.first_name,
                "lastName": staff_user.last_name,
                "email": staff_user.email,
            },
        },
        "shopErrors": [],
    }


def test_staff_notification_create_mutation_with_staffs_email(
    staff_api_client, staff_user, permission_manage_settings
):
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"input": {"email": staff_user.email}}
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": {
            "active": True,
            "email": staff_user.email,
            "user": {
                "id": user_id,
                "firstName": staff_user.first_name,
                "lastName": staff_user.last_name,
                "email": staff_user.email,
            },
        },
        "shopErrors": [],
    }


def test_staff_notification_create_mutation_with_customer_user(
    staff_api_client, customer_user, permission_manage_settings
):
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"input": {"user": user_id}}
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": None,
        "shopErrors": [
            {"code": "INVALID", "field": "user", "message": "User has to be staff user"}
        ],
    }


def test_staff_notification_create_mutation_with_email(
    staff_api_client, permission_manage_settings, permission_manage_staff
):
    staff_email = "test_email@example.com"
    variables = {"input": {"email": staff_email}}
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings, permission_manage_staff],
    )
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": {
            "active": True,
            "email": staff_email,
            "user": None,
        },
        "shopErrors": [],
    }


def test_staff_notification_create_mutation_with_empty_email(
    staff_api_client, permission_manage_settings
):
    staff_email = ""
    variables = {"input": {"email": staff_email}}
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_CREATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)

    assert content["data"]["staffNotificationRecipientCreate"] == {
        "staffNotificationRecipient": None,
        "shopErrors": [
            {
                "code": "INVALID",
                "field": "staffNotification",
                "message": "User and email cannot be set empty",
            }
        ],
    }


MUTATION_STAFF_NOTIFICATION_RECIPIENT_UPDATE = """
    mutation StaffNotificationRecipient (
        $id: ID!,
        $input: StaffNotificationRecipientInput!
    ) {
        staffNotificationRecipientUpdate(id: $id, input: $input) {
            staffNotificationRecipient {
                active
                email
                user {
                    firstName
                    lastName
                    email
                }
            }
            shopErrors {
                field
                message
                code
            }
        }
    }
"""


def test_staff_notification_update_mutation(
    staff_api_client,
    staff_user,
    permission_manage_settings,
    staff_notification_recipient,
):
    old_email = staff_notification_recipient.get_email()
    assert staff_notification_recipient.active
    staff_notification_recipient_id = graphene.Node.to_global_id(
        "StaffNotificationRecipient", staff_notification_recipient.id
    )
    variables = {"id": staff_notification_recipient_id, "input": {"active": False}}
    staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )
    staff_notification_recipient.refresh_from_db()
    assert not staff_notification_recipient.active
    assert staff_notification_recipient.get_email() == old_email


def test_staff_notification_update_mutation_with_empty_user(
    staff_api_client,
    staff_user,
    permission_manage_settings,
    staff_notification_recipient,
):
    staff_notification_recipient_id = graphene.Node.to_global_id(
        "StaffNotificationRecipient", staff_notification_recipient.id
    )
    variables = {"id": staff_notification_recipient_id, "input": {"user": ""}}
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)

    staff_notification_recipient.refresh_from_db()
    assert content["data"]["staffNotificationRecipientUpdate"] == {
        "staffNotificationRecipient": None,
        "shopErrors": [
            {
                "code": "INVALID",
                "field": "staffNotification",
                "message": "User and email cannot be set empty",
            }
        ],
    }


def test_staff_notification_update_mutation_with_empty_email(
    staff_api_client,
    staff_user,
    permission_manage_settings,
    staff_notification_recipient,
):
    staff_notification_recipient_id = graphene.Node.to_global_id(
        "StaffNotificationRecipient", staff_notification_recipient.id
    )
    variables = {"id": staff_notification_recipient_id, "input": {"email": ""}}
    response = staff_api_client.post_graphql(
        MUTATION_STAFF_NOTIFICATION_RECIPIENT_UPDATE,
        variables,
        permissions=[permission_manage_settings],
    )
    content = get_graphql_content(response)

    staff_notification_recipient.refresh_from_db()
    assert content["data"]["staffNotificationRecipientUpdate"] == {
        "staffNotificationRecipient": None,
        "shopErrors": [
            {
                "code": "INVALID",
                "field": "staffNotification",
                "message": "User and email cannot be set empty",
            }
        ],
    }
