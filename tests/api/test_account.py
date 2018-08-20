import json
from unittest.mock import patch

import graphene
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import reverse
from tests.utils import get_graphql_content

from saleor.account.models import Address
from saleor.graphql.account.mutations import SetPassword

from .utils import assert_no_permission, convert_dict_keys_to_camel_case


def test_create_token_mutation(admin_client, staff_user):
    query = '''
    mutation {
        tokenCreate(email: "%(email)s", password: "%(password)s") {
            token
            errors {
                field
                message
            }
        }
    }
    '''
    success_query = query % {'email': staff_user.email, 'password': 'password'}
    response = admin_client.post(
        reverse('api'), json.dumps({'query': success_query}),
        content_type='application/json')
    content = get_graphql_content(response)
    assert 'errors' not in content
    token_data = content['data']['tokenCreate']
    assert token_data['token']
    assert not token_data['errors']

    error_query = query % {'email': staff_user.email, 'password': 'wat'}
    response = admin_client.post(
        reverse('api'), json.dumps({'query': error_query}),
        content_type='application/json')
    content = get_graphql_content(response)
    assert 'errors' not in content
    token_data = content['data']['tokenCreate']
    assert not token_data['token']
    errors = token_data['errors']
    assert errors
    assert not errors[0]['field']


def test_token_create_user_data(
        permission_manage_orders, staff_client, staff_user):
    query = """
    mutation {
        tokenCreate(email: "%(email)s", password: "%(password)s") {
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
    code = '.'.join([permission.content_type.name, permission.codename])
    name = permission.name
    user_id = graphene.Node.to_global_id('User', staff_user.id)

    query = query % {'email': staff_user.email, 'password': 'password'}
    response = staff_client.post(
        reverse('api'), json.dumps({'query': query}),
        content_type='application/json')
    content = get_graphql_content(response)
    assert 'errors' not in content
    token_data = content['data']['tokenCreate']
    assert token_data['user']['id'] == user_id
    assert token_data['user']['email'] == staff_user.email
    assert token_data['user']['permissions'][0]['name'] == name
    assert token_data['user']['permissions'][0]['code'] == code


def test_query_user(admin_api_client, customer_user):
    user = customer_user
    query = """
    query User($id: ID!) {
        user(id: $id) {
            email
            isStaff
            isActive
            addresses {
                totalCount
            }
            orders {
                totalCount
            }
            defaultShippingAddress {
                firstName
                lastName
                companyName
                streetAddress1
                streetAddress2
                city
                cityArea
                postalCode
                country
                countryArea
                phone
            }
        }
    }
    """
    ID = graphene.Node.to_global_id('User', customer_user.id)
    variables = json.dumps({'id': ID})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['user']
    assert data['email'] == user.email
    assert data['isStaff'] == user.is_staff
    assert data['isActive'] == user.is_active
    assert data['addresses']['totalCount'] == user.addresses.count()
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
    assert address['country'] == user_address.country.code
    assert address['countryArea'] == user_address.country_area
    assert address['phone'] == user_address.phone.as_e164


def test_query_users(admin_api_client, user_api_client):
    query = """
    query Users($isStaff: Boolean) {
        users(isStaff: $isStaff) {
            totalCount
            edges {
                node {
                    isStaff
                }
            }
        }
    }
    """
    variables = json.dumps({'isStaff': True})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    users = content['data']['users']['edges']
    assert users
    assert all([user['node']['isStaff'] for user in users])

    variables = json.dumps({'isStaff': False})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    users = content['data']['users']['edges']
    assert users
    assert all([not user['node']['isStaff'] for user in users])

    # check permissions
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)


def test_who_can_see_user(
        staff_user, customer_user, staff_api_client, user_api_client,
        permission_manage_users):
    query = """
    query User($id: ID!) {
        user(id: $id) {
            email
        }
    }
    """

    query_2 = """
    query Users {
        users {
            totalCount
        }
    }
    """

    # Random person (even staff) can't see users data without permissions
    ID = graphene.Node.to_global_id('User', customer_user.id)
    variables = json.dumps({'id': ID})
    response = staff_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert content['data']['user'] is None

    response = staff_api_client.post(
        reverse('api'), {'query': query_2})
    assert_no_permission(response)

    # Add permission and ensure staff can see user(s)
    staff_user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert content['data']['user']['email'] == customer_user.email

    response = staff_api_client.post(reverse('api'), {'query': query_2})
    content = get_graphql_content(response)
    model = get_user_model()
    assert content['data']['users']['totalCount'] == model.objects.count()


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_customer_create(
        send_password_reset_mock, admin_api_client, user_api_client, address):
    query = """
    mutation CreateCustomer(
        $email: String, $note: String, $billing: AddressInput,
        $shipping: AddressInput, $send_mail: Boolean) {
        customerCreate(input: {
            email: $email,
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
                isActive
                isStaff
                note
            }
        }
    }
    """
    email = 'api_user@example.com'
    note = 'Test user'
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    variables = json.dumps(
        {'email': email, 'note': note, 'shipping': address_data,
        'billing': address_data, 'send_mail': True})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)

    User = get_user_model()
    customer = User.objects.get(email=email)

    assert customer.default_billing_address == address
    assert customer.default_shipping_address == address
    assert customer.default_shipping_address.pk != customer.default_billing_address.pk

    assert 'errors' not in content
    data = content['data']['customerCreate']
    assert data['errors'] == []
    assert data['user']['email'] == email
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
        admin_api_client, customer_user, user_api_client, address):
    query = """
    mutation UpdateCustomer($id: ID!, $note: String, $billing: AddressInput, $shipping: AddressInput) {
        customerUpdate(id: $id, input: {
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
                note
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

    # this test requires addresses to be set and checks whether new address
    # instances weren't created, but the existing ones got updated
    assert customer_user.default_billing_address
    assert customer_user.default_shipping_address
    billing_address_pk = customer_user.default_billing_address.pk
    shipping_address_pk = customer_user.default_shipping_address.pk

    id = graphene.Node.to_global_id('User', customer_user.id)
    note = 'Test update note'
    address_data = convert_dict_keys_to_camel_case(address.as_data())

    new_street_address = 'Updated street address'
    address_data['streetAddress1'] = new_street_address

    variables = json.dumps({
        'id': id, 'note': note, 'billing': address_data,
        'shipping': address_data})

    # check unauthorized access
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)

    User = get_user_model()
    customer = User.objects.get(email=customer_user.email)

    # check that existing instances are updated
    assert customer.default_billing_address.pk == billing_address_pk
    assert customer.default_shipping_address.pk == shipping_address_pk

    assert customer.default_billing_address.street_address_1 == new_street_address
    assert customer.default_shipping_address.street_address_1 == new_street_address

    assert 'errors' not in content
    data = content['data']['customerUpdate']
    assert data['errors'] == []
    assert data['user']['note'] == note


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_staff_create(
        send_password_reset_mock, admin_api_client, user_api_client,
        permission_manage_users, permission_manage_products, staff_user):
    query = """
    mutation CreateStaff($email: String, $permissions: [String], $send_mail: Boolean) {
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

    permission_manage_products_codename = '%s.%s' % (
        permission_manage_products.content_type.app_label,
        permission_manage_products.codename)

    email = 'api_user@example.com'
    staff_user.user_permissions.add(permission_manage_users)
    variables = json.dumps({
        'email': email, 'permissions': [permission_manage_products_codename],
        'send_mail': True})

    # check unauthorized access
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['staffCreate']
    assert data['errors'] == []
    assert data['user']['email'] == email
    assert data['user']['isStaff'] == True
    assert data['user']['isActive'] == True
    permissions = data['user']['permissions']
    assert permissions[0]['code'] == permission_manage_products_codename

    assert send_password_reset_mock.call_count == 1
    args, kwargs = send_password_reset_mock.call_args
    call_context = args[0]
    call_email = args[1]
    assert call_email == email
    assert 'token' in call_context


def test_staff_update(admin_api_client, staff_user, user_api_client):
    query = """
    mutation UpdateStaff($id: ID!, $permissions: [String]) {
        staffUpdate(id: $id, input: {permissions: $permissions}) {
            errors {
                field
                message
            }
            user {
                permissions {
                    code
                }
            }
        }
    }
    """
    id = graphene.Node.to_global_id('User', staff_user.id)
    variables = json.dumps({'id': id, 'permissions': []})

    # check unauthorized access
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['staffUpdate']
    assert data['errors'] == []
    assert data['user']['permissions'] == []


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

    variables = {'id': id, 'password': password}

    # check invalid token
    variables['token'] = 'nope'
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': json.dumps(variables)})
    content = get_graphql_content(response)
    errors = content['data']['setPassword']['errors']
    assert errors[0]['message'] == SetPassword.INVALID_TOKEN

    variables['token'] = token
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': json.dumps(variables)})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['setPassword']
    assert data['user']['id']

    customer_user.refresh_from_db()
    assert customer_user.check_password(password)


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_password_reset_email(
        send_password_reset_mock, admin_api_client, customer_user):
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
    variables = json.dumps({'email': email})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
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
        send_password_reset_mock, admin_api_client, customer_user):
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
    variables = json.dumps({'email': email})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['passwordReset']
    assert data['errors'] == [{
        'field': 'email', 'message': "User with this email doesn't exist"}]
    send_password_reset_mock.assert_not_called()


def test_create_address_mutation(admin_api_client, customer_user):
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
            country
         }
        }
    }
    """
    user_id = graphene.Node.to_global_id('User', customer_user.id)
    variables = json.dumps(
        {'user': user_id, 'city': 'Dummy', 'country': 'PL'})
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert content['data']['addressCreate']['errors'] == []
    address_response = content['data']['addressCreate']['address']
    assert address_response['city'] == 'Dummy'
    assert address_response['country'] == 'PL'
    address_obj = Address.objects.get(city='Dummy')
    assert address_obj.user_addresses.first() == customer_user


def test_address_update_mutation(admin_api_client, customer_user):
    query = """
    mutation updateUserAddress($addressId: ID!, $city: String!) {
        addressUpdate(id: $addressId, input: {city: $city}) {
            address {
                city
            }
        }
    }
    """
    address_obj = customer_user.addresses.first()
    new_city = 'Dummy'
    variables = {
        'addressId': graphene.Node.to_global_id('Address', address_obj.id),
        'city': new_city}
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['addressUpdate']
    assert data['address']['city'] == new_city
    address_obj.refresh_from_db()
    assert address_obj.city == new_city


def test_address_delete_mutation(admin_api_client, customer_user):
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
    variables = {
        'id': graphene.Node.to_global_id('Address', address_obj.id)}
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['addressDelete']
    assert data['address']['city'] == address_obj.city
    with pytest.raises(address_obj._meta.model.DoesNotExist):
        address_obj.refresh_from_db()
