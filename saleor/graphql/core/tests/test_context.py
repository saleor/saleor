from django.urls import reverse

from ...context import set_app_on_context


def test_app_middleware_accepts_app_requests(app, rf):
    # given
    # Retrieve sample request object
    request = rf.get(reverse("api"))
    _, token = app.tokens.create()
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    # when
    set_app_on_context(request)

    # then
    assert request.app == app


def test_app_middleware_accepts_saleors_header(app, rf):
    # given
    request = rf.get(reverse("api"))
    _, token = app.tokens.create()
    request.META = {"HTTP_AUTHORIZATION_BEARER": f"{token}"}

    # when
    set_app_on_context(request)

    # then
    assert request.app == app


def test_app_middleware_skips_when_token_length_is_different_than_30(
    app_with_token, rf
):
    # given
    request = rf.get(reverse("api"))
    request.META = {"HTTP_AUTHORIZATION_BEARER": "a" * 31}

    # when
    set_app_on_context(request)

    # then
    assert not request.app
