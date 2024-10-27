from unittest.mock import patch

import graphene

from ......account import events as account_events
from ......account.error_codes import AccountErrorCode
from ......account.search import generate_address_search_document_value
from ......giftcard.models import GiftCard
from ......giftcard.search import update_gift_cards_search_vector
from .....tests.utils import get_graphql_content
from ....tests.utils import convert_dict_keys_to_camel_case

CUSTOMER_UPDATE_MUTATION = """
    mutation UpdateCustomer(
            $id: ID!
            $externalReference: String
            $input: CustomerInput!
        ) {
        customerUpdate(
            id: $id,
            externalReference: $externalReference,
            input: $input
        ) {
            errors {
                field
                message
            }
            user {
                id
                firstName
                lastName
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
                isActive
                note
                externalReference
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


@patch("saleor.plugins.manager.PluginsManager.customer_metadata_updated")
def test_customer_update(
    mocked_customer_metadata_updated,
    staff_api_client,
    staff_user,
    customer_user,
    address,
    permission_manage_users,
):
    # given
    query = CUSTOMER_UPDATE_MUTATION

    # this test requires addresses to be set and checks whether new address
    # instances weren't created, but the existing ones got updated
    assert customer_user.default_billing_address
    assert customer_user.default_shipping_address
    billing_address_pk = customer_user.default_billing_address.pk
    shipping_address_pk = customer_user.default_shipping_address.pk

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    first_name = "new_first_name"
    last_name = "new_last_name"
    note = "Test update note"
    external_reference = "test-ext-ref"
    address_data = convert_dict_keys_to_camel_case(address.as_data())
    metadata = [{"key": "test key", "value": "test value"}]
    private_metadata = [{"key": "private test key", "value": "private test value"}]
    address_data["metadata"] = metadata
    stored_metadata = {"test key": "test value"}
    address_data.pop("privateMetadata")
    address_data.pop("validationSkipped")

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address

    variables = {
        "id": user_id,
        "input": {
            "externalReference": external_reference,
            "firstName": first_name,
            "lastName": last_name,
            "isActive": False,
            "note": note,
            "defaultBillingAddress": address_data,
            "defaultShippingAddress": address_data,
            "languageCode": "PL",
            "metadata": metadata,
            "privateMetadata": private_metadata,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)

    data = content["data"]["customerUpdate"]
    assert data["errors"] == []
    assert data["user"]["firstName"] == first_name
    assert data["user"]["lastName"] == last_name
    assert data["user"]["note"] == note
    assert data["user"]["languageCode"] == "PL"
    assert data["user"]["externalReference"] == external_reference
    assert not data["user"]["isActive"]
    assert metadata[0] in data["user"]["metadata"]
    assert private_metadata[0] in data["user"]["privateMetadata"]
    assert data["user"]["defaultShippingAddress"]["metadata"] == metadata
    assert data["user"]["defaultBillingAddress"]["metadata"] == metadata

    customer_user.refresh_from_db()

    # check that existing instances are updated
    shipping_address, billing_address = (
        customer_user.default_shipping_address,
        customer_user.default_billing_address,
    )
    assert billing_address.pk == billing_address_pk
    assert shipping_address.pk == shipping_address_pk

    assert billing_address.metadata == stored_metadata
    assert billing_address.metadata == stored_metadata

    assert billing_address.street_address_1 == new_street_address
    assert shipping_address.street_address_1 == new_street_address
    (
        name_changed_event,
        deactivated_event,
    ) = account_events.CustomerEvent.objects.order_by("pk")

    assert name_changed_event.type == account_events.CustomerEvents.NAME_ASSIGNED
    assert name_changed_event.user.pk == staff_user.pk
    assert name_changed_event.parameters == {"message": customer_user.get_full_name()}

    assert deactivated_event.type == account_events.CustomerEvents.ACCOUNT_DEACTIVATED
    assert deactivated_event.user.pk == staff_user.pk
    assert deactivated_event.parameters == {"account_id": customer_user.id}

    customer_user.refresh_from_db()
    assert (
        generate_address_search_document_value(billing_address)
        in customer_user.search_document
    )
    assert (
        generate_address_search_document_value(shipping_address)
        in customer_user.search_document
    )
    mocked_customer_metadata_updated.assert_called_once_with(customer_user)


UPDATE_CUSTOMER_BY_EXTERNAL_REFERENCE = """
    mutation UpdateCustomer(
        $id: ID, $externalReference: String, $input: CustomerInput!
    ) {
        customerUpdate(id: $id, externalReference: $externalReference, input: $input) {
            errors {
                field
                message
                code
            }
            user {
                id
                externalReference
                firstName
            }
        }
    }
    """


def test_customer_update_by_external_reference(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    query = UPDATE_CUSTOMER_BY_EXTERNAL_REFERENCE
    user = customer_user
    new_name = "updated name"
    ext_ref = "test-ext-ref"
    user.external_reference = ext_ref
    user.save(update_fields=["external_reference"])

    variables = {
        "externalReference": ext_ref,
        "input": {"firstName": new_name},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    user.refresh_from_db()
    data = content["data"]["customerUpdate"]
    assert not data["errors"]
    assert data["user"]["firstName"] == new_name == user.first_name
    assert data["user"]["id"] == graphene.Node.to_global_id("User", user.id)
    assert data["user"]["externalReference"] == ext_ref


def test_update_customer_by_both_id_and_external_reference(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    query = UPDATE_CUSTOMER_BY_EXTERNAL_REFERENCE
    variables = {"input": {}, "externalReference": "whatever", "id": "whatever"}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["customerUpdate"]
    assert not data["user"]
    assert (
        data["errors"][0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_update_customer_by_external_reference_not_existing(
    staff_api_client, customer_user, permission_manage_users
):
    # given
    query = UPDATE_CUSTOMER_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {
        "input": {},
        "externalReference": ext_ref,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["customerUpdate"]
    assert not data["user"]
    assert data["errors"][0]["message"] == f"Couldn't resolve to a node: {ext_ref}"
    assert data["errors"][0]["field"] == "externalReference"


def test_update_customer_with_non_unique_external_reference(
    staff_api_client, permission_manage_users, user_list
):
    # given
    query = UPDATE_CUSTOMER_BY_EXTERNAL_REFERENCE

    ext_ref = "test-ext-ref"
    user_1 = user_list[0]
    user_1.external_reference = ext_ref
    user_1.save(update_fields=["external_reference"])
    user_2_id = graphene.Node.to_global_id("User", user_list[1].id)

    variables = {"input": {"externalReference": ext_ref}, "id": user_2_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["customerUpdate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == AccountErrorCode.UNIQUE.name
    assert error["message"] == "User with this External reference already exists."


UPDATE_CUSTOMER_EMAIL_MUTATION = """
    mutation UpdateCustomer(
            $id: ID!, $firstName: String, $lastName: String, $email: String) {
        customerUpdate(id: $id, input: {
            firstName: $firstName,
            lastName: $lastName,
            email: $email
        }) {
            errors {
                field
                message
            }
        }
    }
"""


def test_customer_update_generates_event_when_changing_email(
    staff_api_client, staff_user, customer_user, address, permission_manage_users
):
    query = UPDATE_CUSTOMER_EMAIL_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address

    variables = {
        "id": user_id,
        "firstName": customer_user.first_name,
        "lastName": customer_user.last_name,
        "email": "mirumee@example.com",
    }
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # The email was changed, an event should have been triggered
    email_changed_event = account_events.CustomerEvent.objects.get()
    assert email_changed_event.type == account_events.CustomerEvents.EMAIL_ASSIGNED
    assert email_changed_event.user.pk == staff_user.pk
    assert email_changed_event.parameters == {"message": "mirumee@example.com"}


UPDATE_CUSTOMER_IS_ACTIVE_MUTATION = """
    mutation UpdateCustomer(
        $id: ID!, $isActive: Boolean) {
            customerUpdate(id: $id, input: {
            isActive: $isActive,
        }) {
            errors {
                field
                message
            }
        }
    }
"""


def test_customer_update_generates_event_when_deactivating(
    staff_api_client, staff_user, customer_user, address, permission_manage_users
):
    query = UPDATE_CUSTOMER_IS_ACTIVE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)

    variables = {"id": user_id, "isActive": False}
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    account_deactivated_event = account_events.CustomerEvent.objects.get()
    assert (
        account_deactivated_event.type
        == account_events.CustomerEvents.ACCOUNT_DEACTIVATED
    )
    assert account_deactivated_event.user.pk == staff_user.pk
    assert account_deactivated_event.parameters == {"account_id": customer_user.id}


def test_customer_update_generates_event_when_activating(
    staff_api_client, staff_user, customer_user, address, permission_manage_users
):
    customer_user.is_active = False
    customer_user.save(update_fields=["is_active"])

    query = UPDATE_CUSTOMER_IS_ACTIVE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)

    variables = {"id": user_id, "isActive": True}
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    account_activated_event = account_events.CustomerEvent.objects.get()
    assert (
        account_activated_event.type == account_events.CustomerEvents.ACCOUNT_ACTIVATED
    )
    assert account_activated_event.user.pk == staff_user.pk
    assert account_activated_event.parameters == {"account_id": customer_user.id}


def test_customer_update_generates_event_when_deactivating_as_app(
    app_api_client, staff_user, customer_user, address, permission_manage_users
):
    query = UPDATE_CUSTOMER_IS_ACTIVE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)

    variables = {"id": user_id, "isActive": False}
    app_api_client.post_graphql(query, variables, permissions=[permission_manage_users])

    account_deactivated_event = account_events.CustomerEvent.objects.get()
    assert (
        account_deactivated_event.type
        == account_events.CustomerEvents.ACCOUNT_DEACTIVATED
    )
    assert account_deactivated_event.user is None
    assert account_deactivated_event.app.pk == app_api_client.app.pk
    assert account_deactivated_event.parameters == {"account_id": customer_user.id}


def test_customer_update_generates_event_when_activating_as_app(
    app_api_client, staff_user, customer_user, address, permission_manage_users
):
    customer_user.is_active = False
    customer_user.save(update_fields=["is_active"])

    query = UPDATE_CUSTOMER_IS_ACTIVE_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)

    variables = {"id": user_id, "isActive": True}
    app_api_client.post_graphql(query, variables, permissions=[permission_manage_users])

    account_activated_event = account_events.CustomerEvent.objects.get()
    assert (
        account_activated_event.type == account_events.CustomerEvents.ACCOUNT_ACTIVATED
    )
    assert account_activated_event.user is None
    assert account_activated_event.app.pk == app_api_client.app.pk
    assert account_activated_event.parameters == {"account_id": customer_user.id}


def test_customer_update_without_any_changes_generates_no_event(
    staff_api_client, customer_user, address, permission_manage_users
):
    query = UPDATE_CUSTOMER_EMAIL_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address

    variables = {
        "id": user_id,
        "firstName": customer_user.first_name,
        "lastName": customer_user.last_name,
        "email": customer_user.email,
    }
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # No event should have been generated
    assert not account_events.CustomerEvent.objects.exists()


def test_customer_update_generates_event_when_changing_email_by_app(
    app_api_client, staff_user, customer_user, address, permission_manage_users
):
    query = UPDATE_CUSTOMER_EMAIL_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address

    variables = {
        "id": user_id,
        "firstName": customer_user.first_name,
        "lastName": customer_user.last_name,
        "email": "mirumee@example.com",
    }
    app_api_client.post_graphql(query, variables, permissions=[permission_manage_users])

    # The email was changed, an event should have been triggered
    email_changed_event = account_events.CustomerEvent.objects.get()
    assert email_changed_event.type == account_events.CustomerEvents.EMAIL_ASSIGNED
    assert email_changed_event.user is None
    assert email_changed_event.parameters == {"message": "mirumee@example.com"}


def test_customer_update_assign_gift_cards_and_orders(
    staff_api_client,
    staff_user,
    customer_user,
    address,
    gift_card,
    order,
    permission_manage_users,
):
    # given
    query = UPDATE_CUSTOMER_EMAIL_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address
    new_email = "mirumee@example.com"

    gift_card.created_by = None
    gift_card.created_by_email = new_email
    gift_card.save(update_fields=["created_by", "created_by_email"])

    order.user = None
    order.user_email = new_email
    order.save(update_fields=["user_email", "user"])

    variables = {
        "id": user_id,
        "firstName": customer_user.first_name,
        "lastName": customer_user.last_name,
        "email": new_email,
    }

    # when
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # then
    email_changed_event = account_events.CustomerEvent.objects.get()
    assert email_changed_event.type == account_events.CustomerEvents.EMAIL_ASSIGNED
    gift_card.refresh_from_db()
    customer_user.refresh_from_db()
    assert gift_card.created_by == customer_user
    assert gift_card.created_by_email == customer_user.email
    order.refresh_from_db()
    assert order.user == customer_user


def test_customer_update_trigger_gift_card_search_vector_update(
    staff_api_client,
    customer_user,
    gift_card_list,
    permission_manage_users,
):
    # given
    query = UPDATE_CUSTOMER_EMAIL_MUTATION

    user_id = graphene.Node.to_global_id("User", customer_user.id)
    new_email = "mirumee@example.com"

    gift_card_1, gift_card_2, gift_card_3 = gift_card_list
    gift_card_1.created_by = customer_user
    gift_card_2.used_by = customer_user
    gift_card_3.used_by_email = new_email
    GiftCard.objects.bulk_update(
        gift_card_list, ["created_by", "used_by", "used_by_email"]
    )

    update_gift_cards_search_vector(gift_card_list)
    for card in gift_card_list:
        card.refresh_from_db()
        assert card.search_index_dirty is False

    variables = {
        "id": user_id,
        "email": new_email,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["customerUpdate"]["errors"]
    customer_user.refresh_from_db()
    assert customer_user.email == new_email
    for card in gift_card_list:
        card.refresh_from_db()
        assert card.search_index_dirty is True


UPDATE_CUSTOMER_IS_CONFIRMED_MUTATION = """
    mutation UpdateCustomer(
        $id: ID!, $isConfirmed: Boolean) {
            customerUpdate(id: $id, input: {
            isConfirmed: $isConfirmed,
        }) {
            errors {
                field
                message
            }
        }
    }
"""


def test_customer_confirm_assign_gift_cards_and_orders(
    staff_api_client,
    staff_user,
    customer_user,
    address,
    gift_card,
    order,
    permission_manage_users,
):
    # given
    query = UPDATE_CUSTOMER_IS_CONFIRMED_MUTATION

    customer_user.is_confirmed = False
    customer_user.save()

    user_id = graphene.Node.to_global_id("User", customer_user.id)

    gift_card.created_by = None
    gift_card.created_by_email = customer_user.email
    gift_card.save(update_fields=["created_by", "created_by_email"])

    order.user = None
    order.user_email = customer_user.email
    order.save(update_fields=["user_email", "user"])

    variables = {
        "id": user_id,
        "isConfirmed": True,
    }

    # when
    staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )

    # then
    gift_card.refresh_from_db()
    customer_user.refresh_from_db()
    assert gift_card.created_by == customer_user
    assert gift_card.created_by_email == customer_user.email

    order.refresh_from_db()
    assert order.user == customer_user
