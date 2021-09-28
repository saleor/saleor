from unittest.mock import Mock

from django.urls import reverse

from ...middleware import app_middleware


def test_app_middleware_accepts_app_requests(app, rf):
    # given
    # Retrieve sample request object
    request = rf.get(reverse("api"))
    token = app.tokens.first().auth_token
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    # when
    app_middleware(lambda root, info: info.context, Mock(), Mock(context=request))

    # then
    assert request.app == app


def test_app_middleware_accepts_saleors_header(app, rf):
    # given
    request = rf.get(reverse("api"))
    token = app.tokens.first().auth_token
    request.META = {"HTTP_AUTHORIZATION_BEARER": f"{token}"}

    # when
    app_middleware(lambda root, info: info.context, Mock(), Mock(context=request))

    # then
    assert request.app == app


def test_app_middleware_skips_when_token_length_is_different_than_30(app, rf):
    # given
    request = rf.get(reverse("api"))
    request.META = {"HTTP_AUTHORIZATION_BEARER": "a" * 31}

    # when
    app_middleware(lambda root, info: info.context, Mock(), Mock(context=request))

    # then
    assert not request.app
