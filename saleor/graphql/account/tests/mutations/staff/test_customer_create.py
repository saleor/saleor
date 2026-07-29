from unittest.mock import ANY, patch
from urllib.parse import urlencode

import graphene

from ......account import events as account_events
from ......account.error_codes import AccountErrorCode
from ......account.models import Address, User
from ......account.notifications import get_default_user_payload
from ......attribute.models import AssignedUserAttributeValue
from ......core.notify import NotifyEventType
from ......core.tests.utils import get_site_context_payload
from ......core.utils.url import prepare_url
from ......tests import race_condition
from .....tests.utils import get_graphql_content
from ....tests.utils import convert_dict_keys_to_camel_case

CUSTOMER_CREATE_MUTATION = """
    mutation CreateCustomer(
        $email: String, $firstName: String, $lastName: String, $channel: String
        $note: String, $billing: AddressInput, $shipping: AddressInput,
        $redirect_url: String, $languageCode: LanguageCodeEnum,
        $externalReference: String, $metadata: [MetadataInput!],
        $privateMetadata: [MetadataInput!],
        $isActive: Boolean, $isConfirmed: Boolean
    ) {
        customerCreate(input: {
            email: $email,
            firstName: $firstName,
            lastName: $lastName,
            isActive: $isActive,
            isConfirmed: $isConfirmed,
            note: $note,
            defaultShippingAddress: $shipping,
            defaultBillingAddress: $billing,
            redirectUrl: $redirect_url,
            languageCode: $languageCode,
            channel: $channel,
            externalReference: $externalReference
            metadata: $metadata, privateMetadata: $privateMetadata
        }) {
            errors {
                field
                code
                message
            }
            user {
                id
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
                email
                firstName
                lastName
                isActive
                isStaff
                isConfirmed
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
@patch("saleor.account.notifications.password_reset_token_generator.make_token")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.plugins.manager.PluginsManager.account_set_password_requested")
def test_customer_create(
    mocked_account_set_password_requested,
    mocked_notify,
    mocked_generator,
    mocked_customer_metadata_updated,
    staff_api_client,
    address,
    permission_manage_users,
    channel_PLN,
    site_settings,
):
    # given
    mocked_generator.return_value = "token"
    email = "api_user@example.com"
    first_name = "api_first_name"
    last_name = "api_last_name"
    note = "Test user"
    address_data = convert_dict_keys_to_camel_case(address.as_data())
    metadata = [{"key": "test key", "value": "test value"}]
    stored_metadata = {"test key": "test value"}
    address_data["metadata"] = metadata
    address_data.pop("privateMetadata")
    address_data.pop("validationSkipped")

    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"
    private_metadata = [{"key": "private test key", "value": "private test value"}]
    variables = {
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "note": note,
        "shipping": address_data,
        "billing": address_data,
        "redirect_url": redirect_url,
        "languageCode": "PL",
        "channel": channel_PLN.slug,
        "externalReference": external_reference,
        "metadata": metadata,
        "privateMetadata": private_metadata,
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)

    new_customer = User.objects.get(email=email)

    shipping_address, billing_address = (
        new_customer.default_shipping_address,
        new_customer.default_billing_address,
    )
    assert shipping_address == billing_address
    assert billing_address.metadata == stored_metadata
    assert shipping_address.metadata == stored_metadata
    assert shipping_address.pk != billing_address.pk

    data = content["data"]["customerCreate"]
    assert data["errors"] == []
    assert data["user"]["email"] == email
    assert data["user"]["firstName"] == first_name
    assert data["user"]["lastName"] == last_name
    assert data["user"]["note"] == note
    assert data["user"]["languageCode"] == "PL"
    assert data["user"]["externalReference"] == external_reference
    assert not data["user"]["isStaff"]
    assert data["user"]["isConfirmed"] is False
    assert data["user"]["isActive"]
    assert data["user"]["metadata"] == metadata
    assert data["user"]["privateMetadata"] == private_metadata
    assert data["user"]["defaultShippingAddress"]["metadata"] == metadata
    assert data["user"]["defaultBillingAddress"]["metadata"] == metadata

    new_user = User.objects.get(email=email)
    assert new_user.search_vector
    params = urlencode({"email": new_user.email, "token": "token"})
    password_set_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(new_user),
        "token": "token",
        "password_set_url": password_set_url,
        "recipient_email": new_user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug

    mocked_customer_metadata_updated.assert_called_once_with(new_user)

    assert {shipping_address, billing_address} == set(new_user.addresses.all())
    customer_creation_event = account_events.CustomerEvent.objects.get()
    assert customer_creation_event.type == account_events.CustomerEvents.ACCOUNT_CREATED
    assert customer_creation_event.user == new_customer

    mocked_account_set_password_requested.assert_called_once_with(
        new_user, channel_PLN.slug, "token", password_set_url
    )


@patch("saleor.plugins.manager.PluginsManager.customer_metadata_updated")
@patch("saleor.account.notifications.password_reset_token_generator.make_token")
@patch("saleor.plugins.manager.PluginsManager.notify")
@patch("saleor.plugins.manager.PluginsManager.account_set_password_requested")
def test_customer_create_as_app(
    mocked_account_set_password_requested,
    mocked_notify,
    mocked_generator,
    mocked_customer_metadata_updated,
    app_api_client,
    address,
    permission_manage_users,
    channel_PLN,
    site_settings,
):
    # given
    mocked_generator.return_value = "token"
    email = "api_user@example.com"
    first_name = "api_first_name"
    last_name = "api_last_name"
    note = "Test user"
    address_data = convert_dict_keys_to_camel_case(address.as_data())
    metadata = [{"key": "test key", "value": "test value"}]
    stored_metadata = {"test key": "test value"}
    address_data["metadata"] = metadata
    address_data.pop("privateMetadata")
    address_data.pop("validationSkipped")

    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"
    private_metadata = [{"key": "private test key", "value": "private test value"}]
    is_active = True
    is_confirmed = True
    variables = {
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "note": note,
        "shipping": address_data,
        "billing": address_data,
        "redirect_url": redirect_url,
        "languageCode": "PL",
        "channel": channel_PLN.slug,
        "externalReference": external_reference,
        "metadata": metadata,
        "privateMetadata": private_metadata,
        "isActive": is_active,
        "isConfirmed": is_confirmed,
    }

    # when
    response = app_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)

    new_customer = User.objects.get(email=email)

    shipping_address, billing_address = (
        new_customer.default_shipping_address,
        new_customer.default_billing_address,
    )
    assert shipping_address == billing_address
    assert billing_address.metadata == stored_metadata
    assert shipping_address.metadata == stored_metadata
    assert shipping_address.pk != billing_address.pk

    data = content["data"]["customerCreate"]
    assert data["errors"] == []
    assert data["user"]["email"] == email
    assert data["user"]["firstName"] == first_name
    assert data["user"]["lastName"] == last_name
    assert data["user"]["note"] == note
    assert data["user"]["languageCode"] == "PL"
    assert data["user"]["externalReference"] == external_reference
    assert not data["user"]["isStaff"]
    assert data["user"]["isActive"] == is_active
    assert data["user"]["isConfirmed"] is False
    assert data["user"]["isActive"]
    assert data["user"]["metadata"] == metadata
    assert data["user"]["privateMetadata"] == private_metadata
    assert data["user"]["defaultShippingAddress"]["metadata"] == metadata
    assert data["user"]["defaultBillingAddress"]["metadata"] == metadata

    new_user = User.objects.get(email=email)
    assert new_user.search_vector
    params = urlencode({"email": new_user.email, "token": "token"})
    password_set_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(new_user),
        "token": "token",
        "password_set_url": password_set_url,
        "recipient_email": new_user.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug

    mocked_customer_metadata_updated.assert_called_once_with(new_user)

    assert {shipping_address, billing_address} == set(new_user.addresses.all())
    customer_creation_event = account_events.CustomerEvent.objects.get()
    assert customer_creation_event.type == account_events.CustomerEvents.ACCOUNT_CREATED
    assert customer_creation_event.user == new_customer

    mocked_account_set_password_requested.assert_called_once_with(
        new_user, channel_PLN.slug, "token", password_set_url
    )


@patch("saleor.account.notifications.password_reset_token_generator.make_token")
@patch("saleor.plugins.manager.PluginsManager.notify")
def test_customer_create_send_password_with_url(
    mocked_notify,
    mocked_generator,
    staff_api_client,
    permission_manage_users,
    channel_PLN,
    site_settings,
):
    mocked_generator.return_value = "token"
    email = "api_user@example.com"
    variables = {
        "email": email,
        "redirect_url": "https://www.example.com",
        "channel": channel_PLN.slug,
    }

    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert not data["errors"]

    new_customer = User.objects.get(email=email)
    assert new_customer
    redirect_url = "https://www.example.com"
    params = urlencode({"email": email, "token": "token"})
    password_set_url = prepare_url(params, redirect_url)
    expected_payload = {
        "user": get_default_user_payload(new_customer),
        "password_set_url": password_set_url,
        "token": "token",
        "recipient_email": new_customer.email,
        "channel_slug": channel_PLN.slug,
        **get_site_context_payload(site_settings.site),
    }

    assert mocked_notify.call_count == 1
    call_args = mocked_notify.call_args_list[0]
    called_args = call_args.args
    called_kwargs = call_args.kwargs
    assert called_args[0] == NotifyEventType.ACCOUNT_SET_CUSTOMER_PASSWORD
    assert len(called_kwargs) == 2
    assert called_kwargs["payload_func"]() == expected_payload
    assert called_kwargs["channel_slug"] == channel_PLN.slug


def test_customer_create_empty_metadata_key(
    staff_api_client,
    address,
    permission_manage_users,
    channel_PLN,
    site_settings,
):
    # then
    email = "api_user@example.com"
    first_name = "api_first_name"
    last_name = "api_last_name"
    note = "Test user"
    address_data = convert_dict_keys_to_camel_case(address.as_data())
    address_data.pop("metadata")
    address_data.pop("privateMetadata")
    address_data.pop("validationSkipped")

    redirect_url = "https://www.example.com"
    external_reference = "test-ext-ref"
    metadata = [{"key": "", "value": "test value"}]
    variables = {
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "note": note,
        "shipping": address_data,
        "billing": address_data,
        "redirect_url": redirect_url,
        "languageCode": "PL",
        "channel": channel_PLN.slug,
        "externalReference": external_reference,
        "metadata": metadata,
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["customerCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "metadata"
    assert errors[0]["code"] == AccountErrorCode.REQUIRED.name


def test_customer_create_without_send_password(
    staff_api_client, permission_manage_users
):
    email = "api_user@example.com"
    variables = {"email": email}
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert not data["errors"]
    User.objects.get(email=email)


def test_customer_create_with_invalid_url(staff_api_client, permission_manage_users):
    email = "api_user@example.com"
    variables = {"email": email, "redirect_url": "invalid"}
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert data["errors"][0] == {
        "field": "redirectUrl",
        "code": AccountErrorCode.INVALID.name,
        "message": ANY,
    }
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_customer_create_with_not_allowed_url(
    staff_api_client, permission_manage_users
):
    email = "api_user@example.com"
    variables = {"email": email, "redirect_url": "https://www.fake.com"}
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert data["errors"][0] == {
        "field": "redirectUrl",
        "code": AccountErrorCode.INVALID.name,
        "message": ANY,
    }
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_customer_create_with_upper_case_email(
    staff_api_client, permission_manage_users
):
    # given
    email = "UPPERCASE@example.com"
    variables = {"email": email}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["customerCreate"]
    assert not data["errors"]
    assert data["user"]["email"] == email.lower()


def test_customer_create_with_non_unique_external_reference(
    staff_api_client, permission_manage_users, customer_user
):
    # given
    ext_ref = "test-ext-ref"
    customer_user.external_reference = ext_ref
    customer_user.save(update_fields=["external_reference"])

    variables = {"email": "mail.test@exampale.com", "externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["customerCreate"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == AccountErrorCode.UNIQUE.name
    assert error["message"] == "User with this External reference already exists."


@patch("saleor.account.notifications.password_reset_token_generator.make_token")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_customer_create_webhook_event_triggered(
    mocked_trigger_webhooks_async,
    mocked_generator,
    settings,
    user_api_client,
    subscription_account_set_password_requested_webhook,
    staff_api_client,
    address,
    channel_PLN,
    permission_manage_users,
):
    # given
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mocked_generator.return_value = "token"
    email = "api_user@example.com"
    address_data = convert_dict_keys_to_camel_case(address.as_data())
    address_data.pop("privateMetadata")
    address_data.pop("validationSkipped")

    variables = {
        "email": email,
        "firstName": "api_first_name",
        "lastName": "api_last_name",
        "note": "Test user",
        "shipping": address_data,
        "billing": address_data,
        "redirect_url": "https://www.example.com",
        "languageCode": "PL",
        "channel": channel_PLN.slug,
        "externalReference": "test-ext-ref",
    }

    # when
    staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    User.objects.get(email=email)
    mocked_trigger_webhooks_async.assert_called()


def test_customer_create_race_condition(
    staff_api_client, site_settings, permission_manage_users, address
):
    """Context.

    This test checks case when two concurrent mutations fail,
    due to unique constraint on email field. In race-condition scenario it's possible
    that two calls will pass validation (user doesn't exist yet), but the second one
    will fail due to DB having a user created already.
    """

    # given
    site_settings.enable_account_confirmation_by_email = False
    site_settings.save(update_fields=["enable_account_confirmation_by_email"])

    email_to_create = "test-user@example.com"

    address_data = convert_dict_keys_to_camel_case(address.as_data())
    address_data.pop("privateMetadata")
    address_data.pop("validationSkipped")

    variables = {
        "shipping": address_data,
        "billing": address_data,
        "email": email_to_create,
        "firstName": "api_first_name",
        "lastName": "api_last_name",
    }

    def create_existing_customer(*args, **kwargs):
        User.objects.create(email=email_to_create)

    with race_condition.RunBefore(
        "saleor.graphql.account.mutations.staff.customer_create.CustomerCreate._save",
        create_existing_customer,
    ):
        response = staff_api_client.post_graphql(
            CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
        )

        content = get_graphql_content(response)

        errors_list = content["data"]["customerCreate"]["errors"]

        assert len(errors_list) == 1
        assert errors_list[0]["code"] == "UNIQUE"

        # make sure that addresses were not saved.
        assert not Address.objects.exclude(id=address.id).exists()


def test_create_assigns_default_customer_type(
    staff_api_client, permission_manage_users, default_customer_type
):
    # given
    email = "customer-type@example.com"
    variables = {"email": email}

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["customerCreate"]["errors"]
    new_user = User.objects.get(email=email)
    assert new_user.customer_type == default_customer_type


CUSTOMER_CREATE_WITH_ATTRIBUTES_MUTATION = """
    mutation CreateCustomer(
        $email: String, $customerType: ID, $attributes: [AttributeValueInput!]
    ) {
        customerCreate(input: {
            email: $email,
            customerType: $customerType,
            attributes: $attributes
        }) {
            errors {
                field
                code
                message
                attributes
            }
            user {
                id
                email
                customerType {
                    id
                }
            }
        }
    }
"""


def test_create_with_customer_type_and_attributes(
    staff_api_client,
    permission_manage_users,
    customer_type_with_attributes,
    loyalty_customer_attribute,
    description_customer_attribute,
    default_customer_type,
):
    # given
    email = "attributes@example.com"
    value = loyalty_customer_attribute.values.get(slug="gold")
    description_text = "A very important customer."
    variables = {
        "email": email,
        "customerType": graphene.Node.to_global_id(
            "CustomerType", customer_type_with_attributes.pk
        ),
        "attributes": [
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", loyalty_customer_attribute.pk
                ),
                "dropdown": {
                    "id": graphene.Node.to_global_id("AttributeValue", value.pk)
                },
            },
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", description_customer_attribute.pk
                ),
                "plainText": description_text,
            },
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_WITH_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert not data["errors"]
    new_user = User.objects.get(email=email)
    assert new_user.customer_type == customer_type_with_attributes
    assert data["user"]["customerType"]["id"] == graphene.Node.to_global_id(
        "CustomerType", customer_type_with_attributes.pk
    )
    assigned_values = AssignedUserAttributeValue.objects.filter(user=new_user)
    assert assigned_values.count() == 2
    assert (
        assigned_values.get(value__attribute=loyalty_customer_attribute).value == value
    )
    description_value = assigned_values.get(
        value__attribute=description_customer_attribute
    ).value
    assert description_value.plain_text == description_text


def test_create_with_attributes_of_default_customer_type(
    staff_api_client,
    permission_manage_users,
    default_customer_type,
    loyalty_customer_attribute,
):
    # given
    default_customer_type.customer_attributes.add(loyalty_customer_attribute)
    email = "default-type-attributes@example.com"
    value = loyalty_customer_attribute.values.get(slug="silver")
    variables = {
        "email": email,
        "attributes": [
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", loyalty_customer_attribute.pk
                ),
                "dropdown": {
                    "id": graphene.Node.to_global_id("AttributeValue", value.pk)
                },
            }
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_WITH_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert not data["errors"]
    new_user = User.objects.get(email=email)
    assert new_user.customer_type == default_customer_type
    assigned_values = AssignedUserAttributeValue.objects.filter(user=new_user)
    assert assigned_values.count() == 1
    assert assigned_values.first().value == value


def test_create_with_attribute_not_in_customer_type(
    staff_api_client,
    permission_manage_users,
    customer_type,
    loyalty_customer_attribute,
    default_customer_type,
):
    # given: the attribute is not assigned to the given customer type
    assert not customer_type.customer_attributes.filter(
        pk=loyalty_customer_attribute.pk
    ).exists()
    email = "wrong-attribute@example.com"
    attribute_id = graphene.Node.to_global_id(
        "Attribute", loyalty_customer_attribute.pk
    )
    variables = {
        "email": email,
        "customerType": graphene.Node.to_global_id("CustomerType", customer_type.pk),
        "attributes": [{"id": attribute_id, "dropdown": {"value": "gold"}}],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_WITH_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributes"
    assert error["code"] == AccountErrorCode.NOT_FOUND.name
    assert f"Could not resolve attributes: ID: {attribute_id}." == error["message"]
    assert not User.objects.filter(email=email).exists()


def test_create_with_missing_required_attribute(
    staff_api_client,
    permission_manage_users,
    customer_type_with_attributes,
    loyalty_customer_attribute,
    description_customer_attribute,
    segment_customer_attribute,
    default_customer_type,
):
    # given
    loyalty_customer_attribute.value_required = True
    loyalty_customer_attribute.save(update_fields=["value_required"])
    customer_type_with_attributes.customer_attributes.add(segment_customer_attribute)

    email = "missing-required@example.com"
    variables = {
        "email": email,
        "customerType": graphene.Node.to_global_id(
            "CustomerType", customer_type_with_attributes.pk
        ),
        "attributes": [
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", segment_customer_attribute.pk
                ),
                "dropdown": {"value": "Retail"},
            },
            {
                "id": graphene.Node.to_global_id(
                    "Attribute", description_customer_attribute.pk
                ),
                "plainText": "Provided, but the required attribute is not.",
            },
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_WITH_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "attributes"
    assert error["code"] == AccountErrorCode.REQUIRED.name
    assert error["attributes"] == [
        graphene.Node.to_global_id("Attribute", loyalty_customer_attribute.pk)
    ]
    assert not User.objects.filter(email=email).exists()


def test_create_with_invalid_customer_type_id(
    staff_api_client,
    permission_manage_users,
    default_customer_type,
):
    # given: an ID of a different type passed as customerType
    email = "invalid-type-id@example.com"
    variables = {
        "email": email,
        "customerType": graphene.Node.to_global_id("PageType", 1),
    }

    # when
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_WITH_ATTRIBUTES_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "customerType"
    assert error["code"] == AccountErrorCode.GRAPHQL_ERROR.name
    assert not User.objects.filter(email=email).exists()
