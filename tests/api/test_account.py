import json
import re
import uuid
from unittest.mock import ANY, MagicMock, Mock, patch

import graphene
import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.validators import URLValidator
from django.shortcuts import reverse
from freezegun import freeze_time
from prices import Money

from saleor.account import events as account_events
from saleor.account.error_codes import AccountErrorCode
from saleor.account.models import Address, User
from saleor.account.utils import get_random_avatar
from saleor.checkout import AddressType
from saleor.graphql.account.mutations.base import INVALID_TOKEN
from saleor.graphql.account.mutations.staff import (
    CustomerDelete,
    StaffDelete,
    StaffUpdate,
    UserDelete,
)
from saleor.graphql.core.enums import PermissionEnum
from saleor.graphql.core.utils import str_to_enum
from saleor.order.models import FulfillmentStatus, Order
from tests.api.utils import get_graphql_content
from tests.utils import create_image

from .utils import (
    assert_no_permission,
    convert_dict_keys_to_camel_case,
    get_multipart_request_body,
)


@pytest.fixture
def query_customer_with_filter():
    query = """
    query ($filter: CustomerFilterInput!, ) {
        customers(first: 5, filter: $filter) {
            totalCount
            edges {
                node {
                    id
                    lastName
                    firstName
                }
            }
        }
    }
    """
    return query


@pytest.fixture
def query_staff_users_with_filter():
    query = """
    query ($filter: StaffUserInput!, ) {
        staffUsers(first: 5, filter: $filter) {
            totalCount
            edges {
                node {
                    id
                    lastName
                    firstName
                }
            }
        }
    }
    """
    return query


def test_create_token_mutation(admin_client, staff_user):
    query = """
    mutation TokenCreate($email: String!, $password: String!) {
        tokenCreate(email: $email, password: $password) {
            token
            errors {
                field
                message
            }
        }
    }
    """
    variables = {"email": staff_user.email, "password": "password"}
    response = admin_client.post(
        reverse("api"),
        json.dumps({"query": query, "variables": variables}),
        content_type="application/json",
    )
    content = get_graphql_content(response)
    token_data = content["data"]["tokenCreate"]
    assert token_data["token"]
    assert token_data["errors"] == []

    incorrect_variables = {"email": staff_user.email, "password": "incorrect"}
    response = admin_client.post(
        reverse("api"),
        json.dumps({"query": query, "variables": incorrect_variables}),
        content_type="application/json",
    )
    content = get_graphql_content(response)
    token_data = content["data"]["tokenCreate"]
    errors = token_data["errors"]
    assert errors
    assert not errors[0]["field"]
    assert not token_data["token"]


def test_token_create_user_data(permission_manage_orders, staff_api_client, staff_user):
    query = """
    mutation TokenCreate($email: String!, $password: String!) {
        tokenCreate(email: $email, password: $password) {
            user {
                id
                email
                permissions {
                    code
                    name
                }
            }
        }
    }
    """

    permission = permission_manage_orders
    staff_user.user_permissions.add(permission)
    name = permission.name
    user_id = graphene.Node.to_global_id("User", staff_user.id)

    variables = {"email": staff_user.email, "password": "password"}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    token_data = content["data"]["tokenCreate"]
    assert token_data["user"]["id"] == user_id
    assert token_data["user"]["email"] == staff_user.email
    assert token_data["user"]["permissions"][0]["name"] == name
    assert token_data["user"]["permissions"][0]["code"] == "MANAGE_ORDERS"


def test_query_user(
    staff_api_client, customer_user, address, permission_manage_users, media_root
):
    user = customer_user
    user.default_shipping_address.country = "US"
    user.default_shipping_address.save()
    user.addresses.add(address.get_copy())

    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save()

    query = """
    query User($id: ID!) {
        user(id: $id) {
            email
            firstName
            lastName
            isStaff
            isActive
            addresses {
                id
                isDefaultShippingAddress
                isDefaultBillingAddress
            }
            orders {
                totalCount
            }
            dateJoined
            lastLogin
            defaultShippingAddress {
                firstName
                lastName
                companyName
                streetAddress1
                streetAddress2
                city
                cityArea
                postalCode
                countryArea
                phone
                country {
                    code
                }
                isDefaultShippingAddress
                isDefaultBillingAddress
            }
            defaultBillingAddress {
                firstName
                lastName
                companyName
                streetAddress1
                streetAddress2
                city
                cityArea
                postalCode
                countryArea
                phone
                country {
                    code
                }
                isDefaultShippingAddress
                isDefaultBillingAddress
            }
            avatar {
                url
            }
        }
    }
    """
    ID = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": ID}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert data["email"] == user.email
    assert data["firstName"] == user.first_name
    assert data["lastName"] == user.last_name
    assert data["isStaff"] == user.is_staff
    assert data["isActive"] == user.is_active
    assert data["orders"]["totalCount"] == user.orders.count()
    assert data["avatar"]["url"]

    assert len(data["addresses"]) == user.addresses.count()
    for address in data["addresses"]:
        if address["isDefaultShippingAddress"]:
            address_id = graphene.Node.to_global_id(
                "Address", user.default_shipping_address.id
            )
            assert address["id"] == address_id
        if address["isDefaultBillingAddress"]:
            address_id = graphene.Node.to_global_id(
                "Address", user.default_billing_address.id
            )
            assert address["id"] == address_id

    address = data["defaultShippingAddress"]
    user_address = user.default_shipping_address
    assert address["firstName"] == user_address.first_name
    assert address["lastName"] == user_address.last_name
    assert address["companyName"] == user_address.company_name
    assert address["streetAddress1"] == user_address.street_address_1
    assert address["streetAddress2"] == user_address.street_address_2
    assert address["city"] == user_address.city
    assert address["cityArea"] == user_address.city_area
    assert address["postalCode"] == user_address.postal_code
    assert address["country"]["code"] == user_address.country.code
    assert address["countryArea"] == user_address.country_area
    assert address["phone"] == user_address.phone.as_e164
    assert address["isDefaultShippingAddress"] is None
    assert address["isDefaultBillingAddress"] is None

    address = data["defaultBillingAddress"]
    user_address = user.default_billing_address
    assert address["firstName"] == user_address.first_name
    assert address["lastName"] == user_address.last_name
    assert address["companyName"] == user_address.company_name
    assert address["streetAddress1"] == user_address.street_address_1
    assert address["streetAddress2"] == user_address.street_address_2
    assert address["city"] == user_address.city
    assert address["cityArea"] == user_address.city_area
    assert address["postalCode"] == user_address.postal_code
    assert address["country"]["code"] == user_address.country.code
    assert address["countryArea"] == user_address.country_area
    assert address["phone"] == user_address.phone.as_e164
    assert address["isDefaultShippingAddress"] is None
    assert address["isDefaultBillingAddress"] is None


USER_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            email
        }
    }
"""


def test_customer_can_not_see_other_users_data(user_api_client, staff_user):
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id}
    response = user_api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)


def test_user_query_anonymous_user(api_client):
    variables = {"id": ""}
    response = api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)


def test_user_query_permission_manage_users_get_customer(
    staff_api_client, customer_user, permission_manage_users
):
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": customer_id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert customer_user.email == data["email"]


def test_user_query_permission_manage_users_get_staff(
    staff_api_client, staff_user, permission_manage_users
):
    staff_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {"id": staff_id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    assert not content["data"]["user"]


def test_user_query_permission_manage_staff_get_customer(
    staff_api_client, customer_user, permission_manage_staff
):
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": customer_id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    assert not content["data"]["user"]


def test_user_query_permission_manage_staff_get_staff(
    staff_api_client, staff_user, permission_manage_staff
):
    staff_id = graphene.Node.to_global_id("User", staff_user.pk)
    variables = {"id": staff_id}
    response = staff_api_client.post_graphql(
        USER_QUERY, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["user"]
    assert staff_user.email == data["email"]


def test_query_customers(staff_api_client, user_api_client, permission_manage_users):
    query = """
    query Users {
        customers(first: 20) {
            totalCount
            edges {
                node {
                    isStaff
                }
            }
        }
    }
    """
    variables = {}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]
    assert users
    assert all([not user["node"]["isStaff"] for user in users])

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_query_staff(
    staff_api_client, user_api_client, staff_user, admin_user, permission_manage_staff
):
    query = """
    {
        staffUsers(first: 20) {
            edges {
                node {
                    email
                    isStaff
                }
            }
        }
    }
    """
    variables = {}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUsers"]["edges"]
    assert len(data) == 2
    staff_emails = [user["node"]["email"] for user in data]
    assert sorted(staff_emails) == [admin_user.email, staff_user.email]
    assert all([user["node"]["isStaff"] for user in data])

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_who_can_see_user(
    staff_user, customer_user, staff_api_client, permission_manage_users
):
    query = """
    query Users {
        customers {
            totalCount
        }
    }
    """

    # Random person (even staff) can't see users data without permissions
    ID = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": ID}
    response = staff_api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)

    response = staff_api_client.post_graphql(query)
    assert_no_permission(response)

    # Add permission and ensure staff can see user(s)
    staff_user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(USER_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["user"]["email"] == customer_user.email

    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content["data"]["customers"]["totalCount"] == 1


ME_QUERY = """
    query Me {
        me {
            id
            email
            checkout {
                token
            }
        }
    }
"""


def test_me_query(user_api_client):
    response = user_api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert data["email"] == user_api_client.user.email


def test_me_query_anonymous_client(api_client):
    response = api_client.post_graphql(ME_QUERY)
    assert_no_permission(response)


def test_me_query_customer_can_not_see_note(
    staff_user, staff_api_client, permission_manage_users
):
    query = """
    query Me {
        me {
            id
            email
            note
        }
    }
    """
    # Random person (even staff) can't see own note without permissions
    response = staff_api_client.post_graphql(query)
    assert_no_permission(response)

    # Add permission and ensure staff can see own note
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert data["email"] == staff_api_client.user.email
    assert data["note"] == staff_api_client.user.note


def test_me_query_checkout(user_api_client, checkout):
    user = user_api_client.user
    checkout.user = user
    checkout.save()

    response = user_api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    data = content["data"]["me"]
    assert data["checkout"]["token"] == str(checkout.token)


def test_me_with_cancelled_fulfillments(
    user_api_client, fulfilled_order_with_cancelled_fulfillment
):
    query = """
    query Me {
        me {
            orders (first: 1) {
                edges {
                    node {
                        id
                        fulfillments {
                            status
                        }
                    }
                }
            }
        }
    }
    """
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_id = graphene.Node.to_global_id(
        "Order", fulfilled_order_with_cancelled_fulfillment.id
    )
    data = content["data"]["me"]
    order = data["orders"]["edges"][0]["node"]
    assert order["id"] == order_id
    fulfillments = order["fulfillments"]
    assert len(fulfillments) == 1
    assert fulfillments[0]["status"] == FulfillmentStatus.FULFILLED.upper()


def test_user_with_cancelled_fulfillments(
    staff_api_client,
    customer_user,
    permission_manage_users,
    fulfilled_order_with_cancelled_fulfillment,
):
    query = """
    query User($id: ID!) {
        user(id: $id) {
            orders (first: 1) {
                edges {
                    node {
                        id
                        fulfillments {
                            status
                        }
                    }
                }
            }
        }
    }
    """
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"id": user_id}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    order_id = graphene.Node.to_global_id(
        "Order", fulfilled_order_with_cancelled_fulfillment.id
    )
    data = content["data"]["user"]
    order = data["orders"]["edges"][0]["node"]
    assert order["id"] == order_id
    fulfillments = order["fulfillments"]
    assert len(fulfillments) == 2
    assert fulfillments[0]["status"] == FulfillmentStatus.FULFILLED.upper()
    assert fulfillments[1]["status"] == FulfillmentStatus.CANCELED.upper()


CUSTOMER_REGISTER_MUTATION = """
    mutation RegisterCustomer($password: String!, $email: String!) {
        customerRegister(input: {password: $password, email: $email}) {
            errors {
                field
                message
            }
            user {
                id
            }
        }
    }
"""


ACCOUNT_REGISTER_MUTATION = """
    mutation RegisterAccount($password: String!, $email: String!) {
        accountRegister(input: {password: $password, email: $email}) {
            errors {
                field
                message
            }
            user {
                id
            }
        }
    }
"""


@pytest.mark.parametrize(
    "query, mutation_name",
    [
        (CUSTOMER_REGISTER_MUTATION, "customerRegister"),
        (ACCOUNT_REGISTER_MUTATION, "accountRegister"),
    ],
)
def test_customer_register(user_api_client, query, mutation_name):
    email = "customer@example.com"
    variables = {"email": email, "password": "Password"}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]
    new_user = User.objects.get(email=email)

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert data["errors"]
    assert data["errors"][0]["field"] == "email"
    assert data["errors"][0]["message"] == ("User with this Email already exists.")

    customer_creation_event = account_events.CustomerEvent.objects.get()
    assert customer_creation_event.type == account_events.CustomerEvents.ACCOUNT_CREATED
    assert customer_creation_event.user == new_user


CUSTOMER_CREATE_MUTATION = """
    mutation CreateCustomer(
        $email: String, $firstName: String, $lastName: String,
        $note: String, $billing: AddressInput, $shipping: AddressInput,
        $send_mail: Boolean, $redirect_url: String) {
        customerCreate(input: {
            email: $email,
            firstName: $firstName,
            lastName: $lastName,
            note: $note,
            defaultShippingAddress: $shipping,
            defaultBillingAddress: $billing
            sendPasswordEmail: $send_mail
            redirectUrl: $redirect_url
        }) {
            errors {
                field
                message
            }
            user {
                id
                defaultBillingAddress {
                    id
                }
                defaultShippingAddress {
                    id
                }
                email
                firstName
                lastName
                isActive
                isStaff
                note
            }
        }
    }
"""


@patch("saleor.dashboard.emails._send_set_password_email")
def test_customer_create(
    _send_set_password_email_mock, staff_api_client, address, permission_manage_users
):
    email = "api_user@example.com"
    first_name = "api_first_name"
    last_name = "api_last_name"
    note = "Test user"
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    variables = {
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "note": note,
        "shipping": address_data,
        "billing": address_data,
        "send_mail": True,
        "redirect_url": "https://www.example.com",
    }

    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    new_customer = User.objects.get(email=email)

    shipping_address, billing_address = (
        new_customer.default_shipping_address,
        new_customer.default_billing_address,
    )
    assert shipping_address == address
    assert billing_address == address
    assert shipping_address.pk != billing_address.pk

    data = content["data"]["customerCreate"]
    assert data["errors"] == []
    assert data["user"]["email"] == email
    assert data["user"]["firstName"] == first_name
    assert data["user"]["lastName"] == last_name
    assert data["user"]["note"] == note
    assert not data["user"]["isStaff"]
    assert data["user"]["isActive"]

    _send_set_password_email_mock.assert_called_once_with(
        new_customer.email, ANY, "dashboard/customer/set_password"
    )

    customer_creation_event = account_events.CustomerEvent.objects.get()
    assert customer_creation_event.type == account_events.CustomerEvents.ACCOUNT_CREATED
    assert customer_creation_event.user == new_customer


@patch("saleor.dashboard.emails._send_set_user_password_email_with_url.delay")
def test_customer_create_send_password_with_url(
    _send_set_user_password_email_with_url_mock,
    staff_api_client,
    permission_manage_users,
):
    email = "api_user@example.com"
    variables = {
        "email": email,
        "send_mail": True,
        "redirect_url": "https://www.example.com",
    }

    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert not data["errors"]

    new_customer = User.objects.get(email=email)
    assert new_customer

    token = default_token_generator.make_token(new_customer)
    _send_set_user_password_email_with_url_mock.assert_called_once_with(
        new_customer.email, ANY, token, "dashboard/customer/set_password"
    )


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


def test_customer_create_without_redirect_url(
    staff_api_client, permission_manage_users
):
    email = "api_user@example.com"
    variables = {"email": email, "send_mail": True}
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert data["errors"][0]["field"] == "redirectUrl"
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_customer_create_with_invalid_url(staff_api_client, permission_manage_users):
    email = "api_user@example.com"
    variables = {"email": email, "send_mail": True, "redirect_url": "invalid"}
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert data["errors"][0]["field"] == "redirectUrl"
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_customer_create_with_not_allowed_url(
    staff_api_client, permission_manage_users
):
    email = "api_user@example.com"
    variables = {
        "email": email,
        "send_mail": True,
        "redirectUrl": "https://www.fake.com",
    }
    response = staff_api_client.post_graphql(
        CUSTOMER_CREATE_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerCreate"]
    assert data["errors"][0]["field"] == "redirectUrl"
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_customer_update(
    staff_api_client, staff_user, customer_user, address, permission_manage_users
):
    query = """
    mutation UpdateCustomer(
            $id: ID!, $firstName: String, $lastName: String,
            $isActive: Boolean, $note: String, $billing: AddressInput,
            $shipping: AddressInput) {
        customerUpdate(id: $id, input: {
            isActive: $isActive,
            firstName: $firstName,
            lastName: $lastName,
            note: $note,
            defaultBillingAddress: $billing
            defaultShippingAddress: $shipping
        }) {
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
                }
                defaultShippingAddress {
                    id
                }
                isActive
                note
            }
        }
    }
    """

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
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    new_street_address = "Updated street address"
    address_data["streetAddress1"] = new_street_address

    variables = {
        "id": user_id,
        "firstName": first_name,
        "lastName": last_name,
        "isActive": False,
        "note": note,
        "billing": address_data,
        "shipping": address_data,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    customer = User.objects.get(email=customer_user.email)

    # check that existing instances are updated
    shipping_address, billing_address = (
        customer.default_shipping_address,
        customer.default_billing_address,
    )
    assert billing_address.pk == billing_address_pk
    assert shipping_address.pk == shipping_address_pk

    assert billing_address.street_address_1 == new_street_address
    assert shipping_address.street_address_1 == new_street_address

    data = content["data"]["customerUpdate"]
    assert data["errors"] == []
    assert data["user"]["firstName"] == first_name
    assert data["user"]["lastName"] == last_name
    assert data["user"]["note"] == note
    assert not data["user"]["isActive"]

    # The name was changed, an event should have been triggered
    name_changed_event = account_events.CustomerEvent.objects.get()
    assert name_changed_event.type == account_events.CustomerEvents.NAME_ASSIGNED
    assert name_changed_event.user.pk == staff_user.pk
    assert name_changed_event.parameters == {"message": customer.get_full_name()}


def test_customer_update_generates_event_when_changing_email(
    staff_api_client, staff_user, customer_user, address, permission_manage_users
):
    query = """
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


def test_customer_update_without_any_changes_generates_no_event(
    staff_api_client, customer_user, address, permission_manage_users
):
    query = """
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


ACCOUNT_UPDATE_QUERY = """
    mutation accountUpdate(
            $billing: AddressInput, $shipping: AddressInput, $firstName: String,
            $lastName: String) {
        accountUpdate(
          input: {
            defaultBillingAddress: $billing,
            defaultShippingAddress: $shipping,
            firstName: $firstName,
            lastName: $lastName,
        }) {
            errors {
                field
                message
            }
            user {
                firstName
                lastName
                email
                defaultBillingAddress {
                    id
                }
                defaultShippingAddress {
                    id
                }
            }
        }
    }
"""


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


UPDATE_LOGGED_CUSTOMER_QUERY = """
    mutation UpdateLoggedCustomer($billing: AddressInput,
                                  $shipping: AddressInput) {
        loggedUserUpdate(
          input: {
            defaultBillingAddress: $billing,
            defaultShippingAddress: $shipping,
        }) {
            errors {
                field
                message
            }
            user {
                email
                defaultBillingAddress {
                    id
                }
                defaultShippingAddress {
                    id
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "query, mutation_name",
    [
        (UPDATE_LOGGED_CUSTOMER_QUERY, "loggedUserUpdate"),
        (ACCOUNT_UPDATE_QUERY, "accountUpdate"),
    ],
)
def test_logged_customer_update_addresses(
    user_api_client, graphql_address_data, query, mutation_name
):
    # this test requires addresses to be set and checks whether new address
    # instances weren't created, but the existing ones got updated
    user = user_api_client.user
    new_first_name = graphql_address_data["firstName"]
    assert user.default_billing_address
    assert user.default_shipping_address
    assert user.default_billing_address.first_name != new_first_name
    assert user.default_shipping_address.first_name != new_first_name
    variables = {"billing": graphql_address_data, "shipping": graphql_address_data}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]

    # check that existing instances are updated
    billing_address_pk = user.default_billing_address.pk
    shipping_address_pk = user.default_shipping_address.pk
    user = User.objects.get(email=user.email)
    assert user.default_billing_address.pk == billing_address_pk
    assert user.default_shipping_address.pk == shipping_address_pk

    assert user.default_billing_address.first_name == new_first_name
    assert user.default_shipping_address.first_name == new_first_name


@pytest.mark.parametrize(
    "query", [(UPDATE_LOGGED_CUSTOMER_QUERY), (ACCOUNT_UPDATE_QUERY)]
)
def test_logged_customer_update_anonymous_user(api_client, query):
    response = api_client.post_graphql(query, {})
    assert_no_permission(response)


ACCOUNT_REQUEST_DELETION_MUTATION = """
    mutation accountRequestDeletion($redirectUrl: String!) {
        accountRequestDeletion(redirectUrl: $redirectUrl) {
            errors {
                field
                message
            }
        }
    }
"""


@patch("saleor.account.emails._send_delete_confirmation_email")
def test_account_request_deletion(send_delete_confirmation_email_mock, user_api_client):
    user = user_api_client.user
    variables = {"redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]
    send_delete_confirmation_email_mock.assert_called_once_with(user.email, ANY)
    url = send_delete_confirmation_email_mock.mock_calls[0][1][1]
    url_validator = URLValidator()
    url_validator(url)


@patch("saleor.account.emails._send_account_delete_confirmation_email_with_url.delay")
def test_account_request_deletion_token_validation(
    send_account_delete_confirmation_email_with_url_mock, user_api_client
):
    user = user_api_client.user
    token = default_token_generator.make_token(user)
    variables = {"redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]
    send_account_delete_confirmation_email_with_url_mock.assert_called_once_with(
        user.email, ANY, token
    )
    url = send_account_delete_confirmation_email_with_url_mock.mock_calls[0][1][1]
    url_validator = URLValidator()
    url_validator(url)


@patch("saleor.account.emails._send_account_delete_confirmation_email_with_url.delay")
def test_account_request_deletion_anonymous_user(
    send_account_delete_confirmation_email_with_url_mock, api_client
):
    variables = {"redirectUrl": "https://www.example.com"}
    response = api_client.post_graphql(ACCOUNT_REQUEST_DELETION_MUTATION, variables)
    assert_no_permission(response)
    send_account_delete_confirmation_email_with_url_mock.assert_not_called()


@patch("saleor.account.emails._send_account_delete_confirmation_email_with_url.delay")
def test_account_request_deletion_storefront_hosts_not_allowed(
    send_account_delete_confirmation_email_with_url_mock, user_api_client
):
    variables = {"redirectUrl": "https://www.fake.com"}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "redirectUrl"
    send_account_delete_confirmation_email_with_url_mock.assert_not_called()


@patch("saleor.account.emails._send_account_delete_confirmation_email_with_url.delay")
def test_account_request_deletion_all_storefront_hosts_allowed(
    send_account_delete_confirmation_email_with_url_mock, user_api_client, settings
):
    user = user_api_client.user
    token = default_token_generator.make_token(user)
    settings.ALLOWED_CLIENT_HOSTS = ["*"]
    variables = {"redirectUrl": "https://www.test.com"}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]
    send_account_delete_confirmation_email_with_url_mock.assert_called_once_with(
        user.email, ANY, token
    )
    url = send_account_delete_confirmation_email_with_url_mock.mock_calls[0][1][1]
    url_validator = URLValidator()
    url_validator(url)


@patch("saleor.account.emails._send_account_delete_confirmation_email_with_url.delay")
def test_account_request_deletion_subdomain(
    send_account_delete_confirmation_email_with_url_mock, user_api_client, settings
):
    user = user_api_client.user
    token = default_token_generator.make_token(user)
    settings.ALLOWED_CLIENT_HOSTS = [".example.com"]
    variables = {"redirectUrl": "https://sub.example.com"}
    response = user_api_client.post_graphql(
        ACCOUNT_REQUEST_DELETION_MUTATION, variables
    )
    content = get_graphql_content(response)
    data = content["data"]["accountRequestDeletion"]
    assert not data["errors"]
    send_account_delete_confirmation_email_with_url_mock.assert_called_once_with(
        user.email, ANY, token
    )
    url = send_account_delete_confirmation_email_with_url_mock.mock_calls[0][1][1]
    url_validator = URLValidator()
    url_validator(url)


ACCOUNT_DELETE_MUTATION = """
    mutation AccountDelete($token: String!){
        accountDelete(token: $token){
            errors{
                field
                message
            }
        }
    }
"""


def test_account_delete(user_api_client):
    user = user_api_client.user
    token = default_token_generator.make_token(user)
    variables = {"token": token}

    response = user_api_client.post_graphql(ACCOUNT_DELETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountDelete"]
    assert not data["errors"]
    assert not User.objects.filter(pk=user.id).exists()


def test_account_delete_invalid_token(user_api_client):
    user = user_api_client.user
    variables = {"token": "invalid"}

    response = user_api_client.post_graphql(ACCOUNT_DELETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountDelete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Invalid or expired token."
    assert User.objects.filter(pk=user.id).exists()


def test_account_delete_anonymous_user(api_client):
    variables = {"token": "invalid"}

    response = api_client.post_graphql(ACCOUNT_DELETE_MUTATION, variables)
    assert_no_permission(response)


def test_account_delete_staff_user(staff_api_client):
    user = staff_api_client.user
    variables = {"token": "invalid"}

    response = staff_api_client.post_graphql(ACCOUNT_DELETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountDelete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Cannot delete a staff account."
    assert User.objects.filter(pk=user.id).exists()


def test_account_delete_other_customer_token(user_api_client):
    user = user_api_client.user
    other_user = User.objects.create(email="temp@example.com")
    token = default_token_generator.make_token(other_user)
    variables = {"token": token}

    response = user_api_client.post_graphql(ACCOUNT_DELETE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountDelete"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Invalid or expired token."
    assert User.objects.filter(pk=user.id).exists()
    assert User.objects.filter(pk=other_user.id).exists()


@patch(
    "saleor.graphql.account.utils.account_events.staff_user_deleted_a_customer_event"
)
def test_customer_delete(
    mocked_deletion_event,
    staff_api_client,
    staff_user,
    customer_user,
    permission_manage_users,
):
    """Ensure deleting a customer actually deletes the customer and creates proper
    related events"""

    query = """
    mutation CustomerDelete($id: ID!) {
        customerDelete(id: $id){
            errors {
                field
                message
            }
            user {
                id
            }
        }
    }
    """
    customer_id = graphene.Node.to_global_id("User", customer_user.pk)
    variables = {"id": customer_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["customerDelete"]
    assert data["errors"] == []
    assert data["user"]["id"] == customer_id

    # Ensure the customer was properly deleted
    # and any related event was properly triggered
    mocked_deletion_event.assert_called_once_with(
        staff_user=staff_user, deleted_count=1
    )


def test_customer_delete_errors(customer_user, admin_user, staff_user):
    info = Mock(context=Mock(user=admin_user))
    with pytest.raises(ValidationError) as e:
        CustomerDelete.clean_instance(info, staff_user)

    msg = "Cannot delete a staff account."
    assert e.value.error_dict["id"][0].message == msg

    # should not raise any errors
    CustomerDelete.clean_instance(info, customer_user)


STAFF_CREATE_MUTATION = """
    mutation CreateStaff(
            $email: String, $permissions: [PermissionEnum],
            $send_mail: Boolean, $redirect_url: String) {
        staffCreate(input: {email: $email, permissions: $permissions,
                sendPasswordEmail: $send_mail, redirectUrl: $redirect_url}) {
            errors {
                field
                message
            }
            accountErrors {
                field
                message
                code
            }
            user {
                id
                email
                isStaff
                isActive
                permissions {
                    code
                }
                avatar {
                    url
                }
            }
        }
    }
"""


@patch("saleor.dashboard.emails._send_set_password_email")
def test_staff_create(
    _send_set_password_email_mock, staff_api_client, media_root, permission_manage_staff
):
    email = "api_user@example.com"
    variables = {
        "email": email,
        "permissions": [PermissionEnum.MANAGE_PRODUCTS.name],
        "send_mail": True,
        "redirect_url": "https://www.example.com",
    }

    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert data["errors"] == []
    assert data["user"]["email"] == email
    assert data["user"]["isStaff"]
    assert data["user"]["isActive"]
    assert re.match(
        r"http://testserver/media/user-avatars/avatar\d+.*",
        data["user"]["avatar"]["url"],
    )
    permissions = data["user"]["permissions"]
    assert permissions[0]["code"] == "MANAGE_PRODUCTS"

    staff_user = User.objects.get(email=email)

    assert staff_user.is_staff

    _send_set_password_email_mock.assert_called_once_with(
        staff_user.email, ANY, "dashboard/staff/set_password"
    )


@patch("saleor.dashboard.emails._send_set_user_password_email_with_url.delay")
def test_staff_create_send_password_with_url(
    _send_set_user_password_email_with_url_mock,
    staff_api_client,
    media_root,
    permission_manage_staff,
):
    email = "api_user@example.com"
    variables = {
        "email": email,
        "send_mail": True,
        "redirect_url": "https://www.example.com",
    }

    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert not data["errors"]

    staff_user = User.objects.get(email=email)
    assert staff_user.is_staff

    token = default_token_generator.make_token(staff_user)
    _send_set_user_password_email_with_url_mock.assert_called_once_with(
        staff_user.email, ANY, token, "dashboard/staff/set_password"
    )


def test_staff_create_without_send_password(
    staff_api_client, media_root, permission_manage_staff
):
    email = "api_user@example.com"
    variables = {"email": email}
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert not data["errors"]
    User.objects.get(email=email)


def test_staff_create_without_redirect_url(
    staff_api_client, media_root, permission_manage_staff
):
    email = "api_user@example.com"
    variables = {"email": email, "send_mail": True}
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert data["errors"][0]["field"] == "redirectUrl"
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_staff_create_with_invalid_url(
    staff_api_client, media_root, permission_manage_staff
):
    email = "api_user@example.com"
    variables = {"email": email, "send_mail": True, "redirect_url": "invalid"}
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert data["errors"][0]["field"] == "redirectUrl"
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_staff_create_with_not_allowed_url(
    staff_api_client, media_root, permission_manage_staff
):
    email = "api_user@example.com"
    variables = {
        "email": email,
        "send_mail": True,
        "redirectUrl": "https://www.fake.com",
    }
    response = staff_api_client.post_graphql(
        STAFF_CREATE_MUTATION, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffCreate"]
    assert data["errors"][0]["field"] == "redirectUrl"
    staff_user = User.objects.filter(email=email)
    assert not staff_user


def test_staff_update(staff_api_client, permission_manage_staff, media_root):
    query = """
    mutation UpdateStaff(
            $id: ID!, $permissions: [PermissionEnum], $is_active: Boolean) {
        staffUpdate(
                id: $id,
                input: {permissions: $permissions, isActive: $is_active}) {
            errors {
                field
                message
            }
            user {
                permissions {
                    code
                }
                isActive
            }
        }
    }
    """
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id, "permissions": [], "is_active": False}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []
    assert data["user"]["permissions"] == []
    assert not data["user"]["isActive"]


@patch("saleor.graphql.account.mutations.staff.get_random_avatar")
def test_staff_update_doesnt_change_existing_avatar(
    mock_get_random_avatar, staff_api_client, permission_manage_staff, media_root
):
    query = """
    mutation UpdateStaff(
            $id: ID!, $permissions: [PermissionEnum], $is_active: Boolean) {
        staffUpdate(
                id: $id,
                input: {permissions: $permissions, isActive: $is_active}) {
            errors {
                field
                message
            }
            accountErrors {
                field
                message
                code
            }
        }
    }
    """

    mock_file = MagicMock(spec=File)
    mock_file.name = "image.jpg"
    mock_get_random_avatar.return_value = mock_file

    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)

    # Create random avatar
    staff_user.avatar = get_random_avatar()
    staff_user.save()
    original_path = staff_user.avatar.path

    id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": id, "permissions": [], "is_active": False}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffUpdate"]
    assert data["errors"] == []

    # Make sure that random avatar isn't recreated when there is one already set.
    mock_get_random_avatar.assert_not_called()
    staff_user.refresh_from_db()
    assert staff_user.avatar.path == original_path


def test_staff_delete(staff_api_client, permission_manage_staff):
    query = """
        mutation DeleteStaff($id: ID!) {
            staffDelete(id: $id) {
                errors {
                    field
                    message
                }
                user {
                    id
                }
            }
        }
    """
    staff_user = User.objects.create(email="staffuser@example.com", is_staff=True)
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    variables = {"id": user_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    data = content["data"]["staffDelete"]
    assert data["errors"] == []
    assert not User.objects.filter(pk=staff_user.id).exists()


def test_user_delete_errors(staff_user, admin_user):
    info = Mock(context=Mock(user=staff_user))
    with pytest.raises(ValidationError) as e:
        UserDelete.clean_instance(info, staff_user)

    msg = "You cannot delete your own account."
    assert e.value.error_dict["id"][0].message == msg

    info = Mock(context=Mock(user=staff_user))
    with pytest.raises(ValidationError) as e:
        UserDelete.clean_instance(info, admin_user)

    msg = "Cannot delete this account."
    assert e.value.error_dict["id"][0].message == msg


def test_staff_delete_errors(staff_user, customer_user, admin_user):
    info = Mock(context=Mock(user=staff_user))
    with pytest.raises(ValidationError) as e:
        StaffDelete.clean_instance(info, customer_user)
    msg = "Cannot delete a non-staff user."
    assert e.value.error_dict["id"][0].message == msg

    # should not raise any errors
    info = Mock(context=Mock(user=admin_user))
    StaffDelete.clean_instance(info, staff_user)


def test_staff_update_errors(staff_user, customer_user, admin_user):
    StaffUpdate.clean_is_active(None, customer_user, staff_user)

    with pytest.raises(ValidationError) as e:
        StaffUpdate.clean_is_active(False, staff_user, staff_user)
    msg = "Cannot deactivate your own account."
    assert e.value.error_dict["is_active"][0].message == msg

    with pytest.raises(ValidationError) as e:
        StaffUpdate.clean_is_active(False, admin_user, staff_user)
    msg = "Cannot deactivate superuser's account."
    assert e.value.error_dict["is_active"][0].message == msg

    # should not raise any errors
    StaffUpdate.clean_is_active(False, customer_user, staff_user)


SET_PASSWORD_MUTATION = """
    mutation SetPassword($email: String!, $token: String!, $password: String!) {
        setPassword(email: $email, token: $token, password: $password) {
            errors {
                field
                message
            }
            accountErrors {
                field
                message
                code
            }
            user {
                id
            }
            token
        }
    }
"""


def test_set_password(user_api_client, customer_user):
    token = default_token_generator.make_token(customer_user)
    password = "spanish-inquisition"

    variables = {"email": customer_user.email, "password": password, "token": token}
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["setPassword"]
    assert data["user"]["id"]
    assert data["token"]

    customer_user.refresh_from_db()
    assert customer_user.check_password(password)

    password_resent_event = account_events.CustomerEvent.objects.get()
    assert password_resent_event.type == account_events.CustomerEvents.PASSWORD_RESET
    assert password_resent_event.user == customer_user


def test_set_password_invalid_token(user_api_client, customer_user):
    variables = {"email": customer_user.email, "password": "pass", "token": "token"}
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["setPassword"]["errors"]
    assert errors[0]["message"] == INVALID_TOKEN

    account_errors = content["data"]["setPassword"]["accountErrors"]
    assert account_errors[0]["message"] == INVALID_TOKEN
    assert account_errors[0]["code"] == AccountErrorCode.INVALID.name


def test_set_password_invalid_email(user_api_client):
    variables = {"email": "fake@example.com", "password": "pass", "token": "token"}
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["setPassword"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "email"

    account_errors = content["data"]["setPassword"]["accountErrors"]
    assert len(account_errors) == 1
    assert account_errors[0]["field"] == "email"
    assert account_errors[0]["code"] == AccountErrorCode.NOT_FOUND.name


def test_set_password_invalid_password(user_api_client, customer_user, settings):
    settings.AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            "OPTIONS": {"min_length": 5},
        },
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    token = default_token_generator.make_token(customer_user)
    variables = {"email": customer_user.email, "password": "1234", "token": token}
    response = user_api_client.post_graphql(SET_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["setPassword"]["errors"]
    assert len(errors) == 2
    assert (
        errors[0]["message"]
        == "This password is too short. It must contain at least 5 characters."
    )
    assert errors[1]["message"] == "This password is entirely numeric."

    account_errors = content["data"]["setPassword"]["accountErrors"]
    assert account_errors[0]["code"] == str_to_enum("password_too_short")
    assert account_errors[1]["code"] == str_to_enum("password_entirely_numeric")


@patch("saleor.account.emails._send_user_password_reset_email.delay")
def test_deprecated_password_reset_email(
    send_password_reset_mock, staff_api_client, customer_user, permission_manage_users
):
    query = """
    mutation ResetPassword($email: String!) {
        passwordReset(email: $email) {
            errors {
                field
                message
            }
        }
    }
    """
    email = customer_user.email
    variables = {"email": email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["passwordReset"]
    assert data == {"errors": []}
    assert send_password_reset_mock.call_count == 1
    send_password_reset_mock.assert_called_once_with(
        customer_user.email, ANY, customer_user.pk
    )


@patch("saleor.account.emails._send_user_password_reset_email.delay")
def test_password_reset_email_non_existing_user(
    send_password_reset_mock, staff_api_client, permission_manage_users
):
    query = """
    mutation ResetPassword($email: String!) {
        passwordReset(email: $email) {
            errors {
                field
                message
            }
        }
    }
    """
    email = "not_exists@example.com"
    variables = {"email": email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["passwordReset"]
    assert data["errors"] == [
        {"field": "email", "message": "User with this email doesn't exist"}
    ]
    send_password_reset_mock.assert_not_called()


CHANGE_PASSWORD_MUTATION = """
    mutation PasswordChange($oldPassword: String!, $newPassword: String!) {
        passwordChange(oldPassword: $oldPassword, newPassword: $newPassword) {
            errors {
                field
                message
            }
            user {
                email
            }
        }
    }
"""


def test_password_change(user_api_client):
    customer_user = user_api_client.user
    new_password = "spanish-inquisition"

    variables = {"oldPassword": "password", "newPassword": new_password}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["passwordChange"]
    assert not data["errors"]
    assert data["user"]["email"] == customer_user.email

    customer_user.refresh_from_db()
    assert customer_user.check_password(new_password)

    password_change_event = account_events.CustomerEvent.objects.get()
    assert password_change_event.type == account_events.CustomerEvents.PASSWORD_CHANGED
    assert password_change_event.user == customer_user


def test_password_change_incorrect_old_password(user_api_client):
    customer_user = user_api_client.user
    variables = {"oldPassword": "incorrect", "newPassword": ""}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["passwordChange"]
    customer_user.refresh_from_db()
    assert customer_user.check_password("password")
    assert data["errors"]
    assert data["errors"][0]["field"] == "oldPassword"


def test_password_change_invalid_new_password(user_api_client, settings):
    settings.AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            "OPTIONS": {"min_length": 5},
        },
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]

    customer_user = user_api_client.user
    variables = {"oldPassword": "password", "newPassword": "1234"}
    response = user_api_client.post_graphql(CHANGE_PASSWORD_MUTATION, variables)
    content = get_graphql_content(response)
    errors = content["data"]["passwordChange"]["errors"]
    customer_user.refresh_from_db()
    assert customer_user.check_password("password")
    assert len(errors) == 2
    assert errors[1]["field"] == "newPassword"
    assert (
        errors[0]["message"]
        == "This password is too short. It must contain at least 5 characters."
    )
    assert errors[1]["field"] == "newPassword"
    assert errors[1]["message"] == "This password is entirely numeric."


def test_create_address_mutation(
    staff_api_client, customer_user, permission_manage_users
):
    query = """
    mutation CreateUserAddress($user: ID!, $city: String!, $country: String!) {
        addressCreate(userId: $user, input: {city: $city, country: $country}) {
            errors {
                field
                message
            }
            address {
                id
                city
                country {
                    code
                }
            }
            user {
                id
            }
        }
    }
    """
    user_id = graphene.Node.to_global_id("User", customer_user.id)
    variables = {"user": user_id, "city": "Dummy", "country": "PL"}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    assert content["data"]["addressCreate"]["errors"] == []
    data = content["data"]["addressCreate"]
    assert data["address"]["city"] == "Dummy"
    assert data["address"]["country"]["code"] == "PL"
    address_obj = Address.objects.get(city="Dummy")
    assert address_obj.user_addresses.first() == customer_user
    assert data["user"]["id"] == user_id


ADDRESS_UPDATE_MUTATION = """
    mutation updateUserAddress($addressId: ID!, $address: AddressInput!) {
        addressUpdate(id: $addressId, input: $address) {
            address {
                city
            }
            user {
                id
            }
        }
    }
"""


def test_address_update_mutation(
    staff_api_client, customer_user, permission_manage_users, graphql_address_data
):
    query = ADDRESS_UPDATE_MUTATION
    address_obj = customer_user.addresses.first()
    assert staff_api_client.user not in address_obj.user_addresses.all()
    variables = {
        "addressId": graphene.Node.to_global_id("Address", address_obj.id),
        "address": graphql_address_data,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["addressUpdate"]
    assert data["address"]["city"] == graphql_address_data["city"]
    address_obj.refresh_from_db()
    assert address_obj.city == graphql_address_data["city"]


ACCOUNT_ADDRESS_UPDATE_MUTATION = """
    mutation updateAccountAddress($addressId: ID!, $address: AddressInput!) {
        accountAddressUpdate(id: $addressId, input: $address) {
            address {
                city
            }
            user {
                id
            }
        }
    }
"""


def test_customer_update_own_address(
    user_api_client, customer_user, graphql_address_data
):
    query = ACCOUNT_ADDRESS_UPDATE_MUTATION
    address_obj = customer_user.addresses.first()
    address_data = graphql_address_data
    address_data["city"] = "Poznań"
    assert address_data["city"] != address_obj.city

    variables = {
        "addressId": graphene.Node.to_global_id("Address", address_obj.id),
        "address": address_data,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountAddressUpdate"]
    assert data["address"]["city"] == address_data["city"]
    address_obj.refresh_from_db()
    assert address_obj.city == address_data["city"]


@pytest.mark.parametrize(
    "query", [ADDRESS_UPDATE_MUTATION, ACCOUNT_ADDRESS_UPDATE_MUTATION]
)
def test_customer_update_address_for_other(
    user_api_client, customer_user, address_other_country, graphql_address_data, query
):
    address_obj = address_other_country
    assert customer_user not in address_obj.user_addresses.all()

    address_data = graphql_address_data
    variables = {
        "addressId": graphene.Node.to_global_id("Address", address_obj.id),
        "address": address_data,
    }
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


ADDRESS_DELETE_MUTATION = """
    mutation deleteUserAddress($id: ID!) {
        addressDelete(id: $id) {
            address {
                city
            }
            user {
                id
            }
        }
    }
"""


def test_address_delete_mutation(
    staff_api_client, customer_user, permission_manage_users
):
    query = ADDRESS_DELETE_MUTATION
    address_obj = customer_user.addresses.first()
    variables = {"id": graphene.Node.to_global_id("Address", address_obj.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["addressDelete"]
    assert data["address"]["city"] == address_obj.city
    assert data["user"]["id"] == graphene.Node.to_global_id("User", customer_user.pk)
    with pytest.raises(address_obj._meta.model.DoesNotExist):
        address_obj.refresh_from_db()


ACCOUNT_ADDRESS_DELETE_MUTATION = """
    mutation deleteUserAddress($id: ID!) {
        accountAddressDelete(id: $id) {
            address {
                city
            }
            user {
                id
            }
        }
    }
"""


def test_customer_delete_own_address(user_api_client, customer_user):
    query = ACCOUNT_ADDRESS_DELETE_MUTATION
    address_obj = customer_user.addresses.first()
    variables = {"id": graphene.Node.to_global_id("Address", address_obj.id)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountAddressDelete"]
    assert data["address"]["city"] == address_obj.city
    with pytest.raises(address_obj._meta.model.DoesNotExist):
        address_obj.refresh_from_db()


@pytest.mark.parametrize(
    "query", [ADDRESS_DELETE_MUTATION, ACCOUNT_ADDRESS_DELETE_MUTATION]
)
def test_customer_delete_address_for_other(
    user_api_client, customer_user, address_other_country, query
):
    address_obj = address_other_country
    assert customer_user not in address_obj.user_addresses.all()
    variables = {"id": graphene.Node.to_global_id("Address", address_obj.id)}
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)
    address_obj.refresh_from_db()


SET_DEFAULT_ADDRESS_MUTATION = """
mutation($address_id: ID!, $user_id: ID!, $type: AddressTypeEnum!) {
  addressSetDefault(addressId: $address_id, userId: $user_id, type: $type) {
    errors {
      field
      message
    }
    user {
      defaultBillingAddress {
        id
      }
      defaultShippingAddress {
        id
      }
    }
  }
}
"""


def test_set_default_address(
    staff_api_client, address_other_country, customer_user, permission_manage_users
):
    customer_user.default_billing_address = None
    customer_user.default_shipping_address = None
    customer_user.save()

    # try to set an address that doesn't belong to that user
    address = address_other_country

    variables = {
        "address_id": graphene.Node.to_global_id("Address", address.id),
        "user_id": graphene.Node.to_global_id("User", customer_user.id),
        "type": AddressType.SHIPPING.upper(),
    }

    response = staff_api_client.post_graphql(
        SET_DEFAULT_ADDRESS_MUTATION, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    data = content["data"]["addressSetDefault"]
    assert data["errors"][0]["field"] == "addressId"

    # try to set a new billing address using one of user's addresses
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id("Address", address.id)

    variables["address_id"] = address_id
    response = staff_api_client.post_graphql(SET_DEFAULT_ADDRESS_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["addressSetDefault"]
    assert data["user"]["defaultShippingAddress"]["id"] == address_id


def test_address_validation_rules(user_api_client):
    query = """
    query getValidator(
        $country_code: CountryCode!, $country_area: String, $city_area: String) {
        addressValidationRules(
                countryCode: $country_code,
                countryArea: $country_area,
                cityArea: $city_area) {
            countryCode
            countryName
            addressFormat
            addressLatinFormat
            postalCodeMatchers
        }
    }
    """
    variables = {"country_code": "PL", "country_area": None, "city_area": None}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["addressValidationRules"]
    assert data["countryCode"] == "PL"
    assert data["countryName"] == "POLAND"
    assert data["addressFormat"] is not None
    assert data["addressLatinFormat"] is not None
    matcher = data["postalCodeMatchers"][0]
    matcher = re.compile(matcher)
    assert matcher.match("00-123")


def test_address_validation_rules_with_country_area(user_api_client):
    query = """
    query getValidator(
        $country_code: CountryCode!, $country_area: String, $city_area: String) {
        addressValidationRules(
                countryCode: $country_code,
                countryArea: $country_area,
                cityArea: $city_area) {
            countryCode
            countryName
            countryAreaType
            countryAreaChoices {
                verbose
                raw
            }
            cityType
            cityChoices {
                raw
                verbose
            }
            cityAreaType
            cityAreaChoices {
                raw
                verbose
            }
        }
    }
    """
    variables = {
        "country_code": "CN",
        "country_area": "Fujian Sheng",
        "city_area": None,
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["addressValidationRules"]
    assert data["countryCode"] == "CN"
    assert data["countryName"] == "CHINA"
    assert data["countryAreaType"] == "province"
    assert data["countryAreaChoices"]
    assert data["cityType"] == "city"
    assert data["cityChoices"]
    assert data["cityAreaType"] == "city"
    assert not data["cityAreaChoices"]


def test_address_validation_rules_fields_in_camel_case(user_api_client):
    query = """
    query getValidator(
        $country_code: CountryCode!) {
        addressValidationRules(countryCode: $country_code) {
            requiredFields
            allowedFields
        }
    }
    """
    variables = {"country_code": "PL"}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"]["addressValidationRules"]
    required_fields = data["requiredFields"]
    allowed_fields = data["allowedFields"]
    assert "streetAddress1" in required_fields
    assert "streetAddress2" not in required_fields
    assert "streetAddress1" in allowed_fields
    assert "streetAddress2" in allowed_fields


CUSTOMER_PASSWORD_RESET_MUTATION = """
    mutation CustomerPasswordReset($email: String!) {
        customerPasswordReset(input: {email: $email}) {
            errors {
                field
                message
            }
        }
    }
"""


@patch("saleor.account.emails._send_password_reset_email")
def test_deprecated_account_reset_password(
    send_password_reset_mock, user_api_client, customer_user
):
    # we have no user with given email
    variables = {"email": "non-existing-email@email.com"}
    response = user_api_client.post_graphql(CUSTOMER_PASSWORD_RESET_MUTATION, variables)
    get_graphql_content(response)
    assert not send_password_reset_mock.called

    variables = {"email": customer_user.email}
    response = user_api_client.post_graphql(CUSTOMER_PASSWORD_RESET_MUTATION, variables)
    get_graphql_content(response)
    assert send_password_reset_mock.called
    assert send_password_reset_mock.mock_calls[0][1][0] == customer_user.email


REQUEST_PASSWORD_RESET_MUTATION = """
    mutation RequestPasswordReset($email: String!, $redirectUrl: String!) {
        requestPasswordReset(email: $email, redirectUrl: $redirectUrl) {
            errors {
                field
                message
            }
        }
    }
"""


@patch("saleor.account.emails._send_password_reset_email")
def test_account_reset_password(
    send_password_reset_email_mock, user_api_client, customer_user
):
    variables = {"email": customer_user.email, "redirectUrl": "https://www.example.com"}
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    assert send_password_reset_email_mock.called
    send_password_reset_email_mock.assert_called_once_with(
        user_api_client.user.email, ANY, user_api_client.user.pk
    )
    url = send_password_reset_email_mock.mock_calls[0][1][1]
    url_validator = URLValidator()
    url_validator(url)


@patch("saleor.account.emails._send_password_reset_email")
def test_request_password_reset_email_for_staff(
    send_password_reset_email_mock, staff_api_client
):
    redirect_url = "https://www.example.com"
    variables = {"email": staff_api_client.user.email, "redirectUrl": redirect_url}
    response = staff_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    assert send_password_reset_email_mock.call_count == 1
    send_password_reset_email_mock.assert_called_once_with(
        staff_api_client.user.email, ANY, staff_api_client.user.pk
    )
    url = send_password_reset_email_mock.mock_calls[0][1][1]
    url_validator = URLValidator()
    url_validator(url)


@patch("saleor.account.emails._send_password_reset_email")
def test_account_reset_password_invalid_email(
    send_password_reset_email_mock, user_api_client
):
    variables = {
        "email": "non-existing-email@email.com",
        "redirectUrl": "https://www.example.com",
    }
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert len(data["errors"]) == 1
    assert not send_password_reset_email_mock.called


@patch("saleor.account.emails._send_password_reset_email")
def test_account_reset_password_storefront_hosts_not_allowed(
    send_password_reset_email_mock, user_api_client, customer_user
):
    variables = {"email": customer_user.email, "redirectUrl": "https://www.fake.com"}
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "redirectUrl"
    assert not send_password_reset_email_mock.called


@patch("saleor.account.emails._send_password_reset_email")
def test_account_reset_password_all_storefront_hosts_allowed(
    send_password_reset_email_mock, user_api_client, customer_user, settings
):
    settings.ALLOWED_CLIENT_HOSTS = ["*"]
    variables = {"email": customer_user.email, "redirectUrl": "https://www.test.com"}
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    assert send_password_reset_email_mock.called
    send_password_reset_email_mock.assert_called_once_with(
        user_api_client.user.email, ANY, user_api_client.user.pk
    )
    url = send_password_reset_email_mock.mock_calls[0][1][1]
    url_validator = URLValidator()
    url_validator(url)


@patch("saleor.account.emails._send_password_reset_email")
def test_account_reset_password_subdomain(
    send_password_reset_email_mock, user_api_client, customer_user, settings
):
    settings.ALLOWED_CLIENT_HOSTS = [".example.com"]
    variables = {"email": customer_user.email, "redirectUrl": "https://sub.example.com"}
    response = user_api_client.post_graphql(REQUEST_PASSWORD_RESET_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["requestPasswordReset"]
    assert not data["errors"]
    assert send_password_reset_email_mock.called
    send_password_reset_email_mock.assert_called_once_with(
        user_api_client.user.email, ANY, user_api_client.user.pk
    )
    url = send_password_reset_email_mock.mock_calls[0][1][1]
    url_validator = URLValidator()
    url_validator(url)


CUSTOMER_ADDRESS_CREATE_MUTATION = """
mutation($addressInput: AddressInput!, $addressType: AddressTypeEnum) {
  customerAddressCreate(input: $addressInput, type: $addressType) {
    address {
        id,
        city
    }
  }
}
"""


ACCOUNT_ADDRESS_CREATE_MUTATION = """
mutation($addressInput: AddressInput!, $addressType: AddressTypeEnum) {
  accountAddressCreate(input: $addressInput, type: $addressType) {
    address {
        id,
        city
    }
    user {
        email
    }
  }
}
"""


@pytest.mark.parametrize(
    "query, mutation_name",
    [
        (CUSTOMER_ADDRESS_CREATE_MUTATION, "customerAddressCreate"),
        (ACCOUNT_ADDRESS_CREATE_MUTATION, "accountAddressCreate"),
    ],
)
def test_customer_create_address(
    user_api_client, graphql_address_data, query, mutation_name
):
    user = user_api_client.user
    nr_of_addresses = user.addresses.count()

    variables = {"addressInput": graphql_address_data}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]

    assert data["address"]["city"] == graphql_address_data["city"]

    user.refresh_from_db()
    assert user.addresses.count() == nr_of_addresses + 1


def test_account_address_create_return_user(user_api_client, graphql_address_data):
    user = user_api_client.user
    variables = {"addressInput": graphql_address_data}
    response = user_api_client.post_graphql(ACCOUNT_ADDRESS_CREATE_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["accountAddressCreate"]["user"]
    assert data["email"] == user.email


@pytest.mark.parametrize(
    "query, mutation_name",
    [
        (CUSTOMER_ADDRESS_CREATE_MUTATION, "customerAddressCreate"),
        (ACCOUNT_ADDRESS_CREATE_MUTATION, "accountAddressCreate"),
    ],
)
def test_customer_create_default_address(
    user_api_client, graphql_address_data, query, mutation_name
):
    user = user_api_client.user
    nr_of_addresses = user.addresses.count()

    address_type = AddressType.SHIPPING.upper()
    variables = {"addressInput": graphql_address_data, "addressType": address_type}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert data["address"]["city"] == graphql_address_data["city"]

    user.refresh_from_db()
    assert user.addresses.count() == nr_of_addresses + 1
    assert user.default_shipping_address.id == int(
        graphene.Node.from_global_id(data["address"]["id"])[1]
    )

    address_type = AddressType.BILLING.upper()
    variables = {"addressInput": graphql_address_data, "addressType": address_type}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert data["address"]["city"] == graphql_address_data["city"]

    user.refresh_from_db()
    assert user.addresses.count() == nr_of_addresses + 2
    assert user.default_billing_address.id == int(
        graphene.Node.from_global_id(data["address"]["id"])[1]
    )


@pytest.mark.parametrize(
    "query", [CUSTOMER_ADDRESS_CREATE_MUTATION, ACCOUNT_ADDRESS_CREATE_MUTATION]
)
def test_anonymous_user_create_address(api_client, graphql_address_data, query):
    variables = {"addressInput": graphql_address_data}
    response = api_client.post_graphql(query, variables)
    assert_no_permission(response)


CUSTOMER_SET_DEFAULT_ADDRESS_MUTATION = """
mutation($id: ID!, $type: AddressTypeEnum!) {
  customerSetDefaultAddress(id: $id, type: $type) {
    errors {
      field,
      message
    }
  }
}
"""


ACCOUNT_SET_DEFAULT_ADDRESS_MUTATION = """
mutation($id: ID!, $type: AddressTypeEnum!) {
  accountSetDefaultAddress(id: $id, type: $type) {
    errors {
      field,
      message
    }
  }
}
"""


@pytest.mark.parametrize(
    "query, mutation_name",
    [
        (CUSTOMER_SET_DEFAULT_ADDRESS_MUTATION, "customerSetDefaultAddress"),
        (ACCOUNT_SET_DEFAULT_ADDRESS_MUTATION, "accountSetDefaultAddress"),
    ],
)
def test_customer_set_address_as_default(user_api_client, query, mutation_name):
    user = user_api_client.user
    user.default_billing_address = None
    user.default_shipping_address = None
    user.save()
    assert not user.default_billing_address
    assert not user.default_shipping_address
    assert user.addresses.exists()

    address = user.addresses.first()

    variables = {
        "id": graphene.Node.to_global_id("Address", address.id),
        "type": AddressType.SHIPPING.upper(),
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]

    user.refresh_from_db()
    assert user.default_shipping_address == address

    variables["type"] = AddressType.BILLING.upper()
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]

    user.refresh_from_db()
    assert user.default_billing_address == address


@pytest.mark.parametrize(
    "query, mutation_name",
    [
        (CUSTOMER_SET_DEFAULT_ADDRESS_MUTATION, "customerSetDefaultAddress"),
        (ACCOUNT_SET_DEFAULT_ADDRESS_MUTATION, "accountSetDefaultAddress"),
    ],
)
def test_customer_change_default_address(
    user_api_client, address_other_country, query, mutation_name
):
    user = user_api_client.user
    assert user.default_billing_address
    assert user.default_billing_address
    address = user.default_shipping_address
    assert address in user.addresses.all()
    assert address_other_country not in user.addresses.all()

    user.default_shipping_address = address_other_country
    user.save()
    user.refresh_from_db()
    assert address_other_country not in user.addresses.all()

    variables = {
        "id": graphene.Node.to_global_id("Address", address.id),
        "type": AddressType.SHIPPING.upper(),
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content["data"][mutation_name]
    assert not data["errors"]

    user.refresh_from_db()
    assert user.default_shipping_address == address
    assert address_other_country in user.addresses.all()


@pytest.mark.parametrize(
    "query, mutation_name",
    [
        (CUSTOMER_SET_DEFAULT_ADDRESS_MUTATION, "customerSetDefaultAddress"),
        (ACCOUNT_SET_DEFAULT_ADDRESS_MUTATION, "accountSetDefaultAddress"),
    ],
)
def test_customer_change_default_address_invalid_address(
    user_api_client, address_other_country, query, mutation_name
):
    user = user_api_client.user
    assert address_other_country not in user.addresses.all()

    variables = {
        "id": graphene.Node.to_global_id("Address", address_other_country.id),
        "type": AddressType.SHIPPING.upper(),
    }
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"][mutation_name]["errors"][0]["field"] == "id"


USER_AVATAR_UPDATE_MUTATION = """
    mutation userAvatarUpdate($image: Upload!) {
        userAvatarUpdate(image: $image) {
            user {
                avatar {
                    url
                }
            }
        }
    }
"""


def test_user_avatar_update_mutation_permission(api_client):
    """ Should raise error if user is not staff. """

    query = USER_AVATAR_UPDATE_MUTATION

    image_file, image_name = create_image("avatar")
    variables = {"image": image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = api_client.post_multipart(body)

    assert_no_permission(response)


def test_user_avatar_update_mutation(monkeypatch, staff_api_client, media_root):
    query = USER_AVATAR_UPDATE_MUTATION

    user = staff_api_client.user

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        (
            "saleor.graphql.account.mutations.staff."
            "create_user_avatar_thumbnails.delay"
        ),
        mock_create_thumbnails,
    )

    image_file, image_name = create_image("avatar")
    variables = {"image": image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)

    data = content["data"]["userAvatarUpdate"]
    user.refresh_from_db()

    assert user.avatar
    assert data["user"]["avatar"]["url"].startswith(
        "http://testserver/media/user-avatars/avatar"
    )

    # The image creation should have triggered a warm-up
    mock_create_thumbnails.assert_called_once_with(user_id=user.pk)


def test_user_avatar_update_mutation_image_exists(staff_api_client, media_root):
    query = USER_AVATAR_UPDATE_MUTATION

    user = staff_api_client.user
    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = "image.jpg"
    user.avatar = avatar_mock
    user.save()

    image_file, image_name = create_image("new_image")
    variables = {"image": image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)

    data = content["data"]["userAvatarUpdate"]
    user.refresh_from_db()

    assert user.avatar != avatar_mock
    assert data["user"]["avatar"]["url"].startswith(
        "http://testserver/media/user-avatars/new_image"
    )


USER_AVATAR_DELETE_MUTATION = """
    mutation userAvatarDelete {
        userAvatarDelete {
            user {
                avatar {
                    url
                }
            }
        }
    }
"""


def test_user_avatar_delete_mutation_permission(api_client):
    """ Should raise error if user is not staff. """

    query = USER_AVATAR_DELETE_MUTATION

    response = api_client.post_graphql(query)

    assert_no_permission(response)


def test_user_avatar_delete_mutation(staff_api_client):
    query = USER_AVATAR_DELETE_MUTATION

    user = staff_api_client.user

    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)

    user.refresh_from_db()

    assert not user.avatar
    assert not content["data"]["userAvatarDelete"]["user"]["avatar"]


@pytest.mark.parametrize(
    "customer_filter, count",
    [
        ({"placedOrders": {"gte": "2019-04-18"}}, 1),
        ({"placedOrders": {"lte": "2012-01-14"}}, 1),
        ({"placedOrders": {"lte": "2012-01-14", "gte": "2012-01-13"}}, 1),
        ({"placedOrders": {"gte": "2012-01-14"}}, 2),
    ],
)
def test_query_customers_with_filter_placed_orders(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_user,
):
    Order.objects.create(user=customer_user)
    second_customer = User.objects.create(email="second_example@example.com")
    with freeze_time("2012-01-14 11:00:00"):
        Order.objects.create(user=second_customer)
    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]

    assert len(users) == count


@pytest.mark.parametrize(
    "customer_filter, count",
    [
        ({"dateJoined": {"gte": "2019-04-18"}}, 1),
        ({"dateJoined": {"lte": "2012-01-14"}}, 1),
        ({"dateJoined": {"lte": "2012-01-14", "gte": "2012-01-13"}}, 1),
        ({"dateJoined": {"gte": "2012-01-14"}}, 2),
    ],
)
def test_query_customers_with_filter_date_joined(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_user,
):
    with freeze_time("2012-01-14 11:00:00"):
        User.objects.create(email="second_example@example.com")
    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]

    assert len(users) == count


@pytest.mark.parametrize(
    "customer_filter, count",
    [
        ({"numberOfOrders": {"gte": 0, "lte": 1}}, 1),
        ({"numberOfOrders": {"gte": 1, "lte": 3}}, 2),
        ({"numberOfOrders": {"gte": 0}}, 2),
        ({"numberOfOrders": {"lte": 3}}, 2),
    ],
)
def test_query_customers_with_filter_placed_orders_(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_user,
):
    Order.objects.bulk_create(
        [
            Order(user=customer_user, token=str(uuid.uuid4())),
            Order(user=customer_user, token=str(uuid.uuid4())),
            Order(user=customer_user, token=str(uuid.uuid4())),
        ]
    )
    second_customer = User.objects.create(email="second_example@example.com")
    with freeze_time("2012-01-14 11:00:00"):
        Order.objects.create(user=second_customer)
    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]

    assert len(users) == count


@pytest.mark.parametrize(
    "customer_filter, count",
    [
        ({"moneySpent": {"gte": 16, "lte": 25}}, 1),
        ({"moneySpent": {"gte": 15, "lte": 26}}, 2),
        ({"moneySpent": {"gte": 0}}, 2),
        ({"moneySpent": {"lte": 16}}, 1),
    ],
)
def test_query_customers_with_filter_placed_orders__(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_user,
):
    second_customer = User.objects.create(email="second_example@example.com")
    Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                token=str(uuid.uuid4()),
                total_gross=Money(15, "USD"),
            ),
            Order(
                user=second_customer,
                token=str(uuid.uuid4()),
                total_gross=Money(25, "USD"),
            ),
        ]
    )

    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]

    assert len(users) == count


@pytest.mark.parametrize(
    "customer_filter, count",
    [
        ({"search": "example.com"}, 2),
        ({"search": "Alice"}, 1),
        ({"search": "Kowalski"}, 1),
        ({"search": "John"}, 1),  # default_shipping_address__first_name
        ({"search": "Doe"}, 1),  # default_shipping_address__last_name
        ({"search": "wroc"}, 1),  # default_shipping_address__city
        ({"search": "pl"}, 2),  # default_shipping_address__country, email
    ],
)
def test_query_customer_memebers_with_filter_search(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    address,
    staff_user,
):

    User.objects.bulk_create(
        [
            User(
                email="second@example.com",
                first_name="Alice",
                last_name="Kowalski",
                is_active=False,
            ),
            User(
                email="third@example.com",
                is_active=True,
                default_shipping_address=address,
            ),
        ]
    )

    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]

    assert len(users) == count


@pytest.mark.parametrize(
    "staff_member_filter, count",
    [({"status": "DEACTIVATED"}, 1), ({"status": "ACTIVE"}, 2)],
)
def test_query_staff_memebers_with_filter_status(
    staff_member_filter,
    count,
    query_staff_users_with_filter,
    staff_api_client,
    permission_manage_staff,
    staff_user,
):

    User.objects.bulk_create(
        [
            User(email="second@example.com", is_staff=True, is_active=False),
            User(email="third@example.com", is_staff=True, is_active=True),
        ]
    )

    variables = {"filter": staff_member_filter}
    response = staff_api_client.post_graphql(
        query_staff_users_with_filter, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    users = content["data"]["staffUsers"]["edges"]

    assert len(users) == count


@pytest.mark.parametrize(
    "staff_member_filter, count",
    [
        ({"search": "example.com"}, 3),
        ({"search": "Alice"}, 1),
        ({"search": "Kowalski"}, 1),
        ({"search": "John"}, 1),  # default_shipping_address__first_name
        ({"search": "Doe"}, 1),  # default_shipping_address__last_name
        ({"search": "wroc"}, 1),  # default_shipping_address__city
        ({"search": "pl"}, 3),  # default_shipping_address__country, email
    ],
)
def test_query_staff_memebers_with_filter_search(
    staff_member_filter,
    count,
    query_staff_users_with_filter,
    staff_api_client,
    permission_manage_staff,
    address,
    staff_user,
):

    User.objects.bulk_create(
        [
            User(
                email="second@example.com",
                first_name="Alice",
                last_name="Kowalski",
                is_staff=True,
                is_active=False,
            ),
            User(
                email="third@example.com",
                is_staff=True,
                is_active=True,
                default_shipping_address=address,
            ),
            User(
                email="customer@example.com",
                first_name="Alice",
                last_name="Kowalski",
                is_staff=False,
                is_active=True,
            ),
        ]
    )

    variables = {"filter": staff_member_filter}
    response = staff_api_client.post_graphql(
        query_staff_users_with_filter, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    users = content["data"]["staffUsers"]["edges"]

    assert len(users) == count


USER_CHANGE_ACTIVE_STATUS_MUTATION = """
    mutation userChangeActiveStatus($ids: [ID]!, $is_active: Boolean!) {
        userBulkSetActive(ids: $ids, isActive: $is_active) {
            count
            errors {
                field
                message
            }
        }
    }
    """


def test_staff_bulk_set_active(
    staff_api_client, user_list_not_active, permission_manage_users
):
    users = user_list_not_active
    active_status = True
    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in users],
        "is_active": active_status,
    }
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["userBulkSetActive"]
    assert data["count"] == users.count()
    users = User.objects.filter(pk__in=[user.pk for user in users])
    assert all(user.is_active for user in users)


def test_staff_bulk_set_not_active(
    staff_api_client, user_list, permission_manage_users
):
    users = user_list
    active_status = False
    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in users],
        "is_active": active_status,
    }
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["userBulkSetActive"]
    assert data["count"] == len(users)
    users = User.objects.filter(pk__in=[user.pk for user in users])
    assert not any(user.is_active for user in users)


def test_change_active_status_for_superuser(
    staff_api_client, superuser, permission_manage_users
):
    users = [superuser]
    superuser_id = graphene.Node.to_global_id("User", superuser.id)
    active_status = False
    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in users],
        "is_active": active_status,
    }
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["userBulkSetActive"]
    assert data["errors"][0]["field"] == superuser_id
    assert (
        data["errors"][0]["message"] == "Cannot activate or deactivate "
        "superuser's account."
    )


def test_change_active_status_for_himself(staff_api_client, permission_manage_users):
    users = [staff_api_client.user]
    user_id = graphene.Node.to_global_id("User", staff_api_client.user.id)
    active_status = False
    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in users],
        "is_active": active_status,
    }
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION,
        variables,
        permissions=[permission_manage_users],
    )
    content = get_graphql_content(response)
    data = content["data"]["userBulkSetActive"]
    assert data["errors"][0]["field"] == user_id
    assert (
        data["errors"][0]["message"] == "Cannot activate or deactivate "
        "your own account."
    )
