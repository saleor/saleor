import json

import graphene
import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import reverse
from django.test.client import MULTIPART_CONTENT, Client
from graphql_jwt.shortcuts import get_token

from saleor.account.models import User

from .utils import assert_no_permission

API_PATH = reverse('api')


class ApiClient(Client):
    """GraphQL API client."""

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        self.user = user
        if not user.is_anonymous:
            self.token = get_token(user)
        super().__init__(*args, **kwargs)

    def _base_environ(self, **request):
        environ = super()._base_environ(**request)
        if not self.user.is_anonymous:
            environ.update({'HTTP_AUTHORIZATION': 'JWT %s' % self.token})
        return environ

    def post(self, data=None, **kwargs):
        """Send a POST request.

        This wrapper sets the `application/json` content type which is
        more suitable for standard GraphQL requests and doesn't mismatch with
        handling multipart requests in Graphene.
        """
        if data:
            data = json.dumps(data, cls=DjangoJSONEncoder)
        kwargs['content_type'] = 'application/json'
        return super().post(API_PATH, data, **kwargs)

    def post_graphql(
            self, query, variables=None, permissions=None,
            check_no_permissions=True, **kwargs):
        """Dedicated helper for posting GraphQL queries.

        Sets the `application/json` content type and json.dumps the variables
        if present.
        """
        data = {'query': query}
        if variables is not None:
            data['variables'] = variables
        if data:
            data = json.dumps(data, cls=DjangoJSONEncoder)
        kwargs['content_type'] = 'application/json'

        if permissions:
            if check_no_permissions:
                response = super().post(API_PATH, data, **kwargs)
                assert_no_permission(response)
            self.user.user_permissions.add(*permissions)
        return super().post(API_PATH, data, **kwargs)

    def post_multipart(self, *args, permissions=None, **kwargs):
        """Send a multipart POST request.

        This is used to send multipart requests to GraphQL API when e.g.
        uploading files.
        """
        kwargs['content_type'] = MULTIPART_CONTENT

        if permissions:
            response = super().post(API_PATH, *args, **kwargs)
            assert_no_permission(response)
            self.user.user_permissions.add(*permissions)
        return super().post(API_PATH, *args, **kwargs)


@pytest.fixture
def staff_api_client(staff_user):
    return ApiClient(user=staff_user)


@pytest.fixture
def user_api_client(customer_user):
    return ApiClient(user=customer_user)


@pytest.fixture
def api_client():
    return ApiClient(user=AnonymousUser())


@pytest.fixture
def schema_context():
    params = {'user': AnonymousUser()}
    return graphene.types.Context(**params)


@pytest.fixture
def superuser():
    superuser = User.objects.create_superuser('superuser@example.com', 'pass')
    return superuser


@pytest.fixture
def user_list():
    users = User.objects.bulk_create(
        [User(email='user-2@example.com'),
         User(email='user-1@example.com'),
         User(
             email='staff-1@example.com', is_staff=True),
         User(
             email='staff-2@example.com', is_staff=True),
         ])
    return users


@pytest.fixture
def user_list_not_active(user_list):
    users = User.objects.filter(pk__in=[user.pk for user in user_list])
    users.update(is_active=False)
    return users
