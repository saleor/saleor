import jwt
import pytest
from freezegun import freeze_time
from jwt import ExpiredSignatureError, InvalidSignatureError

from ..auth_backend import JSONWebTokenBackend
from ..jwt import (
    JWT_ACCESS_TYPE,
    JWT_ALGORITHM,
    create_access_token,
    create_refresh_token,
    jwt_user_payload,
)


def test_user_authenticated(rf, staff_user):
    access_token = create_access_token(staff_user)
    request = rf.request(HTTP_AUTHORIZATION=f"JWT {access_token}")
    backend = JSONWebTokenBackend()
    user = backend.authenticate(request)
    assert user == staff_user


def test_user_deactivated(rf, staff_user):
    staff_user.is_active = False
    staff_user.save()
    access_token = create_access_token(staff_user)
    request = rf.request(HTTP_AUTHORIZATION=f"JWT {access_token}")
    backend = JSONWebTokenBackend()
    assert backend.authenticate(request) is None


def test_incorect_type_of_token(rf, staff_user):
    token = create_refresh_token(staff_user)
    request = rf.request(HTTP_AUTHORIZATION=f"JWT {token}")
    backend = JSONWebTokenBackend()
    assert backend.authenticate(request) is None


def test_incorrect_token(rf, staff_user, settings):
    payload = jwt_user_payload(
        staff_user, JWT_ACCESS_TYPE, settings.JWT_EXPIRATION_DELTA,
    )
    token = jwt.encode(payload, "Wrong secret", JWT_ALGORITHM,).decode("utf-8")
    request = rf.request(HTTP_AUTHORIZATION=f"JWT {token}")
    backend = JSONWebTokenBackend()
    with pytest.raises(InvalidSignatureError):
        backend.authenticate(request)


def test_missing_token(rf, staff_user):
    request = rf.request(HTTP_AUTHORIZATION="JWT ")
    backend = JSONWebTokenBackend()
    assert backend.authenticate(request) is None


def test_missing_header(rf, staff_user):
    request = rf.request()
    backend = JSONWebTokenBackend()
    assert backend.authenticate(request) is None


def test_token_expired(rf, staff_user):
    with freeze_time("2019-03-18 12:00:00"):
        access_token = create_access_token(staff_user)
    request = rf.request(HTTP_AUTHORIZATION=f"JWT {access_token}")
    backend = JSONWebTokenBackend()
    with pytest.raises(ExpiredSignatureError):
        backend.authenticate(request)


def test_user_doesnt_exist(rf, staff_user):
    access_token = create_access_token(staff_user)
    staff_user.delete()
    request = rf.request(HTTP_AUTHORIZATION=f"JWT {access_token}")
    backend = JSONWebTokenBackend()
    assert backend.authenticate(request) is None


def test_user_deactivated_token(rf, staff_user):
    access_token = create_access_token(staff_user)
    staff_user.jwt_token_key = "New key"
    staff_user.save()
    request = rf.request(HTTP_AUTHORIZATION=f"JWT {access_token}")
    backend = JSONWebTokenBackend()
    assert backend.authenticate(request) is None
