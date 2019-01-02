import json
import re
from unittest.mock import Mock, patch

import graphene
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import reverse

from saleor.account.models import Address, User
from saleor.graphql.account.mutations import (
    CustomerDelete, SetPassword, StaffDelete, StaffUpdate, UserDelete)
from saleor.graphql.core.enums import PermissionEnum
from tests.api.utils import get_graphql_content

from .utils import assert_no_permission, convert_dict_keys_to_camel_case


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
    variables = {'email': staff_user.email, 'password': 'password'}
    response = admin_client.post(
        reverse('api'), json.dumps({'query': query, 'variables': variables}),
        content_type='application/json')
    content = get_graphql_content(response)
    token_data = content['data']['tokenCreate']
    assert token_data['token']
    assert not token_data['errors']

    incorrect_variables = {'email': staff_user.email, 'password': 'incorrect'}
    response = admin_client.post(
        reverse('api'),
        json.dumps({'query': query, 'variables': incorrect_variables}),
        content_type='application/json')
    content = get_graphql_content(response)
    token_data = content['data']['tokenCreate']
    errors = token_data['errors']
    assert errors
    assert not errors[0]['field']
    assert not token_data['token']


def test_token_create_user_data(
        permission_manage_orders, staff_api_client, staff_user):
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
    user_id = graphene.Node.to_global_id('User', staff_user.id)

    variables = {'email': staff_user.email, 'password': 'password'}
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    token_data = content['data']['tokenCreate']
    assert token_data['user']['id'] == user_id
    assert token_data['user']['email'] == staff_user.email
    assert token_data['user']['permissions'][0]['name'] == name
    assert token_data['user']['permissions'][0]['code'] == 'MANAGE_ORDERS'


def test_query_user(staff_api_client, customer_user, permission_manage_users):
    user = customer_user
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
            }
        }
    }
    """
    ID = graphene.Node.to_global_id('User', customer_user.id)
    variables = {'id': ID}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['user']
    assert data['email'] == user.email
    assert data['firstName'] == user.first_name
    assert data['lastName'] == user.last_name
    assert data['isStaff'] == user.is_staff
    assert data['isActive'] == user.is_active
    assert len(data['addresses']) == user.addresses.count()
    assert data['orders']['totalCount'] == user.orders.count()
    address = data['defaultShippingAddress']
    user_address = user.default_shipping_address
    assert address['firstName'] == user_address.first_name
    assert address['lastName'] == user_address.last_name
    assert address['companyName'] == user_address.company_name
    assert address['streetAddress1'] == user_address.street_address_1
    assert address['streetAddress2'] == user_address.street_address_2
    assert address['city'] == user_address.city
    assert address['cityArea'] == user_address.city_area
    assert address['postalCode'] == user_address.postal_code
    assert address['country']['code'] == user_address.country.code
    assert address['countryArea'] == user_address.country_area
    assert address['phone'] == user_address.phone.as_e164


USER_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            email
        }
    }
"""


def test_customer_can_not_see_other_users_data(user_api_client,
                                               staff_user):
    id = graphene.Node.to_global_id('User', staff_user.id)
    variables = {'id': id}
    response = user_api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)


def test_user_query_anonymous_user(api_client):
    variables = {'id': ''}
    response = api_client.post_graphql(
        USER_QUERY, variables)
    assert_no_permission(response)


def test_query_customers(
        staff_api_client, user_api_client, permission_manage_users):
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
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    users = content['data']['customers']['edges']
    assert users
    assert all([not user['node']['isStaff'] for user in users])

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_query_staff(
        staff_api_client, user_api_client, staff_user, customer_user,
        admin_user, permission_manage_staff):
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
        query, variables, permissions=[permission_manage_staff])
    content = get_graphql_content(response)
    data = content['data']['staffUsers']['edges']
    assert len(data) == 2
    staff_emails = [user['node']['email'] for user in data]
    assert sorted(staff_emails) == [admin_user.email, staff_user.email]
    assert all([user['node']['isStaff'] for user in data])

    # check permissions
    response = user_api_client.post_graphql(query, variables)
    assert_no_permission(response)


def test_who_can_see_user(
        staff_user, customer_user, staff_api_client, user_api_client,
        permission_manage_users):
    query = """
    query Users {
        customers {
            totalCount
        }
    }
    """

    # Random person (even staff) can't see users data without permissions
    ID = graphene.Node.to_global_id('User', customer_user.id)
    variables = {'id': ID}
    response = staff_api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)

    response = staff_api_client.post_graphql(query)
    assert_no_permission(response)

    # Add permission and ensure staff can see user(s)
    staff_user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(USER_QUERY, variables)
    content = get_graphql_content(response)
    assert content['data']['user']['email'] == customer_user.email

    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    assert content['data']['customers']['totalCount'] == 1


ME_QUERY = """
    query Me {
        me {
            id
            email
        }
    }
"""


def test_me_query(user_api_client):
    response = user_api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    data = content['data']['me']
    assert data['email'] == user_api_client.user.email


def test_me_query_anonymous_client(api_client):
    response = api_client.post_graphql(ME_QUERY)
    assert_no_permission(response)


def test_me_query_customer_can_not_see_note(
        staff_user, staff_api_client, permission_manage_users):
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
        query, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['me']
    assert data['email'] == staff_api_client.user.email
    assert data['note'] == staff_api_client.user.note


def test_customer_register(user_api_client):
    query = """
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
    email = 'customer@example.com'
    variables = {'email': email, 'password': 'Password'}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['customerRegister']
    assert not data['errors']
    assert User.objects.filter(email=email).exists()

    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['customerRegister']
    assert data['errors']
    assert data['errors'][0]['field'] == 'email'
    assert data['errors'][0]['message'] == (
        'User with this Email already exists.')


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_customer_create(
        send_password_reset_mock, staff_api_client, user_api_client, address,
        permission_manage_users):
    query = """
    mutation CreateCustomer(
        $email: String, $firstName: String, $lastName: String,
        $note: String, $billing: AddressInput, $shipping: AddressInput,
        $send_mail: Boolean) {
        customerCreate(input: {
            email: $email,
            firstName: $firstName,
            lastName: $lastName,
            note: $note,
            defaultShippingAddress: $shipping,
            defaultBillingAddress: $billing
            sendPasswordEmail: $send_mail
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
    email = 'api_user@example.com'
    first_name = "api_first_name"
    last_name = "api_last_name"
    note = 'Test user'
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    variables = {
        'email': email,
        'firstName': first_name,
        'lastName': last_name,
        'note': note,
        'shipping': address_data,
        'billing': address_data,
        'send_mail': True}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)

    User = get_user_model()
    customer = User.objects.get(email=email)

    assert customer.default_billing_address == address
    assert customer.default_shipping_address == address
    assert customer.default_shipping_address.pk != customer.default_billing_address.pk

    data = content['data']['customerCreate']
    assert data['errors'] == []
    assert data['user']['email'] == email
    assert data['user']['firstName'] == first_name
    assert data['user']['lastName'] == last_name
    assert data['user']['note'] == note
    assert data['user']['isStaff'] == False
    assert data['user']['isActive'] == True

    assert send_password_reset_mock.call_count == 1
    args, kwargs = send_password_reset_mock.call_args
    call_context = args[0]
    call_email = args[1]
    assert call_email == email
    assert 'token' in call_context


def test_customer_update(
        staff_api_client, customer_user, address, permission_manage_users):
    query = """
    mutation UpdateCustomer($id: ID!, $firstName: String, $lastName: String, $isActive: Boolean, $note: String, $billing: AddressInput, $shipping: AddressInput) {
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

    id = graphene.Node.to_global_id('User', customer_user.id)
    first_name = 'new_first_name'
    last_name = 'new_last_name'
    note = 'Test update note'
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    new_street_address = 'Updated street address'
    address_data['streetAddress1'] = new_street_address

    variables = {
        'id': id,
        'firstName': first_name,
        'lastName': last_name,
        'isActive': False,
        'note': note,
        'billing': address_data,
        'shipping': address_data}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)

    User = get_user_model()
    customer = User.objects.get(email=customer_user.email)

    # check that existing instances are updated
    assert customer.default_billing_address.pk == billing_address_pk
    assert customer.default_shipping_address.pk == shipping_address_pk

    assert customer.default_billing_address.street_address_1 == new_street_address
    assert customer.default_shipping_address.street_address_1 == new_street_address

    data = content['data']['customerUpdate']
    assert data['errors'] == []
    assert data['user']['firstName'] == first_name
    assert data['user']['lastName'] == last_name
    assert data['user']['note'] == note
    assert not data['user']['isActive']


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


def test_logged_customer_update(user_api_client, graphql_address_data):
    # this test requires addresses to be set and checks whether new address
    # instances weren't created, but the existing ones got updated
    user = user_api_client.user
    new_first_name = graphql_address_data['firstName']
    assert user.default_billing_address
    assert user.default_shipping_address
    assert user.default_billing_address.first_name != new_first_name
    assert user.default_shipping_address.first_name != new_first_name
    variables = {
        'billing': graphql_address_data,
        'shipping': graphql_address_data}
    response = user_api_client.post_graphql(
        UPDATE_LOGGED_CUSTOMER_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['loggedUserUpdate']
    assert not data['errors']

    # check that existing instances are updated
    billing_address_pk = user.default_billing_address.pk
    shipping_address_pk = user.default_shipping_address.pk
    user = User.objects.get(email=user.email)
    assert user.default_billing_address.pk == billing_address_pk
    assert user.default_shipping_address.pk == shipping_address_pk

    assert user.default_billing_address.first_name == new_first_name
    assert user.default_shipping_address.first_name == new_first_name


def test_logged_customer_update_anonymus_user(api_client):
    response = api_client.post_graphql(
        UPDATE_LOGGED_CUSTOMER_QUERY, {})
    assert_no_permission(response)


def test_customer_delete(staff_api_client, customer_user, permission_manage_users):
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
    customer_id = graphene.Node.to_global_id('User', customer_user.pk)
    variables = {'id': customer_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['customerDelete']
    assert data['errors'] == []
    assert data['user']['id'] == customer_id


def test_customer_delete_errors(customer_user, admin_user, staff_user):
    info = Mock(context=Mock(user=admin_user))
    errors = CustomerDelete.clean_instance(info, staff_user, [])
    assert errors[0].field == 'id'
    assert errors[0].message == 'Cannot delete a staff account.'

    errors = CustomerDelete.clean_instance(info, customer_user, [])
    assert errors == []


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_staff_create(
        send_password_reset_mock, staff_api_client,
        permission_manage_staff, permission_manage_products, staff_user):
    query = """
    mutation CreateStaff($email: String, $permissions: [PermissionEnum], $send_mail: Boolean) {
        staffCreate(input: {email: $email, permissions: $permissions, sendPasswordEmail: $send_mail}) {
            errors {
                field
                message
            }
            user {
                id
                email
                isStaff
                isActive
                permissions {
                    code
                }
            }
        }
    }
    """

    email = 'api_user@example.com'
    variables = {
        'email': email,
        'permissions': [PermissionEnum.MANAGE_PRODUCTS.name],
        'send_mail': True}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff])
    content = get_graphql_content(response)
    data = content['data']['staffCreate']
    assert data['errors'] == []
    assert data['user']['email'] == email
    assert data['user']['isStaff'] == True
    assert data['user']['isActive'] == True
    permissions = data['user']['permissions']
    assert permissions[0]['code'] == 'MANAGE_PRODUCTS'

    assert send_password_reset_mock.call_count == 1
    args, kwargs = send_password_reset_mock.call_args
    call_context = args[0]
    call_email = args[1]
    assert call_email == email
    assert 'token' in call_context


def test_staff_update(staff_api_client, permission_manage_staff):
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
    staff_user = User.objects.create(
        email='staffuser@example.com', is_staff=True)
    id = graphene.Node.to_global_id('User', staff_user.id)
    variables = {'id': id, 'permissions': [], 'is_active': False}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff])
    content = get_graphql_content(response)
    data = content['data']['staffUpdate']
    assert data['errors'] == []
    assert data['user']['permissions'] == []
    assert data['user']['isActive'] == False


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
    staff_user = User.objects.create(
        email='staffuser@example.com', is_staff=True)
    user_id = graphene.Node.to_global_id('User', staff_user.id)
    variables = {'id': user_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff])
    content = get_graphql_content(response)
    data = content['data']['staffDelete']
    assert data['errors'] == []
    assert not User.objects.filter(pk=staff_user.id).exists()


def test_user_delete_errors(staff_user, customer_user, admin_user):
    info = Mock(context=Mock(user=staff_user))
    errors = UserDelete.clean_instance(info, staff_user, [])
    assert errors[0].field == 'id'
    assert errors[0].message == 'You cannot delete your own account.'

    info = Mock(context=Mock(user=staff_user))
    errors = UserDelete.clean_instance(info, admin_user, [])
    assert errors[0].field == 'id'
    assert errors[0].message == 'Only superuser can delete his own account.'


def test_staff_delete_errors(staff_user, customer_user, admin_user):
    info = Mock(context=Mock(user=staff_user))
    errors = StaffDelete.clean_instance(info, customer_user, [])
    assert errors[0].field == 'id'
    assert errors[0].message == 'Cannot delete a non-staff user.'

    info = Mock(context=Mock(user=admin_user))
    errors = StaffDelete.clean_instance(info, staff_user, [])
    assert not errors


def test_staff_update_errors(staff_user, customer_user, admin_user):
    errors = StaffUpdate.clean_is_active(None, customer_user, staff_user, [])
    assert not errors

    errors = StaffUpdate.clean_is_active(False, staff_user, staff_user, [])
    assert errors[0].field == 'isActive'
    assert errors[0].message == 'Cannot deactivate your own account.'

    errors = StaffUpdate.clean_is_active(False, admin_user, staff_user, [])
    assert errors[0].field == 'isActive'
    assert errors[0].message == 'Cannot deactivate superuser\'s account.'

    errors = StaffUpdate.clean_is_active(False, customer_user, staff_user, [])
    assert not errors


def test_set_password(user_api_client, customer_user):
    query = """
    mutation SetPassword($id: ID!, $token: String!, $password: String!) {
        setPassword(id: $id, input: {token: $token, password: $password}) {
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
    id = graphene.Node.to_global_id('User', customer_user.id)
    token = default_token_generator.make_token(customer_user)
    password = 'spanish-inquisition'

    # check invalid token
    variables = {'id': id, 'password': password, 'token': 'nope'}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    errors = content['data']['setPassword']['errors']
    assert errors[0]['message'] == SetPassword.INVALID_TOKEN

    variables['token'] = token
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['setPassword']
    assert data['user']['id']

    customer_user.refresh_from_db()
    assert customer_user.check_password(password)


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_password_reset_email(
        send_password_reset_mock, staff_api_client, customer_user,
        permission_manage_users):
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
    variables = {'email': email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['passwordReset']
    assert data is None
    assert send_password_reset_mock.call_count == 1
    args, kwargs = send_password_reset_mock.call_args
    call_context = args[0]
    call_email = args[1]
    assert call_email == email
    assert 'token' in call_context


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_password_reset_email_non_existing_user(
        send_password_reset_mock, staff_api_client, customer_user,
        permission_manage_users):
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
    email = 'not_exists@example.com'
    variables = {'email': email}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['passwordReset']
    assert data['errors'] == [{
        'field': 'email',
        'message': "User with this email doesn't exist"}]
    send_password_reset_mock.assert_not_called()


def test_create_address_mutation(
        staff_api_client, customer_user, permission_manage_users):
    query = """
    mutation CreateUserAddress($user: ID!, $city: String!, $country: String!) {
        addressCreate(input: {userId: $user, city: $city, country: $country}) {
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
        }
    }
    """
    user_id = graphene.Node.to_global_id('User', customer_user.id)
    variables = {'user': user_id, 'city': 'Dummy', 'country': 'PL'}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    assert content['data']['addressCreate']['errors'] == []
    address_response = content['data']['addressCreate']['address']
    assert address_response['city'] == 'Dummy'
    assert address_response['country']['code'] == 'PL'
    address_obj = Address.objects.get(city='Dummy')
    assert address_obj.user_addresses.first() == customer_user


def test_address_update_mutation(
        staff_api_client, customer_user, permission_manage_users,
        graphql_address_data):
    query = """
    mutation updateUserAddress($addressId: ID!, $address: AddressInput!) {
        addressUpdate(id: $addressId, input: $address) {
            address {
                city
            }
        }
    }
    """
    address_obj = customer_user.addresses.first()
    variables = {
        'addressId': graphene.Node.to_global_id('Address', address_obj.id),
        'address': graphql_address_data}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['addressUpdate']
    assert data['address']['city'] == graphql_address_data['city']
    address_obj.refresh_from_db()
    assert address_obj.city == graphql_address_data['city']


def test_address_delete_mutation(
        staff_api_client, customer_user, permission_manage_users):
    query = """
            mutation deleteUserAddress($id: ID!) {
                addressDelete(id: $id) {
                    address {
                        city
                    }
                }
            }
        """
    address_obj = customer_user.addresses.first()
    variables = {'id': graphene.Node.to_global_id('Address', address_obj.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['addressDelete']
    assert data['address']['city'] == address_obj.city
    with pytest.raises(address_obj._meta.model.DoesNotExist):
        address_obj.refresh_from_db()


def test_address_validator(user_api_client):
    query = """
    query getValidator($input: AddressValidationInput!) {
        addressValidator(input: $input) {
            countryCode
            countryName
            addressFormat
            addressLatinFormat
            postalCodeMatchers
        }
    }
    """
    variables = {
        'input': {
            'countryCode': 'PL',
            'countryArea': None,
            'cityArea': None}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['addressValidator']
    assert data['countryCode'] == 'PL'
    assert data['countryName'] == 'POLAND'
    assert data['addressFormat'] is not None
    assert data['addressLatinFormat'] is not None
    matcher = data['postalCodeMatchers'][0]
    matcher = re.compile(matcher)
    assert matcher.match('00-123')


def test_address_validator_uses_geip_when_country_code_missing(
        user_api_client, monkeypatch):
    query = """
    query getValidator($input: AddressValidationInput!) {
        addressValidator(input: $input) {
            countryCode,
            countryName
        }
    }
    """
    variables = {
        'input': {
            'countryCode': None,
            'countryArea': None,
            'cityArea': None}}
    mock_country_by_ip = Mock(return_value=Mock(code='US'))
    monkeypatch.setattr(
        'saleor.graphql.account.resolvers.get_client_ip',
        lambda request: Mock(return_value='127.0.0.1'))
    monkeypatch.setattr(
        'saleor.graphql.account.resolvers.get_country_by_ip',
        mock_country_by_ip)
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert mock_country_by_ip.called
    data = content['data']['addressValidator']
    assert data['countryCode'] == 'US'
    assert data['countryName'] == 'UNITED STATES'


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_customer_reset_password(
        send_password_reset_mock, user_api_client, customer_user):
    query = """
        mutation CustomerPasswordReset($email: String!) {
            customerPasswordReset(input: {email: $email}) {
                errors {
                    field
                    message
                }
            }
        }
    """
    # we have no user with given email
    variables = {'email': 'non-existing-email@email.com'}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert not send_password_reset_mock.called

    variables = {'email': customer_user.email}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert send_password_reset_mock.called
    assert send_password_reset_mock.mock_calls[0][1][1] == customer_user.email
