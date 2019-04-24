import json
import re
import uuid
from unittest.mock import MagicMock, Mock, patch

import graphene
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.files import File
from django.shortcuts import reverse
from freezegun import freeze_time
from prices import Money

from saleor.account.models import Address, User
from saleor.checkout import AddressType
from saleor.graphql.account.mutations import (
    CustomerDelete, SetPassword, StaffDelete, StaffUpdate, UserDelete)
from saleor.graphql.core.enums import PermissionEnum
from saleor.order.models import FulfillmentStatus, Order
from tests.api.utils import get_graphql_content
from tests.utils import create_image

from .utils import (
    assert_no_permission, convert_dict_keys_to_camel_case,
    get_multipart_request_body)


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
    variables = {'email': staff_user.email, 'password': 'password'}
    response = admin_client.post(
        reverse('api'),
        json.dumps({
            'query': query,
            'variables': variables}),
        content_type='application/json')
    content = get_graphql_content(response)
    token_data = content['data']['tokenCreate']
    assert token_data['token']
    assert token_data['errors'] == []

    incorrect_variables = {'email': staff_user.email, 'password': 'incorrect'}
    response = admin_client.post(
        reverse('api'),
        json.dumps({
            'query': query,
            'variables': incorrect_variables}),
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


def test_query_user(
        staff_api_client, customer_user, address, permission_manage_users,
        media_root):
    user = customer_user
    user.default_shipping_address.country = 'US'
    user.default_shipping_address.save()
    user.addresses.add(address.get_copy())

    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = 'image.jpg'
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
    assert data['orders']['totalCount'] == user.orders.count()
    assert data['avatar']['url']

    assert len(data['addresses']) == user.addresses.count()
    for address in data['addresses']:
        if address['isDefaultShippingAddress']:
            address_id = graphene.Node.to_global_id(
                'Address', user.default_shipping_address.id)
            assert address['id'] == address_id
        if address['isDefaultBillingAddress']:
            address_id = graphene.Node.to_global_id(
                'Address', user.default_billing_address.id)
            assert address['id'] == address_id

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
    assert address['isDefaultShippingAddress'] is None
    assert address['isDefaultBillingAddress'] is None

    address = data['defaultBillingAddress']
    user_address = user.default_billing_address
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
    assert address['isDefaultShippingAddress'] is None
    assert address['isDefaultBillingAddress'] is None


USER_QUERY = """
    query User($id: ID!) {
        user(id: $id) {
            email
        }
    }
"""


def test_customer_can_not_see_other_users_data(user_api_client, staff_user):
    id = graphene.Node.to_global_id('User', staff_user.id)
    variables = {'id': id}
    response = user_api_client.post_graphql(USER_QUERY, variables)
    assert_no_permission(response)


def test_user_query_anonymous_user(api_client):
    variables = {'id': ''}
    response = api_client.post_graphql(USER_QUERY, variables)
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
        staff_api_client, user_api_client, staff_user, admin_user,
        permission_manage_staff):
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
        staff_user, customer_user, staff_api_client, permission_manage_users):
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
            checkout {
                token
            }
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


def test_me_query_checkout(user_api_client, checkout):
    user = user_api_client.user
    checkout.user = user
    checkout.save()

    response = user_api_client.post_graphql(ME_QUERY)
    content = get_graphql_content(response)
    data = content['data']['me']
    assert data['checkout']['token'] == str(checkout.token)


def test_me_with_cancelled_fulfillments(
        user_api_client, fulfilled_order_with_cancelled_fulfillment):
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
        'Order', fulfilled_order_with_cancelled_fulfillment.id)
    data = content['data']['me']
    order = data['orders']['edges'][0]['node']
    assert order['id'] == order_id
    fulfillments = order['fulfillments']
    assert len(fulfillments) == 1
    assert fulfillments[0]['status'] == FulfillmentStatus.FULFILLED.upper()


def test_user_with_cancelled_fulfillments(
        staff_api_client, customer_user, permission_manage_users,
        fulfilled_order_with_cancelled_fulfillment):
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
    user_id = graphene.Node.to_global_id('User', customer_user.id)
    variables = {'id': user_id}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    order_id = graphene.Node.to_global_id(
        'Order', fulfilled_order_with_cancelled_fulfillment.id)
    data = content['data']['user']
    order = data['orders']['edges'][0]['node']
    assert order['id'] == order_id
    fulfillments = order['fulfillments']
    assert len(fulfillments) == 2
    assert fulfillments[0]['status'] == FulfillmentStatus.FULFILLED.upper()
    assert fulfillments[1]['status'] == FulfillmentStatus.CANCELED.upper()


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


@patch('saleor.dashboard.emails.send_set_password_customer_email.delay')
def test_customer_create(
        send_set_password_customer_email_mock, staff_api_client, address,
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

    shipping_address, billing_address = (
        customer.default_shipping_address, customer.default_billing_address)
    assert shipping_address == address
    assert billing_address == address
    assert shipping_address.pk != billing_address.pk

    data = content['data']['customerCreate']
    assert data['errors'] == []
    assert data['user']['email'] == email
    assert data['user']['firstName'] == first_name
    assert data['user']['lastName'] == last_name
    assert data['user']['note'] == note
    assert not data['user']['isStaff']
    assert data['user']['isActive']

    assert send_set_password_customer_email_mock.call_count == 1
    args, kwargs = send_set_password_customer_email_mock.call_args
    call_pk = args[0]
    assert call_pk == customer.pk


def test_customer_update(
        staff_api_client, customer_user, address, permission_manage_users):
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
    shipping_address, billing_address = (
        customer.default_shipping_address, customer.default_billing_address)
    assert billing_address.pk == billing_address_pk
    assert shipping_address.pk == shipping_address_pk

    assert billing_address.street_address_1 == new_street_address
    assert shipping_address.street_address_1 == new_street_address

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
    response = api_client.post_graphql(UPDATE_LOGGED_CUSTOMER_QUERY, {})
    assert_no_permission(response)


def test_customer_delete(
        staff_api_client, customer_user, permission_manage_users):
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
    with pytest.raises(ValidationError) as e:
        CustomerDelete.clean_instance(info, staff_user)

    msg = 'Cannot delete a staff account.'
    assert e.value.error_dict['id'][0].message == msg

    # shuold not raise any errors
    CustomerDelete.clean_instance(info, customer_user)


@patch('saleor.dashboard.emails.send_set_password_staff_email.delay')
def test_staff_create(
        send_set_password_staff_email_mock, staff_api_client, media_root,
        permission_manage_staff):
    query = """
    mutation CreateStaff(
            $email: String, $permissions: [PermissionEnum],
            $send_mail: Boolean) {
        staffCreate(input: {email: $email, permissions: $permissions,
                sendPasswordEmail: $send_mail}) {
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
                avatar {
                    url
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
    assert data['user']['isStaff']
    assert data['user']['isActive']
    assert re.match(
        r'http://testserver/media/user-avatars/avatar\d+.*',
        data['user']['avatar']['url']
    )
    permissions = data['user']['permissions']
    assert permissions[0]['code'] == 'MANAGE_PRODUCTS'

    User = get_user_model()
    staff_user = User.objects.get(email=email)

    assert staff_user.is_staff

    assert send_set_password_staff_email_mock.call_count == 1
    args, kwargs = send_set_password_staff_email_mock.call_args
    call_pk = args[0]
    assert call_pk == staff_user.pk


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
    assert not data['user']['isActive']


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


def test_user_delete_errors(staff_user, admin_user):
    info = Mock(context=Mock(user=staff_user))
    with pytest.raises(ValidationError) as e:
        UserDelete.clean_instance(info, staff_user)

    msg = 'You cannot delete your own account.'
    assert e.value.error_dict['id'][0].message == msg

    info = Mock(context=Mock(user=staff_user))
    with pytest.raises(ValidationError) as e:
        UserDelete.clean_instance(info, admin_user)

    msg = 'Cannot delete this account.'
    assert e.value.error_dict['id'][0].message == msg


def test_staff_delete_errors(staff_user, customer_user, admin_user):
    info = Mock(context=Mock(user=staff_user))
    with pytest.raises(ValidationError) as e:
        StaffDelete.clean_instance(info, customer_user)
    msg = 'Cannot delete a non-staff user.'
    assert e.value.error_dict['id'][0].message == msg

    # shuold not raise any errors
    info = Mock(context=Mock(user=admin_user))
    StaffDelete.clean_instance(info, staff_user)


def test_staff_update_errors(staff_user, customer_user, admin_user):
    StaffUpdate.clean_is_active(None, customer_user, staff_user)

    with pytest.raises(ValidationError) as e:
        StaffUpdate.clean_is_active(False, staff_user, staff_user)
    msg = 'Cannot deactivate your own account.'
    assert e.value.error_dict['is_active'][0].message == msg

    with pytest.raises(ValidationError) as e:
        StaffUpdate.clean_is_active(False, admin_user, staff_user)
    msg = 'Cannot deactivate superuser\'s account.'
    assert e.value.error_dict['is_active'][0].message == msg

    # shuold not raise any errors
    StaffUpdate.clean_is_active(False, customer_user, staff_user)


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
    assert data == {'errors': []}
    assert send_password_reset_mock.call_count == 1
    args, kwargs = send_password_reset_mock.call_args
    call_context = args[0]
    call_email = args[1]
    assert call_email == email
    assert 'token' in call_context


@patch('saleor.account.emails.send_password_reset_email.delay')
def test_password_reset_email_non_existing_user(
        send_password_reset_mock, staff_api_client, permission_manage_users):
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
    user_id = graphene.Node.to_global_id('User', customer_user.id)
    variables = {'user': user_id, 'city': 'Dummy', 'country': 'PL'}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    assert content['data']['addressCreate']['errors'] == []
    data = content['data']['addressCreate']
    assert data['address']['city'] == 'Dummy'
    assert data['address']['country']['code'] == 'PL'
    address_obj = Address.objects.get(city='Dummy')
    assert address_obj.user_addresses.first() == customer_user
    assert data['user']['id'] == user_id


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
        staff_api_client, customer_user, permission_manage_users,
        graphql_address_data):
    query = ADDRESS_UPDATE_MUTATION
    address_obj = customer_user.addresses.first()
    assert staff_api_client.user not in address_obj.user_addresses.all()
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


def test_customer_update_own_address(
        user_api_client, customer_user, graphql_address_data):
    query = ADDRESS_UPDATE_MUTATION
    address_obj = customer_user.addresses.first()
    address_data = graphql_address_data
    address_data['city'] = 'Poznań'
    assert address_data['city'] != address_obj.city

    variables = {
        'addressId': graphene.Node.to_global_id('Address', address_obj.id),
        'address': address_data}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['addressUpdate']
    assert data['address']['city'] == address_data['city']
    address_obj.refresh_from_db()
    assert address_obj.city == address_data['city']


def test_customer_update_address_for_other(
        user_api_client, customer_user, address_other_country,
        graphql_address_data):
    query = ADDRESS_UPDATE_MUTATION
    address_obj = address_other_country
    assert customer_user not in address_obj.user_addresses.all()

    address_data = graphql_address_data
    variables = {
        'addressId': graphene.Node.to_global_id('Address', address_obj.id),
        'address': address_data}
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
        staff_api_client, customer_user, permission_manage_users):
    query = ADDRESS_DELETE_MUTATION
    address_obj = customer_user.addresses.first()
    variables = {'id': graphene.Node.to_global_id('Address', address_obj.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['addressDelete']
    assert data['address']['city'] == address_obj.city
    assert data['user']['id'] == graphene.Node.to_global_id(
        'User', customer_user.pk)
    with pytest.raises(address_obj._meta.model.DoesNotExist):
        address_obj.refresh_from_db()


def test_customer_delete_own_address(user_api_client, customer_user):
    query = ADDRESS_DELETE_MUTATION
    address_obj = customer_user.addresses.first()
    variables = {'id': graphene.Node.to_global_id('Address', address_obj.id)}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['addressDelete']
    assert data['address']['city'] == address_obj.city
    with pytest.raises(address_obj._meta.model.DoesNotExist):
        address_obj.refresh_from_db()


def test_customer_delete_address_for_other(
        user_api_client, customer_user, address_other_country):
    query = ADDRESS_DELETE_MUTATION
    address_obj = address_other_country
    assert customer_user not in address_obj.user_addresses.all()
    variables = {'id': graphene.Node.to_global_id('Address', address_obj.id)}
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
        staff_api_client, address_other_country, customer_user,
        permission_manage_users):
    customer_user.default_billing_address = None
    customer_user.default_shipping_address = None
    customer_user.save()

    # try to set an address that doesn't belong to that user
    address = address_other_country

    variables = {
        'address_id': graphene.Node.to_global_id('Address', address.id),
        'user_id': graphene.Node.to_global_id('User', customer_user.id),
        'type': AddressType.SHIPPING.upper()}

    response = staff_api_client.post_graphql(
        SET_DEFAULT_ADDRESS_MUTATION, variables,
        permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['addressSetDefault']
    assert data['errors'][0]['field'] == 'addressId'

    # try to set a new billing address using one of user's addresses
    address = customer_user.addresses.first()
    address_id = graphene.Node.to_global_id('Address', address.id)

    variables['address_id'] = address_id
    response = staff_api_client.post_graphql(
        SET_DEFAULT_ADDRESS_MUTATION, variables)
    content = get_graphql_content(response)
    data = content['data']['addressSetDefault']
    assert data['user']['defaultShippingAddress']['id'] == address_id


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


def test_address_validator_with_country_area(user_api_client):
    query = """
    query getValidator($input: AddressValidationInput!) {
        addressValidator(input: $input) {
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
        'input': {
            'countryCode': 'CN',
            'countryArea': 'Fujian Sheng',
            'cityArea': None}}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['addressValidator']
    assert data['countryCode'] == 'CN'
    assert data['countryName'] == 'CHINA'
    assert data['countryAreaType'] == 'province'
    assert data['countryAreaChoices']
    assert data['cityType'] == 'city'
    assert data['cityChoices']
    assert data['cityAreaType'] == 'city'
    assert not data['cityAreaChoices']


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
    get_graphql_content(response)
    assert not send_password_reset_mock.called

    variables = {'email': customer_user.email}
    response = user_api_client.post_graphql(query, variables)
    get_graphql_content(response)
    assert send_password_reset_mock.called
    assert send_password_reset_mock.mock_calls[0][1][1] == customer_user.email


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


def test_customer_create_address(user_api_client, graphql_address_data):
    user = user_api_client.user
    nr_of_addresses = user.addresses.count()

    query = CUSTOMER_ADDRESS_CREATE_MUTATION
    variables = {'addressInput': graphql_address_data}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['customerAddressCreate']

    assert data['address']['city'] == graphql_address_data['city']

    user.refresh_from_db()
    assert user.addresses.count() == nr_of_addresses + 1


def test_customer_create_default_address(
        user_api_client, graphql_address_data):
    user = user_api_client.user
    nr_of_addresses = user.addresses.count()

    query = CUSTOMER_ADDRESS_CREATE_MUTATION
    address_type = AddressType.SHIPPING.upper()
    variables = {
        'addressInput': graphql_address_data, 'addressType': address_type}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['customerAddressCreate']
    assert data['address']['city'] == graphql_address_data['city']

    user.refresh_from_db()
    assert user.addresses.count() == nr_of_addresses + 1
    assert user.default_shipping_address.id == int(
        graphene.Node.from_global_id(data['address']['id'])[1])

    address_type = AddressType.BILLING.upper()
    variables = {
        'addressInput': graphql_address_data, 'addressType': address_type}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['customerAddressCreate']
    assert data['address']['city'] == graphql_address_data['city']

    user.refresh_from_db()
    assert user.addresses.count() == nr_of_addresses + 2
    assert user.default_billing_address.id == int(
        graphene.Node.from_global_id(data['address']['id'])[1])


def test_anonymous_user_create_address(api_client, graphql_address_data):
    query = CUSTOMER_ADDRESS_CREATE_MUTATION
    variables = {'addressInput': graphql_address_data}
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


def test_customer_set_address_as_default(user_api_client, address):
    user = user_api_client.user
    user.default_billing_address = None
    user.default_shipping_address = None
    user.save()
    assert not user.default_billing_address
    assert not user.default_shipping_address

    assert address in user.addresses.all()

    query = CUSTOMER_SET_DEFAULT_ADDRESS_MUTATION
    variables = {
        'id': graphene.Node.to_global_id('Address', address.id),
        'type': AddressType.SHIPPING.upper()}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['customerSetDefaultAddress']
    assert not data['errors']

    user.refresh_from_db()
    assert user.default_shipping_address == address

    variables['type'] = AddressType.BILLING.upper()
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['customerSetDefaultAddress']
    assert not data['errors']

    user.refresh_from_db()
    assert user.default_billing_address == address


def test_customer_change_default_address(
        user_api_client, address_other_country):
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

    query = CUSTOMER_SET_DEFAULT_ADDRESS_MUTATION
    variables = {
        'id': graphene.Node.to_global_id('Address', address.id),
        'type': AddressType.SHIPPING.upper()}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    data = content['data']['customerSetDefaultAddress']
    assert not data['errors']

    user.refresh_from_db()
    assert user.default_shipping_address == address
    assert address_other_country in user.addresses.all()


def test_customer_change_default_address_invalid_address(
        user_api_client, address_other_country):
    user = user_api_client.user
    assert address_other_country not in user.addresses.all()

    query = CUSTOMER_SET_DEFAULT_ADDRESS_MUTATION
    variables = {
        'id': graphene.Node.to_global_id('Address', address_other_country.id),
        'type': AddressType.SHIPPING.upper()}
    response = user_api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert (
            content['data']['customerSetDefaultAddress']['errors'][0][
                'field'] ==
            'id')


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

    image_file, image_name = create_image('avatar')
    variables = {'image': image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = api_client.post_multipart(body)

    assert_no_permission(response)


def test_user_avatar_update_mutation(
        monkeypatch, staff_api_client, media_root):
    query = USER_AVATAR_UPDATE_MUTATION

    user = staff_api_client.user

    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        ('saleor.graphql.account.mutations.'
         'create_user_avatar_thumbnails.delay'),
        mock_create_thumbnails)

    image_file, image_name = create_image('avatar')
    variables = {'image': image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)

    data = content['data']['userAvatarUpdate']
    user.refresh_from_db()

    assert user.avatar
    assert data['user']['avatar']['url'].startswith(
        'http://testserver/media/user-avatars/avatar'
    )

    # The image creation should have triggered a warm-up
    mock_create_thumbnails.assert_called_once_with(user_id=user.pk)


def test_user_avatar_update_mutation_image_exists(
        staff_api_client, media_root):
    query = USER_AVATAR_UPDATE_MUTATION

    user = staff_api_client.user
    avatar_mock = MagicMock(spec=File)
    avatar_mock.name = 'image.jpg'
    user.avatar = avatar_mock
    user.save()

    image_file, image_name = create_image('new_image')
    variables = {'image': image_name}
    body = get_multipart_request_body(query, variables, image_file, image_name)
    response = staff_api_client.post_multipart(body)
    content = get_graphql_content(response)

    data = content['data']['userAvatarUpdate']
    user.refresh_from_db()

    assert user.avatar != avatar_mock
    assert data['user']['avatar']['url'].startswith(
        'http://testserver/media/user-avatars/new_image'
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
    assert not content['data']['userAvatarDelete']['user']['avatar']


@pytest.mark.parametrize('customer_filter, count', [
    ({'placedOrders': {'gte': '2019-04-18'}}, 1),
    ({'placedOrders': {'lte': '2012-01-14'}}, 1),
    ({'placedOrders': {'lte': '2012-01-14', 'gte': '2012-01-13'}}, 1),
    ({'placedOrders': {'gte': '2012-01-14'}}, 2),

])
def test_query_customers_with_filter_placed_orders(
        customer_filter, count, query_customer_with_filter, staff_api_client,
        permission_manage_users, customer_user):
    Order.objects.create(user=customer_user)
    second_customer = User.objects.create(email='second_example@example.com')
    with freeze_time("2012-01-14 11:00:00"):
        o = Order.objects.create(user=second_customer)
    variables = {'filter': customer_filter}
    response = staff_api_client.post_graphql(
            query_customer_with_filter, variables,
            permissions=[permission_manage_users])
    content = get_graphql_content(response)
    users = content['data']['customers']['edges']

    assert len(users) == count


@pytest.mark.parametrize('customer_filter, count', [
    ({'dateJoined': {'gte': '2019-04-18'}}, 1),
    ({'dateJoined': {'lte': '2012-01-14'}}, 1),
    ({'dateJoined': {'lte': '2012-01-14', 'gte': '2012-01-13'}},
     1),
    ({'dateJoined': {'gte': '2012-01-14'}}, 2),

])
def test_query_customers_with_filter_date_joined(
        customer_filter, count, query_customer_with_filter,
        staff_api_client,
        permission_manage_users, customer_user):
    with freeze_time("2012-01-14 11:00:00"):
        User.objects.create(
            email='second_example@example.com')
    variables = {'filter': customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables,
        permissions=[permission_manage_users])
    content = get_graphql_content(response)
    users = content['data']['customers']['edges']

    assert len(users) == count


@pytest.mark.parametrize('customer_filter, count', [
    ({'numberOfOrders': {"gte": 0, "lte": 1}}, 1),
    ({'numberOfOrders': {"gte": 1, "lte": 3}}, 2),
    ({'numberOfOrders': {"gte": 0}}, 2),
    ({'numberOfOrders': {"lte": 3}}, 2),

])
def test_query_customers_with_filter_placed_orders(
        customer_filter, count, query_customer_with_filter, staff_api_client,
        permission_manage_users, customer_user):
    Order.objects.bulk_create([
        Order(user=customer_user, token=str(uuid.uuid4())),
        Order(user=customer_user, token=str(uuid.uuid4())),
        Order(user=customer_user, token=str(uuid.uuid4()))
    ])
    second_customer = User.objects.create(email='second_example@example.com')
    with freeze_time("2012-01-14 11:00:00"):
        Order.objects.create(user=second_customer)
    variables = {'filter': customer_filter}
    response = staff_api_client.post_graphql(
            query_customer_with_filter, variables,
            permissions=[permission_manage_users])
    content = get_graphql_content(response)
    users = content['data']['customers']['edges']

    assert len(users) == count


@pytest.mark.parametrize('customer_filter, count', [
    ({'moneySpent': {"gte": 16, "lte": 25}}, 1),
    ({'moneySpent': {"gte": 15, "lte": 26}}, 2),
    ({'moneySpent': {"gte": 0}}, 2),
    ({'moneySpent': {"lte": 16}}, 1),

])
def test_query_customers_with_filter_placed_orders(
        customer_filter, count, query_customer_with_filter, staff_api_client,
        permission_manage_users, customer_user):
    second_customer = User.objects.create(email='second_example@example.com')
    Order.objects.bulk_create([
        Order(
            user=customer_user, token=str(uuid.uuid4()),
            total_gross=Money(15, 'USD')),
        Order(
            user=second_customer, token=str(uuid.uuid4()),
            total_gross=Money(25, 'USD'))
    ])

    variables = {'filter': customer_filter}
    response = staff_api_client.post_graphql(
            query_customer_with_filter, variables,
            permissions=[permission_manage_users])
    content = get_graphql_content(response)
    users = content['data']['customers']['edges']

    assert len(users) == count


@pytest.mark.parametrize('customer_filter, count', [
    ({'search': 'example.com'}, 2), ({'search': 'Alice'}, 1),
    ({'search': 'Kowalski'}, 1),
    ({'search': 'John'}, 1),  # default_shipping_address__first_name
    ({'search': 'Doe'}, 1),  # default_shipping_address__last_name
    ({'search': 'wroc'}, 1),  # default_shipping_address__city
    ({'search': 'pl'}, 2),  # default_shipping_address__country, email
])
def test_query_customer_memebers_with_filter_search(
        customer_filter, count, query_customer_with_filter,
        staff_api_client, permission_manage_users, address, staff_user):

    User.objects.bulk_create([
        User(email='second@example.com', first_name='Alice',
             last_name='Kowalski', is_active=False),
        User(
            email='third@example.com', is_active=True,
            default_shipping_address=address)
    ])

    variables = {'filter': customer_filter}
    response = staff_api_client.post_graphql(
            query_customer_with_filter, variables,
            permissions=[permission_manage_users])
    content = get_graphql_content(response)
    users = content['data']['customers']['edges']

    assert len(users) == count


@pytest.mark.parametrize('staff_member_filter, count', [
    ({'status': 'DEACTIVATED'}, 1),
    ({'status': 'ACTIVE'}, 2),
])
def test_query_staff_memebers_with_filter_status(
        staff_member_filter, count, query_staff_users_with_filter,
        staff_api_client, permission_manage_staff, staff_user):

    User.objects.bulk_create([
        User(email='second@example.com', is_staff=True, is_active=False),
        User(email='third@example.com', is_staff=True, is_active=True)
    ])

    variables = {'filter': staff_member_filter}
    response = staff_api_client.post_graphql(
            query_staff_users_with_filter, variables,
            permissions=[permission_manage_staff])
    content = get_graphql_content(response)
    users = content['data']['staffUsers']['edges']

    assert len(users) == count


@pytest.mark.parametrize('staff_member_filter, count', [
    ({'search': 'example.com'}, 3), ({'search': 'Alice'}, 1),
    ({'search': 'Kowalski'}, 1),
    ({'search': 'John'}, 1),  # default_shipping_address__first_name
    ({'search': 'Doe'}, 1),  # default_shipping_address__last_name
    ({'search': 'wroc'}, 1),  # default_shipping_address__city
    ({'search': 'pl'}, 3),  # default_shipping_address__country, email
])
def test_query_staff_memebers_with_filter_search(
        staff_member_filter, count, query_staff_users_with_filter,
        staff_api_client, permission_manage_staff, address, staff_user):

    User.objects.bulk_create([
        User(email='second@example.com', first_name='Alice',
             last_name='Kowalski', is_staff=True, is_active=False),
        User(
            email='third@example.com', is_staff=True, is_active=True,
            default_shipping_address=address),
        User(email='customer@example.com', first_name='Alice',
             last_name='Kowalski', is_staff=False, is_active=True),
    ])

    variables = {'filter': staff_member_filter}
    response = staff_api_client.post_graphql(
            query_staff_users_with_filter, variables,
            permissions=[permission_manage_staff])
    content = get_graphql_content(response)
    users = content['data']['staffUsers']['edges']

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
        staff_api_client, user_list_not_active, permission_manage_users):
    users = user_list_not_active
    active_status = True
    variables = {
        'ids': [
            graphene.Node.to_global_id('User', user.id)
            for user in users],
        'is_active': active_status}
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION, variables,
        permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['userBulkSetActive']
    assert data['count'] == users.count()
    users = User.objects.filter(pk__in=[user.pk for user in users])
    assert all(user.is_active for user in users)


def test_staff_bulk_set_not_active(
        staff_api_client, user_list, permission_manage_users):
    users = user_list
    active_status = False
    variables = {
        'ids': [
            graphene.Node.to_global_id('User', user.id)
            for user in users],
        'is_active': active_status}
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION, variables,
        permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['userBulkSetActive']
    assert data['count'] == len(users)
    users = User.objects.filter(pk__in=[user.pk for user in users])
    assert not any(user.is_active for user in users)


def test_change_active_status_for_superuser(
        staff_api_client, superuser, permission_manage_users):
    users = [superuser]
    superuser_id = graphene.Node.to_global_id('User', superuser.id)
    active_status = False
    variables = {
        'ids': [
            graphene.Node.to_global_id('User', user.id)
            for user in users],
        'is_active': active_status}
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION, variables,
        permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['userBulkSetActive']
    assert data['errors'][0]['field'] == superuser_id
    assert data['errors'][0]['message'] == 'Cannot activate or deactivate ' \
                                           'superuser\'s account.'


def test_change_active_status_for_himself(
        staff_api_client, permission_manage_users):
    users = [staff_api_client.user]
    user_id = graphene.Node.to_global_id('User', staff_api_client.user.id)
    active_status = False
    variables = {
        'ids': [
            graphene.Node.to_global_id('User', user.id)
            for user in users],
        'is_active': active_status}
    response = staff_api_client.post_graphql(
        USER_CHANGE_ACTIVE_STATUS_MUTATION, variables,
        permissions=[permission_manage_users])
    content = get_graphql_content(response)
    data = content['data']['userBulkSetActive']
    assert data['errors'][0]['field'] == user_id
    assert data['errors'][0]['message'] == 'Cannot activate or deactivate ' \
                                           'your own account.'
