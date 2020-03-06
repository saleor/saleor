from unittest.mock import Mock

from django.urls import reverse

from saleor.graphql.middleware import service_account_middleware


def test_service_account_middleware_accepts_api_requests(service_account, rf):

    # Retrieve sample request object
    request = rf.get(reverse("api"))
    token = service_account.tokens.first().auth_token
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    service_account_middleware(
        lambda root, info: info.context, Mock(), Mock(context=request)
    )

    assert request.service_account == service_account
