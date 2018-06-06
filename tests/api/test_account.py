import json

import graphene
from django.shortcuts import reverse
from tests.utils import get_graphql_content


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
