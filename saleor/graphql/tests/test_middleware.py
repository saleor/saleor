from ...app.models import AppToken
from ..middleware import get_app


def test_get_app(app):
    # given
    _token_inst, token = AppToken.objects.create_app_token(app=app, name="test")

    # when
    returned_app = get_app(token)

    # then
    assert returned_app.id == app.id


def test_get_app_not_active(app):
    # given
    app.is_active = False
    app.save(update_fields=["is_active"])

    _token_inst, token = AppToken.objects.create_app_token(app=app, name="test")

    # when
    returned_app = get_app(token)

    # then
    assert returned_app is None


def test_get_app_no_app_found():
    # when
    returned_app = get_app("test")

    # then
    assert returned_app is None
