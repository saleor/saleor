import datetime
import json
import time
import warnings
from unittest import mock
from unittest.mock import MagicMock, Mock, call, patch

import pytest
import requests
from authlib.jose import JWTClaims
from django.core.exceptions import ValidationError
from freezegun import freeze_time
from requests import Response
from requests_hardened import HTTPSession

from ....account.models import Group, User
from ....core.jwt import (
    JWT_REFRESH_TYPE,
    PERMISSIONS_FIELD,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ....permission.models import Permission
from ..exceptions import AuthenticationError
from ..utils import (
    JWKS_CACHE_TIME,
    JWKS_KEY,
    OIDC_DEFAULT_CACHE_TIME,
    _update_user_details,
    assign_staff_to_default_group_and_update_permissions,
    create_jwt_refresh_token,
    create_jwt_token,
    create_tokens_from_oauth_payload,
    fetch_jwks,
    get_domain_from_email,
    get_or_create_user_from_payload,
    get_saleor_permission_names,
    get_saleor_permissions_qs_from_scope,
    get_user_from_oauth_access_token_in_jwt_format,
    get_user_from_token,
    get_user_info,
    validate_refresh_token,
)

OIDC_CACHE_TIMEOUT = min(JWKS_CACHE_TIME, OIDC_DEFAULT_CACHE_TIME)


@pytest.mark.parametrize(
    "error",
    [
        json.JSONDecodeError(msg="", doc="", pos=0),
        requests.exceptions.RequestException(),
    ],
)
def test_fetch_jwks_raises_error(monkeypatch, error):
    mocked_get = Mock()
    mocked_get.side_effect = error
    jwks_url = "http://localhost:3000/"
    monkeypatch.setattr(HTTPSession, "request", mocked_get)

    with pytest.raises(AuthenticationError):
        fetch_jwks(jwks_url)


@pytest.mark.vcr(decode_compressed_response=True)
@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
def test_fetch_jwks(mocked_cache_set):
    jwks_url = "https://saleor.io/.well-known/jwks.json"
    keys = fetch_jwks(jwks_url)
    assert len(keys) == 2
    mocked_cache_set.assert_called_once_with(JWKS_KEY, keys, JWKS_CACHE_TIME)


def test_get_or_create_user_from_token_missing_email(id_payload):
    del id_payload["email"]
    with pytest.raises(AuthenticationError):
        get_or_create_user_from_payload(id_payload, "https://saleor.io/oauth")


def test_get_or_create_user_from_token_user_not_active(id_payload, admin_user):
    admin_user.is_active = False
    admin_user.save()
    with pytest.raises(AuthenticationError):
        get_or_create_user_from_payload(id_payload, "https://saleor.io/oauth")


def test_get_user_from_token_missing_email(id_payload):
    del id_payload["email"]
    with pytest.raises(AuthenticationError):
        get_user_from_token(id_payload)


def test_get_user_from_token_missing_user(id_payload):
    User.objects.all().delete()
    with pytest.raises(AuthenticationError):
        get_user_from_token(id_payload)


def test_get_user_from_token_user_not_active(id_payload, admin_user):
    admin_user.is_active = False
    admin_user.save()
    with pytest.raises(AuthenticationError):
        get_user_from_token(id_payload)


@freeze_time("2019-03-18 12:00:00")
def test_create_tokens_from_oauth_payload(monkeypatch, id_token, id_payload):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        Mock(return_value=mocked_jwt_validator),
    )
    permissions_from_scope = [
        "MANAGE_ORDERS",
    ]
    auth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "id_token": id_token,
        "scope": (
            "openid profile email offline_access saleor:manage_orders saleor:staff"
        ),
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    user, _, _ = get_or_create_user_from_payload(id_payload, "https://saleor.io/oauth")
    permissions = get_saleor_permissions_qs_from_scope(auth_payload.get("scope"))
    perms = get_saleor_permission_names(permissions)
    tokens = create_tokens_from_oauth_payload(
        auth_payload, user, id_payload, perms, "PluginID"
    )

    created_user = User.objects.get()

    token = create_jwt_token(
        id_payload,
        created_user,
        auth_payload["access_token"],
        permissions_from_scope,
        "PluginID",
    )

    assert created_user.email == id_payload["email"]
    assert tokens["token"] == token
    # confirm that we have jwt token
    decoded_token = jwt_decode(tokens["token"])
    assert decoded_token.get(PERMISSIONS_FIELD) == permissions_from_scope

    decoded_refresh_token = jwt_decode(tokens["refresh_token"])
    assert decoded_refresh_token["oauth_refresh_token"] == "refresh"


@freeze_time("2019-03-18 12:00:00")
def test_validate_refresh_token_missing_csrf_token(admin_user):
    token = create_jwt_refresh_token(admin_user, "refresh_token", "csrf", "pluginID")
    with pytest.raises(ValidationError):
        validate_refresh_token(token, {})


def test_validate_refresh_token_missing_csrf_token_in_token_payload(admin_user):
    additional_payload = {"oauth_refresh_token": "refresh_token"}
    jwt_payload = jwt_user_payload(
        admin_user,
        JWT_REFRESH_TYPE,
        # oauth_refresh_token has own expiration time. No need to duplicate it here
        exp_delta=None,
        additional_payload=additional_payload,
    )
    token = jwt_encode(jwt_payload)
    with pytest.raises(ValidationError):
        validate_refresh_token(token, {})


def test_validate_refresh_token_missing_token():
    refresh_token = ""
    with pytest.raises(ValidationError):
        validate_refresh_token(refresh_token, {})


def test_get_saleor_permissions_from_scope():
    auth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "scope": (
            "openid profile email offline_access saleor:manage_orders "
            "saleor:non_existing saleor saleor: saleor:manage_users"
        ),
    }
    expected_permissions = {"MANAGE_USERS", "MANAGE_ORDERS"}
    permissions = get_saleor_permissions_qs_from_scope(auth_payload.get("scope"))
    permission_names = get_saleor_permission_names(permissions)
    assert set(permission_names) == expected_permissions


def test_get_user_info_raises_decode_error(monkeypatch):
    response = Response()
    response.status_code = 200
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=response))

    user_info = get_user_info("https://saleor.io/userinfo", "access_token")
    assert user_info is None


def test_get_user_info_raises_http_error(monkeypatch):
    response = Response()
    response.status_code = 500
    monkeypatch.setattr(HTTPSession, "request", Mock(return_value=response))

    user_info = get_user_info("https://saleor.io/userinfo", "access_token")
    assert user_info is None


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_retrieve_user_by_sub(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    customer_user.private_metadata = {f"oidc:{oauth_url}": sub_id}
    customer_user.save()

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user_from_payload, _, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)
    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    assert user_from_payload.id == customer_user.id
    assert user_from_payload.private_metadata[f"oidc:{oauth_url}"] == sub_id


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_updates_sub(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    customer_user.private_metadata = {f"oidc:{oauth_url}": "old-sub"}
    customer_user.save()

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user_from_payload, _, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    assert user_from_payload.id == customer_user.id
    assert user_from_payload.private_metadata[f"oidc:{oauth_url}"] == sub_id


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_assigns_sub(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user_from_payload, _, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    assert user_from_payload.id == customer_user.id
    assert user_from_payload.private_metadata[f"oidc:{oauth_url}"] == sub_id
    assert customer_user.is_staff is False


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_creates_user_with_sub(
    mocked_cache_get, mocked_cache_set
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    customer_email = "email.customer@example.com"

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user_from_payload, _, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, user_from_payload.id, OIDC_CACHE_TIMEOUT
    )
    assert user_from_payload.email == customer_email
    assert user_from_payload.private_metadata[f"oidc:{oauth_url}"] == sub_id
    assert not user_from_payload.has_usable_password()
    assert user_from_payload.is_active
    assert user_from_payload.is_confirmed


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_match_orders_for_new_user(
    mocked_cache_get, mocked_cache_set, order
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    customer_email = "email.customer@example.com"

    mocked_cache_get.side_effect = lambda cache_key: None

    order.user = None
    order.user_email = customer_email
    order.save()

    # when
    user_from_payload, _, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, user_from_payload.id, OIDC_CACHE_TIMEOUT
    )
    order.refresh_from_db()
    assert order.user == user_from_payload


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_match_orders_when_changing_email(
    mocked_cache_get, mocked_cache_set, customer_user, order
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    new_customer_email = "new.customer@example.com"

    mocked_cache_get.side_effect = lambda cache_key: None

    customer_user.private_metadata = {f"oidc:{oauth_url}": sub_id}
    customer_user.save()

    order.user_email = new_customer_email
    order.user = None
    order.save()

    # when
    user_from_payload, _, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": new_customer_email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    customer_user.refresh_from_db()
    order.refresh_from_db()
    assert order.user == user_from_payload


def test_get_or_create_user_from_payload_multiple_subs(customer_user, admin_user):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    customer_user.private_metadata = {f"oidc-{oauth_url}": sub_id}
    customer_user.save()

    admin_user.private_metadata = {f"oidc-{oauth_url}": sub_id}
    admin_user.save()

    # when
    with warnings.catch_warnings(record=True):
        user_from_payload, _, _ = get_or_create_user_from_payload(
            payload={"sub": sub_id, "email": customer_user.email},
            oauth_url=oauth_url,
        )

    # then
    assert user_from_payload.email == customer_user.email
    assert user_from_payload.private_metadata[f"oidc-{oauth_url}"] == sub_id


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_different_email(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    new_customer_email = "new.customer@example.com"

    mocked_cache_get.side_effect = lambda cache_key: None

    customer_user.private_metadata = {f"oidc:{oauth_url}": sub_id}
    customer_user.save()

    # when
    user_from_payload, _, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": new_customer_email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    customer_user.refresh_from_db()
    assert user_from_payload.id == customer_user.id
    assert customer_user.email == new_customer_email
    assert customer_user.private_metadata[f"oidc:{oauth_url}"] == sub_id


@freeze_time("2019-03-18 12:00:00")
@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_with_last_login(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    current_ts = int(time.time())

    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    mocked_cache_get.side_effect = lambda cache_key: None

    customer_user.last_login = datetime.datetime.fromtimestamp(
        current_ts - 10, tz=datetime.UTC
    )
    customer_user.save()

    # when
    user_from_payload, _, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
        last_login=current_ts,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    customer_user.refresh_from_db()
    assert customer_user.last_login == datetime.datetime.fromtimestamp(
        current_ts, tz=datetime.UTC
    )
    assert user_from_payload.email == customer_user.email
    assert user_from_payload.private_metadata[f"oidc:{oauth_url}"] == sub_id


@freeze_time("2019-03-18 12:00:00")
@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_update_last_login(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    assert customer_user.last_login is None
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user, created, updated = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    customer_user.refresh_from_db()
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    assert customer_user.last_login
    last_login = customer_user.last_login.strftime("%Y-%m-%d %H:%M:%S")
    assert last_login == "2019-03-18 12:00:00"
    assert updated is True


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_set_is_confirmed(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    customer_user.is_confirmed = False
    customer_user.save(update_fields=["is_confirmed"])
    assert customer_user.last_login is None
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    customer_user.refresh_from_db()
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    assert customer_user.is_confirmed


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_last_login_stays_same(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    last_login = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(minutes=14)
    customer_user.last_login = last_login
    customer_user.save()
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )

    # then
    customer_user.refresh_from_db()
    assert customer_user.last_login == last_login


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_last_login_modifies(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # given
    last_login = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(minutes=16)
    customer_user.last_login = last_login
    customer_user.save()
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )
    cache_key = f"oidc:{oauth_url}" + ":" + str(sub_id)

    # then
    customer_user.refresh_from_db()
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.id, OIDC_CACHE_TIMEOUT
    )
    assert customer_user.last_login
    assert customer_user.last_login != last_login


@patch("saleor.plugins.manager.PluginsManager.customer_created")
def test_jwt_token_without_expiration_claim(
    mocked_customer_created_webhook,
    monkeypatch,
    decoded_access_token,
    django_capture_on_commit_callbacks,
):
    # given
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info_from_cache_or_fetch",
        lambda *args, **kwargs: {
            "email": "test@example.org",
            "sub": token_payload["sub"],
            "scope": token_payload["scope"],
        },
    )
    decoded_access_token.pop("exp")
    token_payload = JWTClaims(
        decoded_access_token,
        {},
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        user = get_user_from_oauth_access_token_in_jwt_format(
            token_payload,
            "https://example.com",
            access_token="fake-token",
            use_scope_permissions=False,
            audience="",
            staff_user_domains=[],
            staff_default_group_name="",
        )

    # then
    assert user.email == "test@example.org"
    mocked_customer_created_webhook.assert_called_once_with(user)


@patch("saleor.plugins.manager.PluginsManager.customer_created")
@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_jwt_token_without_expiration_claim_mixed_permissions_from_group(
    mocked_cache_get,
    mocked_cache_set,
    mocked_customer_created_webhook,
    customer_user,
    monkeypatch,
    decoded_access_token,
    permission_group_manage_shipping,
    django_capture_on_commit_callbacks,
):
    # given
    customer_user.groups.add(permission_group_manage_shipping)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info_from_cache_or_fetch",
        lambda *args, **kwargs: {
            "email": customer_user.email,
            "sub": token_payload["sub"],
            "scope": token_payload["scope"],
        },
    )
    decoded_access_token.pop("exp")
    token_payload = JWTClaims(
        decoded_access_token,
        {},
    )

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    with django_capture_on_commit_callbacks(execute=True):
        user = get_user_from_oauth_access_token_in_jwt_format(
            token_payload,
            "https://example.com",
            access_token="fake-token",
            use_scope_permissions=True,
            audience="",
            staff_user_domains=[customer_user.email.split("@")[1]],
            staff_default_group_name="",
        )

    # then
    manage_shipping = permission_group_manage_shipping.permissions.first()
    assert user.id == customer_user.id
    assert manage_shipping in user.effective_permissions
    assert len(user.effective_permissions) > 1
    # ensure that manage_shipping is not from openID scope permissions
    assert "saleor:manage_shipping" not in token_payload["scope"]
    mocked_customer_created_webhook.assert_not_called()


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_jwt_token_without_expiration_claim_email_not_match_staff_user_domains(
    mocked_cache_get, mocked_cache_set, customer_user, monkeypatch, decoded_access_token
):
    # given
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info_from_cache_or_fetch",
        lambda *args, **kwargs: {
            "email": customer_user.email,
            "sub": token_payload["sub"],
            "scope": "",
        },
    )
    decoded_access_token.pop("exp")
    token_payload = JWTClaims(
        decoded_access_token,
        {},
    )
    default_group_name = "test group"
    assert Group.objects.count() == 0

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user = get_user_from_oauth_access_token_in_jwt_format(
        token_payload,
        "https://example.com",
        access_token="fake-token",
        use_scope_permissions=False,
        audience="",
        staff_user_domains=["test.pl"],
        staff_default_group_name=default_group_name,
    )

    # then
    assert user.id == customer_user.id
    assert user.is_staff is False
    assert list(user.effective_permissions) == []
    assert Group.objects.count() == 0
    assert user.groups.count() == 0


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_jwt_token_without_expiration_claim_default_channel_group(
    mocked_cache_get, mocked_cache_set, customer_user, monkeypatch, decoded_access_token
):
    # given
    decoded_access_token["scope"] = ""
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info_from_cache_or_fetch",
        lambda *args, **kwargs: {
            "email": customer_user.email,
            "sub": token_payload["sub"],
            "scope": token_payload["scope"],
        },
    )
    decoded_access_token.pop("exp")
    token_payload = JWTClaims(
        decoded_access_token,
        {},
    )
    default_group_name = "test group"
    assert Group.objects.count() == 0

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user = get_user_from_oauth_access_token_in_jwt_format(
        token_payload,
        "https://example.com",
        access_token="fake-token",
        use_scope_permissions=False,
        audience="",
        staff_user_domains=[customer_user.email.split("@")[1]],
        staff_default_group_name=default_group_name,
    )

    # then
    assert user.id == customer_user.id
    assert user.is_staff is True
    assert list(user.effective_permissions) == []
    assert Group.objects.count() == 1
    group = Group.objects.get()
    assert group.name == default_group_name
    assert user.groups.count() == 1
    assert user.groups.first() == group


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_jwt_token_without_expiration_claim_with_existing_default_channel_group(
    mocked_cache_get,
    mocked_cache_set,
    customer_user,
    monkeypatch,
    decoded_access_token,
    permission_manage_users,
):
    # given
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info_from_cache_or_fetch",
        lambda *args, **kwargs: {
            "email": customer_user.email,
            "sub": token_payload["sub"],
            "scope": token_payload["scope"],
        },
    )
    decoded_access_token.pop("exp")
    token_payload = JWTClaims(
        decoded_access_token,
        {},
    )
    default_group_name = "test group"
    group = Group.objects.create(name=default_group_name)
    group.permissions.add(permission_manage_users)
    group_count = Group.objects.count()

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user = get_user_from_oauth_access_token_in_jwt_format(
        token_payload,
        "https://example.com",
        access_token="fake-token",
        use_scope_permissions=False,
        audience="",
        staff_user_domains=[customer_user.email.split("@")[1]],
        staff_default_group_name=default_group_name,
    )

    # then
    assert user.id == customer_user.id
    assert user.is_staff is True
    assert Group.objects.count() == group_count
    assert group in user.groups.all()
    assert len(user.effective_permissions) > 1
    assert permission_manage_users in user.effective_permissions
    # ensure that manage_users is not from openID scope permissions
    assert "saleor:manage_users" not in token_payload["scope"]


@pytest.mark.parametrize("staff_default_group_name", ["  ", ""])
@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_jwt_token_without_expiration_claim_empty_default_channel_group(
    mocked_cache_get,
    mocked_cache_set,
    staff_default_group_name,
    customer_user,
    monkeypatch,
    decoded_access_token,
):
    # given
    decoded_access_token["scope"] = ""
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info_from_cache_or_fetch",
        lambda *args, **kwargs: {
            "email": customer_user.email,
            "sub": token_payload["sub"],
            "scope": token_payload["scope"],
        },
    )
    decoded_access_token.pop("exp")
    token_payload = JWTClaims(
        decoded_access_token,
        {},
    )
    assert Group.objects.count() == 0

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user = get_user_from_oauth_access_token_in_jwt_format(
        token_payload,
        "https://example.com",
        access_token="fake-token",
        use_scope_permissions=False,
        audience="",
        staff_user_domains=[customer_user.email.split("@")[1]],
        staff_default_group_name=staff_default_group_name,
    )

    # then
    assert user.id == customer_user.id
    assert user.is_staff is True
    assert list(user.effective_permissions) == []
    assert Group.objects.count() == 0
    assert user.groups.count() == 0


@pytest.mark.parametrize(
    ("email", "expected_domain"),
    [
        ("test@example.com", "example.com"),
        ("ABCd", None),
        ("", None),
        ("test.test", None),
    ],
)
def test_get_domain_from_email(email, expected_domain):
    # when
    domain = get_domain_from_email(email)

    # then
    assert domain == expected_domain


def test_assign_staff_to_default_group_and_update_permissions_new_group_created(
    staff_user,
):
    # given
    assert Group.objects.count() == 0
    default_group_name = "test default group"

    # when
    assign_staff_to_default_group_and_update_permissions(staff_user, default_group_name)

    # then
    assert Group.objects.count() == 1
    group = Group.objects.get()
    assert group.name == default_group_name
    assert group in staff_user.groups.all()


def test_assign_staff_to_default_group_and_update_permissions_update_user_permissions(
    staff_user, permission_manage_orders, permission_manage_users
):
    # given
    default_group_name = "test default group"
    group = Group.objects.create(name=default_group_name)
    group.permissions.add(permission_manage_users)

    staff_user.effective_permissions = Permission.objects.filter(
        id=permission_manage_orders.id
    )

    # when
    assign_staff_to_default_group_and_update_permissions(
        staff_user, "test default group"
    )

    # then
    assert group in staff_user.groups.all()
    assert {perm.name for perm in staff_user.effective_permissions} == {
        permission_manage_users.name,
        permission_manage_orders.name,
    }


@patch("saleor.plugins.openid_connect.utils.match_orders_with_new_user")
@patch("saleor.plugins.openid_connect.utils.logger")
def test_update_user_details_no_user_with_new_email_in_db(
    mock_logger,
    mock_match_orders_with_new_user,
    customer_user,
):
    # given
    assert customer_user.email != "test_user_email@example.com"

    # when
    _update_user_details(
        customer_user,
        "test oidc_key",
        "test_user_email@example.com",
        customer_user.first_name,
        customer_user.last_name,
        "test oidc_sub",
        customer_user.last_login,
    )

    # then
    customer_user.refresh_from_db()
    assert customer_user.email == "test_user_email@example.com"
    assert mock_logger.mock_calls == []
    mock_match_orders_with_new_user.assert_called_once_with(customer_user)


@patch("saleor.plugins.openid_connect.utils.match_orders_with_new_user")
@patch("saleor.plugins.openid_connect.utils.logger")
def test_update_user_details_user_with_new_email_in_db(
    mock_logger, mock_match_orders_with_new_user, customer_user, customer_user2
):
    # given
    assert customer_user.email != customer_user2.email

    # when
    _update_user_details(
        customer_user,
        "test oidc_key",
        customer_user2.email,
        customer_user.first_name,
        customer_user.last_name,
        "test oidc_sub",
        customer_user.last_login,
    )

    # then
    customer_user.refresh_from_db()
    assert customer_user.email != customer_user2.email
    assert mock_logger.mock_calls == [
        call.warning(
            "Unable to update user email as the new one already exists in DB",
            extra={"oidc_key": "test oidc_key"},
        )
    ]
    mock_match_orders_with_new_user.assert_not_called()


def test_update_user_details_update_user_first_name(
    customer_user,
):
    # given
    expected_search_document = "test@example.com\ntest user_first_name\nwade\n"
    assert customer_user.first_name != "test user_first_name"
    assert customer_user.search_document != expected_search_document

    # when
    updated = _update_user_details(
        customer_user,
        "test oidc_key",
        customer_user.email,
        "test user_first_name",
        customer_user.last_name,
        "test oidc_sub",
        customer_user.last_login,
    )

    # then
    customer_user.refresh_from_db()
    assert customer_user.first_name == "test user_first_name"
    assert customer_user.search_document == expected_search_document
    assert updated is True


def test_update_user_details_update_user_last_name(
    customer_user,
):
    # given
    expected_search_document = "test@example.com\nleslie\ntest user_last_name\n"
    assert customer_user.last_name != "test user_last_name"
    assert customer_user.search_document != expected_search_document

    # when
    updated = _update_user_details(
        customer_user,
        "test oidc_key",
        customer_user.email,
        customer_user.first_name,
        "test user_last_name",
        "test oidc_sub",
        customer_user.last_login,
    )

    # then
    customer_user.refresh_from_db()
    assert customer_user.last_name == "test user_last_name"
    assert customer_user.search_document == expected_search_document
    assert updated is True


def test_update_user_details_nothing_changed(
    customer_user,
):
    # given
    last_login = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(minutes=14)
    customer_user.last_login = last_login
    customer_user.search_document = "abc"
    customer_user.save(update_fields=["search_document", "last_login"])

    first_name = customer_user.first_name

    # when
    updated = _update_user_details(
        customer_user,
        "test oidc_key",
        customer_user.email,
        customer_user.first_name,
        customer_user.last_name,
        None,
        5,
    )

    # then
    customer_user.refresh_from_db()
    assert customer_user.first_name == first_name
    assert updated is False
