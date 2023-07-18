from unittest.mock import patch

from ......account.error_codes import AccountErrorCode
from ......account.models import User
from ......checkout import AddressType
from ......giftcard.search import update_gift_cards_search_vector
from .....tests.utils import assert_no_permission, get_graphql_content

ACCOUNT_UPDATE_QUERY = """
    mutation accountUpdate(
        $billing: AddressInput
        $shipping: AddressInput
        $firstName: String,
        $lastName: String
        $languageCode: LanguageCodeEnum
        $metadata: [MetadataInput!]
    ) {
        accountUpdate(
          input: {
            defaultBillingAddress: $billing,
            defaultShippingAddress: $shipping,
            firstName: $firstName,
            lastName: $lastName,
            languageCode: $languageCode,
            metadata: $metadata
        }) {
            errors {
                field
                code
                message
                addressType
            }
            user {
                firstName
                lastName
                email
                defaultBillingAddress {
                    id
                    metadata {
                        key
                        value
                    }
                }
                defaultShippingAddress {
                    id
                    metadata {
                        key
                        value
                    }
                }
                languageCode
                metadata {
                    key
                    value
                }
            }
        }
    }
"""


def test_logged_customer_updates_language_code(user_api_client):
    language_code = "PL"
    user = user_api_client.user
    assert user.language_code != language_code
    variables = {"languageCode": language_code}

    response = user_api_client.post_graphql(ACCOUNT_UPDATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountUpdate"]

    assert not data["errors"]
    assert data["user"]["languageCode"] == language_code
    user.refresh_from_db()
    assert user.language_code == language_code.lower()
    assert user.search_document


def test_logged_customer_update_names(user_api_client):
    first_name = "first"
    last_name = "last"
    user = user_api_client.user
    assert user.first_name != first_name
    assert user.last_name != last_name

    variables = {"firstName": first_name, "lastName": last_name}
    response = user_api_client.post_graphql(ACCOUNT_UPDATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountUpdate"]

    user.refresh_from_db()
    assert not data["errors"]
    assert user.first_name == first_name
    assert user.last_name == last_name


def test_logged_customer_update_addresses(user_api_client, graphql_address_data):
    # this test requires addresses to be set and checks whether new address
    # instances weren't created, but the existing ones got updated
    user = user_api_client.user
    new_first_name = graphql_address_data["firstName"]
    metadata = graphql_address_data["metadata"]
    assert user.default_billing_address
    assert user.default_shipping_address
    assert user.default_billing_address.first_name != new_first_name
    assert user.default_shipping_address.first_name != new_first_name

    query = ACCOUNT_UPDATE_QUERY
    mutation_name = "accountUpdate"
    variables = {"billing": graphql_address_data, "shipping": graphql_address_data}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]

    assert data["user"]["defaultShippingAddress"]["metadata"] == metadata
    assert data["user"]["defaultBillingAddress"]["metadata"] == metadata

    # check that existing instances are updated
    billing_address_pk = user.default_billing_address.pk
    shipping_address_pk = user.default_shipping_address.pk
    user = User.objects.get(email=user.email)
    assert user.default_billing_address.pk == billing_address_pk
    assert user.default_shipping_address.pk == shipping_address_pk

    assert user.default_billing_address.first_name == new_first_name
    assert user.default_shipping_address.first_name == new_first_name
    assert user.search_document

    assert user.default_billing_address.metadata == {"public": "public_value"}
    assert user.default_shipping_address.metadata == {"public": "public_value"}


def test_logged_customer_update_addresses_invalid_shipping_address(
    user_api_client, graphql_address_data
):
    shipping_address = graphql_address_data.copy()
    del shipping_address["country"]

    query = ACCOUNT_UPDATE_QUERY
    mutation_name = "accountUpdate"
    variables = {"billing": graphql_address_data, "shipping": shipping_address}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert len(data["errors"]) == 1
    errors = data["errors"]
    assert errors[0]["field"] == "country"
    assert errors[0]["code"] == AccountErrorCode.REQUIRED.name
    assert errors[0]["addressType"] == AddressType.SHIPPING.upper()


def test_logged_customer_update_addresses_invalid_billing_address(
    user_api_client, graphql_address_data
):
    billing_address = graphql_address_data.copy()
    del billing_address["country"]

    query = ACCOUNT_UPDATE_QUERY
    mutation_name = "accountUpdate"
    variables = {"billing": billing_address, "shipping": graphql_address_data}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert len(data["errors"]) == 1
    errors = data["errors"]
    assert errors[0]["field"] == "country"
    assert errors[0]["code"] == AccountErrorCode.REQUIRED.name
    assert errors[0]["addressType"] == AddressType.BILLING.upper()


def test_logged_customer_update_anonymous_user(api_client):
    query = ACCOUNT_UPDATE_QUERY
    response = api_client.post_graphql(query, {})
    assert_no_permission(response)


@patch("saleor.plugins.manager.PluginsManager.customer_metadata_updated")
def test_logged_customer_updates_metadata(
    mocked_customer_metadata_updated, user_api_client
):
    # given
    metadata = {"key": "test key", "value": "test value"}
    variables = {"metadata": [metadata]}

    # when
    response = user_api_client.post_graphql(ACCOUNT_UPDATE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["accountUpdate"]

    assert not data["errors"]
    assert metadata in data["user"]["metadata"]
    mocked_customer_metadata_updated.assert_called_once_with(user_api_client.user)


def test_logged_customer_update_names_trigger_gift_card_search_vector_update(
    user_api_client, gift_card, gift_card_used, gift_card_expiry_date
):
    # given
    first_name = "first"
    last_name = "last"
    gift_cards = [gift_card, gift_card_used, gift_card_expiry_date]

    update_gift_cards_search_vector(gift_cards)
    for card in gift_cards:
        card.refresh_from_db()
        assert card.search_index_dirty is False

    variables = {"firstName": first_name, "lastName": last_name}

    # when
    response = user_api_client.post_graphql(ACCOUNT_UPDATE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["accountUpdate"]
    assert not data["errors"]
    for card in gift_cards:
        card.refresh_from_db()
        assert card.search_index_dirty is True
