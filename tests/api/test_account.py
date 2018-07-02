import json
from django.contrib.auth.tokens import default_token_generator

import graphene
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from tests.utils import get_graphql_content
from .utils import assert_no_permission

from saleor.graphql.account.mutations import SetPassword


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
        permission_view_order, staff_client, staff_group, staff_user):
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

    permission = permission_view_order
    staff_group.permissions.add(permission)
    staff_user.groups.add(staff_group)
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
    assert address['phone'] == user_address.phone.raw_input


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
        staff_group, permission_view_user):
    user = customer_user
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
    staff_group.permissions.add(permission_view_user)
    staff_user.groups.add(staff_group)
    response = staff_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert content['data']['user']['email'] == customer_user.email

    response = staff_api_client.post(reverse('api'), {'query': query_2})
    content = get_graphql_content(response)
    model = get_user_model()
    assert content['data']['users']['totalCount'] == model.objects.count()


def test_customer_create(admin_api_client, user_api_client):
    query = """
    mutation CreateCustomer($email: String, $note: String) {
        customerCreate(input: {email: $email, note: $note}) {
            errors {
                field
                message
            }
            user {
                id
                email
                isStaff
                isActive
                note
            }
        }
    }
    """
    email = 'api_user@example.com'
    note = 'Test user'

    variables = json.dumps({'email': email, 'note': note})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['customerCreate']
    assert data['errors'] == []
    assert data['user']['email'] == email
    assert data['user']['note'] == note
    assert data['user']['isStaff'] == False
    assert data['user']['isActive'] == True


def test_customer_update(admin_api_client, customer_user, user_api_client):
    query = """
    mutation UpdateCustomer($id: ID!, $note: String) {
        customerUpdate(id: $id, input: {note: $note}) {
            errors {
                field
                message
            }
            user {
                id
                email
                isStaff
                isActive
                note
            }
        }
    }
    """

    id = graphene.Node.to_global_id('User', customer_user.id)
    note = 'Test update note'
    variables = json.dumps({'id': id, 'note': note})

    # check unauthorized access
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['customerUpdate']
    assert data['errors'] == []
    assert data['user']['note'] == note


def test_staff_create(
        admin_api_client, user_api_client, staff_group, permission_view_user,
        permission_view_product):
    query = """
    mutation CreateStaff($email: String, $permissions: [String], $groups: [ID]) {
        staffCreate(input: {email: $email, permissions: $permissions, groups: $groups}) {
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
                groups {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        }
    }
    """

    permission_view_user_codename = '%s.%s' % (
        permission_view_user.content_type.app_label,
        permission_view_user.codename)
    permission_view_product_codename = '%s.%s' % (
        permission_view_product.content_type.app_label,
        permission_view_product.codename)

    email = 'api_user@example.com'
    staff_group.permissions.add(permission_view_user)
    group_id = graphene.Node.to_global_id('Group', staff_group.id)

    variables = json.dumps({
        'email': email, 'groups': [group_id],
        'permissions': [permission_view_product_codename]})

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
    assert permissions[0]['code'] == permission_view_user_codename
    assert permissions[1]['code'] == permission_view_product_codename
    groups = data['user']['groups']['edges']
    assert len(groups) == 1
    assert groups[0]['node']['name'] == staff_group.name


def test_staff_update(admin_api_client, staff_user, user_api_client):
    query = """
    mutation UpdateStaff($id: ID!, $permissions: [String], $groups: [ID]) {
        staffUpdate(id: $id, input: {permissions: $permissions, groups: $groups}) {
            errors {
                field
                message
            }
            user {
                permissions {
                    code
                }
                groups {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
    }
    """
    id = graphene.Node.to_global_id('User', staff_user.id)
    variables = json.dumps({'id': id, 'permissions': [], 'groups': []})

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
    assert data['user']['groups']['edges'] == []


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
