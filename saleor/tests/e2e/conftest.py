import json

import pytest
from django.core.serializers.json import DjangoJSONEncoder
from django.test.client import MULTIPART_CONTENT, Client

from ...account.models import User
from ...graphql.tests.fixtures import BaseApiClient
from ..utils import flush_post_commit_hooks


class E2eApiClient(BaseApiClient):
    def post_graphql(
        self,
        query,
        variables=None,
        **kwargs,
    ):
        """Dedicated helper for posting GraphQL queries.

        Sets the `application/json` content type and json.dumps the variables
        if present.
        """
        data = {"query": query}
        if variables is not None:
            data["variables"] = variables
        data = json.dumps(data, cls=DjangoJSONEncoder)
        kwargs["content_type"] = "application/json"

        result = super(Client, self).post(self.api_path, data, **kwargs)
        flush_post_commit_hooks()
        return result

    def post_multipart(self, *args, **kwargs):
        """Send a multipart POST request.

        This is used to send multipart requests to GraphQL API when e.g.
        uploading files.
        """
        kwargs["content_type"] = MULTIPART_CONTENT

        result = super(Client, self).post(self.api_path, *args, **kwargs)
        flush_post_commit_hooks()
        return result


@pytest.fixture
def e2e_staff_api_client():
    e2e_staff_user = User.objects.create_user(
        email="e2e_staff_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )
    return E2eApiClient(user=e2e_staff_user)


@pytest.fixture
def e2e_logged_api_client():
    e2e_customer = User.objects.create_user(
        email="JoeCustomer@example.com",
        password="password",
        first_name="Joe",
        last_name="Saleor",
        is_active=True,
        is_staff=False,
    )
    return E2eApiClient(user=e2e_customer)


@pytest.fixture
def e2e_not_logged_api_client():
    return E2eApiClient()
