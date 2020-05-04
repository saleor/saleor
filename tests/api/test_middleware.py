from unittest.mock import Mock

from django.urls import reverse

from saleor.graphql.middleware import app_middleware


def test_app_middleware_accepts_api_requests(app, rf):

    # Retrieve sample request object
    request = rf.get(reverse("api"))
    token = app.tokens.first().auth_token
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    app_middleware(lambda root, info: info.context, Mock(), Mock(context=request))

    assert request.app == app
