import json
import logging
from unittest import mock
from unittest.mock import Mock

import graphene
import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.test import TestCase
from django.test.client import MULTIPART_CONTENT, Client
from django.urls import reverse
from django.utils.functional import SimpleLazyObject

from ...account.models import User
from ...core.jwt import create_access_token
from ...plugins.manager import get_plugins_manager
from ..utils import handled_errors_logger, unhandled_errors_logger
from .utils import assert_no_permission

API_PATH = reverse("api")


class BaseApiClient(Client):
    """GraphQL API client."""

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        app = kwargs.pop("app", None)
        api_path = kwargs.pop("api_path", None)
        self._user = None
        self.token = None
        self.user = user
        self.app_token = None
        self.app = app
        if app:
            _, auth_token = app.tokens.create(name="Default")
            self.app_token = auth_token
        self.api_path = API_PATH
        if api_path:
            self.api_path = api_path
        super().__init__(*args, **kwargs)

    def _base_environ(self, **request):
        environ = super()._base_environ(**request)
        self.ensure_access_token()
        if self.token:
            environ["HTTP_AUTHORIZATION"] = f"JWT {self.token}"
        elif self.app_token:
            environ["HTTP_AUTHORIZATION"] = f"Bearer {self.app_token}"
        return environ

    def regenerate_access_token(self):
        if self.user and self.token:
            self.token = create_access_token(self.user)
        else:
            self.token = None

    def ensure_access_token(self):
        if self.user and not self.token:
            self.token = create_access_token(self.user)

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, user):
        self._user = user
        self.token = None

    def post(self, data=None, **kwargs):
        """Send a POST request.

        This wrapper sets the `application/json` content type which is
        more suitable for standard GraphQL requests and doesn't mismatch with
        handling multipart requests in Graphene.
        """
        if data:
            data = json.dumps(data, cls=DjangoJSONEncoder)
        kwargs["content_type"] = "application/json"
        return super().post(self.api_path, data, **kwargs)


class ApiClient(BaseApiClient):
    def post_graphql(
        self,
        query,
        variables=None,
        # @deprecated - do not use it, because it makes implicit permissions check
        # Use explicit permissions assertions
        permissions=None,
        check_no_permissions=True,
        **kwargs,
    ):
        """Dedicated helper for posting GraphQL queries.

        Sets the `application/json` content type and json.dumps the variables
        if present.
        """
        data = {"query": query}
        if variables is not None:
            data["variables"] = variables
        if data:
            data = json.dumps(data, cls=DjangoJSONEncoder)
        kwargs["content_type"] = "application/json"

        if permissions:
            if check_no_permissions:
                with mock.patch("saleor.graphql.utils.handled_errors_logger"):
                    response = super(Client, self).post(self.api_path, data, **kwargs)
                assert_no_permission(response)
            if self.app:
                self.app.permissions.add(*permissions)
            else:
                self.user.user_permissions.add(*permissions)
        with TestCase.captureOnCommitCallbacks(execute=True):
            result = super(Client, self).post(self.api_path, data, **kwargs)
        return result

    def post_multipart(self, *args, permissions=None, **kwargs):
        """Send a multipart POST request.

        This is used to send multipart requests to GraphQL API when e.g.
        uploading files.
        """
        kwargs["content_type"] = MULTIPART_CONTENT

        if permissions:
            response = super(Client, self).post(self.api_path, *args, **kwargs)
            assert_no_permission(response)
            self.user.user_permissions.add(*permissions)
        with TestCase.captureOnCommitCallbacks(execute=True):
            result = super(Client, self).post(self.api_path, *args, **kwargs)
        return result


@pytest.fixture
def app_api_client(app):
    return ApiClient(app=app)


@pytest.fixture
def staff_api_client(staff_user):
    return ApiClient(user=staff_user)


@pytest.fixture
def superuser_api_client(superuser):
    return ApiClient(user=superuser)


@pytest.fixture
def user_api_client(customer_user):
    return ApiClient(user=customer_user)


@pytest.fixture
def user2_api_client(customer_user2):
    return ApiClient(user=customer_user2)


@pytest.fixture
def api_client():
    return ApiClient(user=None)


@pytest.fixture
def schema_context():
    params = {
        "user": SimpleLazyObject(lambda: None),
        "app": SimpleLazyObject(lambda: None),
        "plugins": get_plugins_manager(allow_replica=False),
        "auth_token": "",
    }
    return graphene.types.Context(**params)


@pytest.fixture
def info(schema_context):
    return Mock(context=schema_context)


@pytest.fixture
def anonymous_plugins():
    return get_plugins_manager(allow_replica=False)


class LoggingHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = []

    def emit(self, record: logging.LogRecord):
        exc_type, exc_value, _tb = record.exc_info
        self.messages.append(
            f"{record.name}[{record.levelname.upper()}].{exc_type.__name__}"
        )


@pytest.fixture
def graphql_log_handler():
    log_handler = LoggingHandler()

    unhandled_errors_logger.addHandler(log_handler)
    handled_errors_logger.addHandler(log_handler)

    return log_handler


@pytest.fixture
def superuser(db):
    superuser = User.objects.create_user(
        "superuser@example.com",
        "pass",
        is_staff=True,
        is_active=True,
        is_superuser=True,
    )
    return superuser


@pytest.fixture
def user_list():
    users = User.objects.bulk_create(
        [
            User(email="user-2@example.com"),
            User(email="user-1@example.com"),
            User(email="staff-1@example.com", is_staff=True),
            User(email="staff-2@example.com", is_staff=True),
        ]
    )
    return users


@pytest.fixture
def user_list_not_active(user_list):
    users = User.objects.filter(pk__in=[user.pk for user in user_list])
    users.update(is_active=False)
    return users
