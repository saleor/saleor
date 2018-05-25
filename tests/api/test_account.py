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
