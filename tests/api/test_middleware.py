from unittest.mock import Mock

import pytest
from django.urls import reverse

from saleor.graphql.middleware import service_account_middleware


def test_service_account_middleware_accepts_api_requests(service_account, rf):

    # Retrieve sample request object
    request = rf.get(reverse("api"))
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {service_account.auth_token}"}

    middleware = service_account_middleware(Mock())
    middleware(request)

    assert request.service_account == service_account


@pytest.mark.parametrize("path", ["account:details", "home"])
def test_service_account_middleware_block(service_account, path, rf):

    # Retrieve sample request object
    request = rf.get(reverse("api"))

    request.path = reverse(path)
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {service_account.auth_token}"}

    middleware = service_account_middleware(Mock())
    middleware(request)

    assert not hasattr(request, "service_account")
