from unittest.mock import Mock

from django.urls import reverse

from ....app.models import AppToken
from ...middleware import app_middleware


def test_app_middleware_accepts_api_requests(app, rf):

    # Retrieve sample request object
    request = rf.get(reverse("api"))
    _token_inst, token = AppToken.objects.create_app_token(app=app)
    request.META = {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    app_middleware(lambda root, info: info.context, Mock(), Mock(context=request))

    assert request.app == app
