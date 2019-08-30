from unittest.mock import Mock

import pytest
from django.urls import reverse

from saleor.graphql.middleware import service_account_middleware


@pytest.mark.parametrize("path, should_accept", [("api", True), ("home", False)])
def test_service_account_middleware(service_account, path, should_accept, rf):

    # Retrieve sample request object
    request = rf.get(reverse("api"))

    request.path = reverse(path)
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {service_account.auth_token}"}

    middleware = service_account_middleware(Mock())
    middleware(request)

    if should_accept:
        assert request.service == service_account
    else:
        assert not hasattr(request, "service")
