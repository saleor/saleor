from django.core.handlers.base import BaseHandler
from freezegun import freeze_time

from ..jwt import JWT_REFRESH_TOKEN_COOKIE_NAME, create_refresh_token


@freeze_time("2020-03-18 12:00:00")
def test_jwt_refresh_token_middleware(rf, customer_user, settings):
    refresh_token = create_refresh_token(customer_user)
    settings.MIDDLEWARE = [
        "saleor.core.middleware.jwt_refresh_token_middleware",
    ]
    request = rf.request()
    request.refresh_token = refresh_token
    handler = BaseHandler()
    handler.load_middleware()
    response = handler.get_response(request)
    cookie = response.cookies.get(JWT_REFRESH_TOKEN_COOKIE_NAME)
    assert cookie.value == refresh_token
