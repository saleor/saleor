from django.urls import reverse

from ...app.dataloaders import load_app


def test_app_middleware_accepts_app_requests(app, rf):
    # given
    # Retrieve sample request object
    request = rf.get(reverse("api"))
    _, token = app.tokens.create()
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    # when
    request_app = load_app(request)

    # then
    assert request_app == app


def test_app_middleware_accepts_saleors_header(app, rf):
    # given
    request = rf.get(reverse("api"))
    _, token = app.tokens.create()
    request.META = {"HTTP_AUTHORIZATION_BEARER": f"{token}"}

    # when
    request_app = load_app(request)

    # then
    assert request_app == app


def test_app_middleware_skips_when_token_length_is_different_than_30(
    app_with_token, rf
):
    # given
    request = rf.get(reverse("api"))
    request.META = {"HTTP_AUTHORIZATION_BEARER": "a" * 31}

    # when
    request_app = load_app(request)

    # then
    assert not request_app
