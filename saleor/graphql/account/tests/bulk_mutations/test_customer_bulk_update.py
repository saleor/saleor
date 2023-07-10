from unittest.mock import patch

import graphene

from .....account import models
from .....account.error_codes import CustomerBulkUpdateErrorCode
from .....account.events import CustomerEvents
from .....account.search import generate_address_search_document_value
from .....giftcard.models import GiftCard
from .....giftcard.search import update_gift_cards_search_vector
from ....core.enums import ErrorPolicyEnum
from ....tests.utils import get_graphql_content
from ..utils import convert_dict_keys_to_camel_case

CUSTOMER_BULK_UPDATE_MUTATION = """
    mutation CustomerBulkUpdate(
        $customers: [CustomerBulkUpdateInput!]!,
        $errorPolicy: ErrorPolicyEnum
    ){
        customerBulkUpdate(customers: $customers, errorPolicy: $errorPolicy){
            results{
                errors {
                    path
                    message
                    code
                }
                customer{
                    id
                    firstName
                }
            }
            count
        }
    }
"""


def test_customers_bulk_update_using_ids(
    staff_api_client,
    customer_users,
    permission_manage_users,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_id = graphene.Node.to_global_id("User", customer_1.pk)
    customer_2_id = graphene.Node.to_global_id("User", customer_2.pk)

    customer_1_new_name = "NewName1"
    customer_2_new_name = "NewName2"

    customers_input = [
        {
            "id": customer_1_id,
            "input": {
                "firstName": customer_1_new_name,
            },
        },
        {
            "id": customer_2_id,
            "input": {
                "firstName": customer_2_new_name,
            },
        },
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    customer_1.refresh_from_db()
    customer_2.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert customer_1.first_name == customer_1_new_name
    assert customer_2.first_name == customer_2_new_name


@patch("saleor.plugins.manager.PluginsManager.customer_updated")
def test_stocks_bulk_update_send_stock_updated_event(
    customer_updated_webhook,
    staff_api_client,
    customer_users,
    permission_manage_users,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_id = graphene.Node.to_global_id("User", customer_1.pk)
    customer_2_id = graphene.Node.to_global_id("User", customer_2.pk)

    customer_1_new_name = "NewName1"
    customer_2_new_name = "NewName2"

    customers_input = [
        {
            "id": customer_1_id,
            "input": {
                "firstName": customer_1_new_name,
            },
        },
        {
            "id": customer_2_id,
            "input": {
                "firstName": customer_2_new_name,
            },
        },
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert customer_updated_webhook.call_count == 2


def test_customers_bulk_update_generate_events_when_deactivating(
    staff_api_client,
    staff_user,
    customer_users,
    permission_manage_users,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_id = graphene.Node.to_global_id("User", customer_1.pk)
    customer_2_id = graphene.Node.to_global_id("User", customer_2.pk)

    customers_input = [
        {
            "id": customer_1_id,
            "input": {
                "isActive": False,
            },
        },
        {
            "id": customer_2_id,
            "input": {
                "isActive": False,
            },
        },
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    account_deactivated_events = models.CustomerEvent.objects.all()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2

    assert len(account_deactivated_events) == 2
    for event in account_deactivated_events:
        assert event.type == CustomerEvents.ACCOUNT_DEACTIVATED
        assert event.user.pk == staff_user.pk


def test_customers_bulk_update_generate_events_when_name_change(
    staff_api_client,
    staff_user,
    customer_users,
    permission_manage_users,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_id = graphene.Node.to_global_id("User", customer_1.pk)
    customer_2_id = graphene.Node.to_global_id("User", customer_2.pk)

    customer_1_new_name = "NewName1"
    customer_2_new_name = "NewName2"

    customers_input = [
        {
            "id": customer_1_id,
            "input": {
                "firstName": customer_1_new_name,
            },
        },
        {
            "id": customer_2_id,
            "input": {
                "firstName": customer_2_new_name,
            },
        },
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    name_changed_events = models.CustomerEvent.objects.all()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2

    assert len(name_changed_events) == 2
    for event in name_changed_events:
        assert event.type == CustomerEvents.NAME_ASSIGNED
        assert event.user.pk == staff_user.pk


def test_customers_bulk_update_generate_events_when_email_change(
    staff_api_client,
    staff_user,
    gift_card,
    order,
    customer_user,
    permission_manage_users,
):
    # give

    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    customer_new_email = "newemail1@example.com"

    gift_card.created_by = None
    gift_card.created_by_email = customer_new_email
    gift_card.save(update_fields=["created_by", "created_by_email"])

    order.user = None
    order.user_email = customer_new_email
    order.save(update_fields=["user_email", "user"])

    customers_input = [
        {
            "id": customer_id,
            "input": {
                "email": customer_new_email,
            },
        }
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    gift_card.refresh_from_db()
    order.refresh_from_db()
    customer_user.refresh_from_db()
    email_changed_event = models.CustomerEvent.objects.get()
    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert email_changed_event.type == CustomerEvents.EMAIL_ASSIGNED
    assert email_changed_event.user.pk == staff_user.pk
    assert gift_card.created_by == customer_user
    assert gift_card.created_by_email == customer_user.email
    assert order.user == customer_user


def test_customers_bulk_update_using_external_refs(
    staff_api_client,
    customer_users,
    permission_manage_users,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_new_name = "NewName1"
    customer_2_new_name = "NewName2"

    customers_input = [
        {
            "externalReference": customer_1.external_reference,
            "input": {
                "firstName": customer_1_new_name,
            },
        },
        {
            "externalReference": customer_2.external_reference,
            "input": {
                "firstName": customer_2_new_name,
            },
        },
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    customer_1.refresh_from_db()
    customer_2.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert customer_1.first_name == customer_1_new_name
    assert customer_2.first_name == customer_2_new_name


def test_customers_bulk_update_when_no_id_or_external_ref_provided(
    staff_api_client,
    permission_manage_users,
):
    # given
    customers_input = [
        {
            "input": {
                "firstName": "NewName",
            }
        }
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["message"] == (
        "At least one of arguments is required: 'id', " "'externalReference'."
    )


def test_customers_bulk_update_when_invalid_id_provided(
    staff_api_client,
    permission_manage_users,
):
    # given
    customers_input = [
        {
            "id": "WrongID",
            "input": {
                "firstName": "NewName",
            },
        }
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["message"] == "Invalid customer ID."


def test_customers_bulk_update_when_customer_not_exists(
    staff_api_client,
    permission_manage_users,
):
    # given
    customers_input = [
        {
            "externalReference": "WrongRef",
            "input": {
                "firstName": "NewName",
            },
        }
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    error = data["results"][0]["errors"][0]
    assert error["code"] == CustomerBulkUpdateErrorCode.NOT_FOUND.name
    assert error["message"] == "Customer was not found."


def test_customers_bulk_update_correct_fields_validation(
    staff_api_client,
    customer_user,
    permission_manage_users,
):
    # given
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    new_name = 50 * "NewName1"
    new_last_name = 30 * "NewLastName2"

    customers_input = [
        {"id": customer_id, "input": {"firstName": new_name, "lastName": new_last_name}}
    ]
    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    errors = data["results"][0]["errors"]
    assert errors
    assert errors[0]["code"] == CustomerBulkUpdateErrorCode.MAX_LENGTH.name
    assert errors[0]["path"] == "input.firstName"
    assert errors[1]["code"] == CustomerBulkUpdateErrorCode.MAX_LENGTH.name
    assert errors[1]["path"] == "input.lastName"
    assert data["count"] == 0


def test_customers_bulk_update_with_address(
    staff_api_client,
    customer_user,
    address,
    permission_manage_users,
):
    # given
    shipping_address, billing_address = (
        customer_user.default_shipping_address,
        customer_user.default_billing_address,
    )

    assert shipping_address
    assert billing_address

    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    address_data = convert_dict_keys_to_camel_case(address.as_data())
    address_data.pop("metadata")
    address_data.pop("privateMetadata")

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address

    customers_input = [
        {
            "id": customer_id,
            "input": {
                "defaultBillingAddress": address_data,
                "defaultShippingAddress": address_data,
            },
        }
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then

    shipping_address.refresh_from_db()
    billing_address.refresh_from_db()
    customer_user.refresh_from_db()

    assert not data["results"][0]["errors"]
    assert data["count"] == 1
    assert billing_address.street_address_1 == new_street_address
    assert shipping_address.street_address_1 == new_street_address
    assert (
        generate_address_search_document_value(billing_address)
        in customer_user.search_document
    )
    assert (
        generate_address_search_document_value(shipping_address)
        in customer_user.search_document
    )


def test_customers_bulk_update_with_address_when_no_default(
    staff_api_client,
    customer_user,
    address,
    permission_manage_users,
):
    # given
    shipping_address = customer_user.default_shipping_address

    customer_user.default_shipping_address = None
    customer_user.save(update_fields=["default_shipping_address"])

    assert shipping_address

    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    address_data = convert_dict_keys_to_camel_case(shipping_address.as_data())
    address_data.pop("metadata")
    address_data.pop("privateMetadata")

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address

    customers_input = [
        {
            "id": customer_id,
            "input": {
                "defaultShippingAddress": address_data,
            },
        }
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    customer_user.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert data["count"] == 1

    assert customer_user.default_shipping_address
    assert customer_user.default_shipping_address in customer_user.addresses.all()


def test_customers_bulk_update_with_invalid_address(
    staff_api_client,
    customer_user,
    address,
    permission_manage_users,
):
    # given
    shipping_address, billing_address = (
        customer_user.default_shipping_address,
        customer_user.default_billing_address,
    )

    assert shipping_address
    assert billing_address

    customer_id = graphene.Node.to_global_id("User", customer_user.pk)

    address_data = convert_dict_keys_to_camel_case(address.as_data())
    address_data.pop("metadata")
    address_data.pop("privateMetadata")
    address_data.pop("country")

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address

    customers_input = [
        {
            "id": customer_id,
            "input": {
                "defaultBillingAddress": address_data,
            },
        }
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    assert data["results"][0]["errors"]
    assert data["count"] == 0
    error = data["results"][0]["errors"][0]
    assert error["code"] == CustomerBulkUpdateErrorCode.REQUIRED.name
    assert error["path"] == "input.defaultBillingAddress.country"


def test_customers_bulk_update_with_duplicated_external_ref(
    staff_api_client,
    customer_users,
    permission_manage_users,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_id = graphene.Node.to_global_id("User", customer_1.pk)
    customer_2_id = graphene.Node.to_global_id("User", customer_2.pk)

    external_ref = "sameRef"

    customers_input = [
        {"id": customer_1_id, "input": {"externalReference": external_ref}},
        {"id": customer_2_id, "input": {"externalReference": external_ref}},
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    assert data["count"] == 0
    assert data["results"][0]["errors"]
    assert data["results"][1]["errors"]
    assert (
        data["results"][0]["errors"][0]["code"]
        == CustomerBulkUpdateErrorCode.DUPLICATED_INPUT_ITEM.name
    )
    assert (
        data["results"][1]["errors"][0]["code"]
        == CustomerBulkUpdateErrorCode.DUPLICATED_INPUT_ITEM.name
    )


@patch("saleor.plugins.manager.PluginsManager.customer_metadata_updated")
def test_customers_bulk_update_metadata(
    mocked_customer_metadata_updated,
    staff_api_client,
    customer_users,
    permission_manage_users,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_id = graphene.Node.to_global_id("User", customer_1.pk)
    customer_2_id = graphene.Node.to_global_id("User", customer_2.pk)

    metadata_1 = {"key": "test key 1", "value": "test value 1"}
    private_metadata_1 = {"key": "private test key 1", "value": "private test value 1"}
    metadata_2 = {"key": "test key 2", "value": "test value 2"}
    private_metadata_2 = {"key": "private test key 2", "value": "private test value 2"}

    customers_input = [
        {
            "id": customer_1_id,
            "input": {
                "metadata": [metadata_1],
                "privateMetadata": [private_metadata_1],
            },
        },
        {
            "id": customer_2_id,
            "input": {
                "metadata": [metadata_2],
                "privateMetadata": [private_metadata_2],
            },
        },
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    customer_1.refresh_from_db()
    customer_2.refresh_from_db()
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    assert customer_1.metadata.get(metadata_1["key"]) == metadata_1["value"]
    assert customer_2.metadata.get(metadata_2["key"]) == metadata_2["value"]
    assert (
        customer_1.private_metadata.get(private_metadata_1["key"])
        == private_metadata_1["value"]
    )
    assert (
        customer_2.private_metadata.get(private_metadata_2["key"])
        == private_metadata_2["value"]
    )
    assert mocked_customer_metadata_updated.call_count == 2


@patch("saleor.plugins.manager.PluginsManager.customer_metadata_updated")
def test_customers_bulk_update_metadata_empty_key_in_one_input(
    mocked_customer_metadata_updated,
    staff_api_client,
    customer_users,
    permission_manage_users,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_id = graphene.Node.to_global_id("User", customer_1.pk)
    customer_2_id = graphene.Node.to_global_id("User", customer_2.pk)

    metadata_1 = {"key": "", "value": "test value 1"}
    private_metadata_1 = {"key": "", "value": "private test value 1"}
    metadata_2 = {"key": "test key 2", "value": "test value 2"}
    private_metadata_2 = {"key": "private test key 2", "value": "private test value 2"}

    customers_input = [
        {
            "id": customer_1_id,
            "input": {
                "metadata": [metadata_1],
                "privateMetadata": [private_metadata_1],
            },
        },
        {
            "id": customer_2_id,
            "input": {
                "metadata": [metadata_2],
                "privateMetadata": [private_metadata_2],
            },
        },
    ]

    variables = {
        "customers": customers_input,
        "errorPolicy": ErrorPolicyEnum.REJECT_FAILED_ROWS.name,
    }

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]

    # then
    customer_1.refresh_from_db()
    customer_2.refresh_from_db()
    customer_1_errors = data["results"][0]["errors"]
    assert len(customer_1_errors) == 2
    assert {error["code"] for error in customer_1_errors} == {
        CustomerBulkUpdateErrorCode.REQUIRED.name
    }
    assert {error["path"] for error in customer_1_errors} == {
        "input.metadata",
        "input.privateMetadata",
    }

    assert not data["results"][1]["errors"]
    assert data["count"] == 1
    assert metadata_1["key"] not in customer_1.metadata
    assert customer_2.metadata.get(metadata_2["key"]) == metadata_2["value"]
    assert private_metadata_1["key"] not in customer_1.private_metadata
    assert (
        customer_2.private_metadata.get(private_metadata_2["key"])
        == private_metadata_2["value"]
    )
    mocked_customer_metadata_updated.called_once_with(customer_2)


def test_customers_bulk_update_trigger_gift_card_search_vector_update(
    staff_api_client,
    customer_users,
    permission_manage_users,
    gift_card_list,
):
    # given
    customer_1 = customer_users[0]
    customer_2 = customer_users[1]

    customer_1_id = graphene.Node.to_global_id("User", customer_1.pk)
    customer_2_id = graphene.Node.to_global_id("User", customer_2.pk)

    customer_1_new_name = "NewName1"
    customer_2_new_name = "NewName2"

    gift_card_1, gift_card_2, gift_card_3 = gift_card_list
    gift_card_1.created_by = customer_1
    gift_card_2.used_by = customer_2
    gift_card_3.used_by_email = customer_1.email
    GiftCard.objects.bulk_update(
        gift_card_list, ["created_by", "used_by", "used_by_email"]
    )

    update_gift_cards_search_vector(gift_card_list)
    for card in gift_card_list:
        card.refresh_from_db()
        assert card.search_index_dirty is False

    customers_input = [
        {
            "id": customer_1_id,
            "input": {
                "firstName": customer_1_new_name,
            },
        },
        {
            "id": customer_2_id,
            "input": {
                "firstName": customer_2_new_name,
            },
        },
    ]

    variables = {"customers": customers_input}

    # when
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(CUSTOMER_BULK_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerBulkUpdate"]
    assert not data["results"][0]["errors"]
    assert not data["results"][1]["errors"]
    assert data["count"] == 2
    for card in gift_card_list:
        card.refresh_from_db()
        assert card.search_index_dirty is True
