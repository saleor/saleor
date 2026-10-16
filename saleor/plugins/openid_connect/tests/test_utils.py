import datetime
import json
import time
import warnings
from functools import partial
from unittest import mock
from unittest.mock import MagicMock, Mock, call, patch

import pytest
import requests
from authlib.jose import JWTClaims
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from freezegun import freeze_time
from requests import Response
from requests_hardened import HTTPSession

from ....account.models import Group, User
from ....account.search import update_user_search_vector
from ....core.jwt import (
    JWT_REFRESH_TYPE,
    PERMISSIONS_FIELD,
    create_access_token,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ....core.jwt_manager import get_jwt_manager
from ....permission.models import Permission
from ..exceptions import AuthenticationError
from ..utils import (
    JWKS_CACHE_TIME,
    JWKS_KEY,
    OIDC_DEFAULT_CACHE_TIME,
    _get_or_create_user,
    _update_user_details,
    assign_staff_to_default_group_and_update_permissions,
    create_jwt_refresh_token,
    create_jwt_token,
    create_tokens_from_oauth_payload,
    decode_access_token,
    fetch_jwks,
    get_domain_from_email,
    get_or_create_user_from_payload,
    get_saleor_permission_names,
    get_saleor_permissions_qs_from_scope,
    get_user_from_oauth_access_token_in_jwt_format,
    get_user_from_token,
    get_user_info,
    is_jwt_shaped,
    validate_refresh_token,
)

OIDC_CACHE_TIMEOUT = min(JWKS_CACHE_TIME, OIDC_DEFAULT_CACHE_TIME)
EXTRA_CASE_VARIANT_EMAILS = (
    "jOhn.doe@example.com",
    "joHn.doe@example.com",
    "johN.doe@example.com",
    "john.Doe@example.com",
    "john.dOe@example.com",
)


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


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        # 2 dots -> signed JWT (JWS), 4 dots -> encrypted JWT (JWE).
        ("header.payload.signature", True),
        ("header.encrypted_key.iv.ciphertext.tag", True),
        # A signature-less "alg:none" token still has 2 dots, so it is JWT-shaped.
        # Rejecting it is the job of the decoder, not the shape check.
        ("header.payload.", True),
        # Opaque reference tokens are not JWTs and have nothing to decode.
        ("FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3", False),
        ("", False),
        ("header.payload", False),
        ("a.b.c.d", False),
        ("a.b.c.d.e.f", False),
    ],
)
def test_is_jwt_shaped(token, expected):
    # when
    result = is_jwt_shaped(token)

    # then
    assert result is expected


def test_decode_access_token_opaque_token_skips_decode_and_logging(monkeypatch, caplog):
    # given
    opaque_token = "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3"
    jwks_url = "https://example.com/.well-known/jwks.json"
    mocked_get_decoded_token = Mock()
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        mocked_get_decoded_token,
    )

    # when
    result = decode_access_token(opaque_token, jwks_url)

    # then
    assert result is None
    mocked_get_decoded_token.assert_not_called()
    assert "Invalid OIDC access token format" not in caplog.text


def test_decode_access_token_invalid_signature_returns_none_and_logs(
    customer_user, caplog
):
    # given
    jwks_url = "https://example.com/.well-known/jwks.json"
    cache.set(JWKS_KEY, get_jwt_manager().get_jwks()["keys"], JWKS_CACHE_TIME)

    # tamper with the signature of an otherwise valid token so the real decoder
    # rejects it on signature verification
    header, payload, signature = create_access_token(customer_user).split(".")
    tampered_signature = ("A" if signature[0] != "A" else "B") + signature[1:]
    tampered_token = ".".join([header, payload, tampered_signature])

    # when
    result = decode_access_token(tampered_token, jwks_url)

    # then
    assert result is None
    assert "Invalid OIDC access token format" in caplog.text


def test_decode_access_token_valid_jwt_returns_payload(customer_user):
    # given
    jwks_url = "https://example.com/.well-known/jwks.json"
    cache.set(JWKS_KEY, get_jwt_manager().get_jwks()["keys"], JWKS_CACHE_TIME)
    token = create_access_token(customer_user)

    # when
    result = decode_access_token(token, jwks_url)

    # then
    assert result is not None
    assert result["email"] == customer_user.email


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
    assert not user_from_payload.has_usable_password()


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_clears_password_for_existing_user(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # When OIDC finds an existing user by email (not by sub), the old password
    # should be invalidated to prevent login with stale credentials.

    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|new-sub"
    assert customer_user.has_usable_password()

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user_from_payload, created, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )

    # then
    assert not created
    assert user_from_payload.id == customer_user.id
    assert not user_from_payload.has_usable_password()
    customer_user.refresh_from_db()
    assert not customer_user.has_usable_password()


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_keeps_password_for_returning_oidc_user(
    mocked_cache_get, mocked_cache_set, customer_user
):
    # When an existing OIDC user is found by email (cache miss on sub lookup),
    # the password should NOT be cleared since they already have the OIDC identity.

    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|existing-sub"
    oidc_key = f"oidc:{oauth_url}"
    customer_user.store_value_in_private_metadata({oidc_key: sub_id})
    customer_user.save(update_fields=["private_metadata"])
    assert customer_user.has_usable_password()

    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user_from_payload, created, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_user.email},
        oauth_url=oauth_url,
    )

    # then
    assert not created
    assert user_from_payload.id == customer_user.id
    assert user_from_payload.has_usable_password()


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
def test_get_or_create_user_from_payload_does_not_match_orders_for_existing_user(
    mocked_cache_get,
    _mocked_cache_set,
    customer_user,
    customer_user2,
    order,
    gift_card,
):
    """When a user already exists, it should NOT merge anonymous objects."""

    mocked_cache_get.side_effect = lambda cache_key: None

    # This user has the email address that 'login_as_user' user will use to login
    other_user = customer_user2
    other_email = other_user.email

    # The user that we are logging as
    login_as_user = customer_user
    original_email = login_as_user.email
    login_as_user.private_metadata = {"oidc:https://saleor.io/oauth": "oauth|1234"}
    login_as_user.save(update_fields=("private_metadata",))
    assert other_email != original_email

    perform_get_or_create = partial(
        get_or_create_user_from_payload,
        payload={"sub": "oauth|1234", "email": other_email},
        oauth_url="https://saleor.io/oauth",
    )

    # Create anonymous objects assigned to the targeted email
    order.user = gift_card.created_by = None
    order.user_email = gift_card.created_by_email = other_email
    gift_card.save(update_fields=["created_by", "created_by_email"])
    order.save(update_fields=["user", "user_email"])

    # Perform the call - it shouldn't attempt to associate the anonymous objects
    user_from_payload, created, _updated = perform_get_or_create()
    assert created is False, "should have found the user already exists"

    # Ensure we indeed did not merge the account with 'other_user'
    login_as_user.refresh_from_db(fields=("email",))
    assert login_as_user.email == original_email, "shouldn't have changed the email"

    order.refresh_from_db(fields=("user",))
    assert order.user is None, "shouldn't have associated the anonymous order"
    gift_card.refresh_from_db(fields=("created_by",))
    assert gift_card.created_by is None, (
        "shouldn't have associated the anonymous giftcard"
    )

    # Sanity check: if the user doesn't exist in DB, then it should merge
    # the anonymous objects
    other_user.delete()
    user_from_payload, created, _updated = perform_get_or_create()

    # Ensure we now updated the email address as it's no longer taken
    login_as_user.refresh_from_db(fields=("email",))
    assert login_as_user.email == other_email, "should have changed the email"

    assert created is False, "shouldn't have created a new user"
    order.refresh_from_db(fields=("user",))
    assert order.user == user_from_payload, "should have merged the order"
    gift_card.refresh_from_db(fields=("created_by",))
    assert gift_card.created_by is None, "shouldn't have merged the giftcard"


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


def test_get_or_create_user_from_payload_multiple_subs(
    mocker, customer_user, admin_user
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    oidc_metadata_key = f"oidc:{oauth_url}"
    cache_key = f"{oidc_metadata_key}:{sub_id}"
    mocked_cache_set = mocker.patch("saleor.plugins.openid_connect.utils.cache.set")
    mocked_cache_get = mocker.patch("saleor.plugins.openid_connect.utils.cache.get")

    customer_user.private_metadata = {oidc_metadata_key: sub_id}
    customer_user.save(update_fields=("private_metadata",))

    admin_user.private_metadata = {oidc_metadata_key: sub_id}
    admin_user.save(update_fields=("private_metadata",))
    mocked_cache_get.return_value = None

    # when
    with warnings.catch_warnings(record=True):
        user_from_payload, created, _ = get_or_create_user_from_payload(
            payload={"sub": sub_id, "email": customer_user.email},
            oauth_url=oauth_url,
        )

    # then
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.pk, OIDC_CACHE_TIMEOUT
    )
    assert created is False
    assert user_from_payload.pk == customer_user.pk
    assert user_from_payload.private_metadata[oidc_metadata_key] == sub_id


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


def test_get_or_create_user_from_payload_with_email_capitalization_change(
    mocker, customer_user
):
    """Email address changing capitalization shouldn't create a new user.

    When a given email address already exists and capitalization changed, then it
    shouldn't create a new user.
    """
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "member-live-1234"
    initial_email = "john.doe@example.com"
    capitalized_email = "John.doe@example.com"
    mocked_cache_set = mocker.patch("saleor.plugins.openid_connect.utils.cache.set")
    mocked_cache_get = mocker.patch("saleor.plugins.openid_connect.utils.cache.get")
    customer_user.email = initial_email
    customer_user.external_reference = sub_id
    customer_user.save(update_fields=("email", "external_reference"))
    mocked_cache_get.return_value = None

    # when
    user_from_payload, created, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": capitalized_email},
        oauth_url=oauth_url,
    )

    # then
    cache_key = f"oidc:{oauth_url}:{sub_id}"
    mocked_cache_get.assert_called_once_with(cache_key)
    mocked_cache_set.assert_called_once_with(
        cache_key, customer_user.pk, OIDC_CACHE_TIMEOUT
    )
    assert created is False
    assert user_from_payload.pk == customer_user.pk
    customer_user.refresh_from_db(fields=("email", "private_metadata"))
    assert customer_user.email == initial_email, "shouldn't have changed"
    assert customer_user.private_metadata[f"oidc:{oauth_url}"] == sub_id
    assert User.objects.filter(email__iexact=initial_email).count() == 1


@pytest.mark.parametrize(
    ("_case", "additional_emails"),
    [
        ("two_case_variants", ()),
        ("seven_case_variants", EXTRA_CASE_VARIANT_EMAILS),
    ],
)
def test_get_or_create_user_from_payload_preserves_exact_case_account(
    _case, additional_emails, mocker, customer_user, customer_user2
):
    """An OIDC claim should select the account with the exact email spelling.

    When users have emails that differ only by case, the incoming subject should
    be linked to the exact-case user without changing the other accounts.
    """
    # given
    oauth_url = "https://idp.example.com/oauth"
    claimed_email = "John.doe@example.com"
    lowercase_email = claimed_email.lower()
    sub_id = "member-live-1234"
    oidc_metadata_key = f"oidc:{oauth_url}"
    exact_match_user = customer_user
    other_case_user = customer_user2
    exact_match_user.email = claimed_email
    exact_match_user.save(update_fields=("email",))
    other_case_user.email = lowercase_email
    other_case_user.save(update_fields=("email",))
    User.objects.bulk_create([User(email=email) for email in additional_emails])
    assert User.objects.filter(email__iexact=claimed_email).count() == (
        2 + len(additional_emails)
    )
    assert oidc_metadata_key not in exact_match_user.private_metadata
    assert oidc_metadata_key not in other_case_user.private_metadata
    mocked_cache_get = mocker.patch(
        "saleor.plugins.openid_connect.utils.cache.get", return_value=None
    )
    mocked_cache_set = mocker.patch("saleor.plugins.openid_connect.utils.cache.set")

    # when
    user, created, updated = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": claimed_email},
        oauth_url=oauth_url,
    )

    # then
    assert created is False
    assert updated is True
    assert user.pk == exact_match_user.pk
    mocked_cache_get.assert_called_once_with(f"{oidc_metadata_key}:{sub_id}")
    mocked_cache_set.assert_called_once_with(
        f"{oidc_metadata_key}:{sub_id}", exact_match_user.pk, OIDC_CACHE_TIMEOUT
    )
    exact_match_user.refresh_from_db(fields=("email", "private_metadata"))
    other_case_user.refresh_from_db(fields=("email", "private_metadata"))
    assert exact_match_user.email == claimed_email
    assert exact_match_user.private_metadata[oidc_metadata_key] == sub_id
    assert other_case_user.email == lowercase_email
    assert oidc_metadata_key not in other_case_user.private_metadata
    # Across all case variants, only the exact-match account should be linked.
    assert list(
        User.objects.filter(
            email__iexact=claimed_email,
            private_metadata__has_key=oidc_metadata_key,
        ).values_list("pk", flat=True)
    ) == [exact_match_user.pk]


@pytest.mark.parametrize(
    ("_case", "additional_emails"),
    [
        ("two_case_variants", ()),
        ("seven_case_variants", EXTRA_CASE_VARIANT_EMAILS),
    ],
)
def test_get_or_create_user_from_payload_rejects_ambiguous_case_variants(
    _case, additional_emails, mocker, customer_user, customer_user2
):
    """An ambiguous email claim should not link any case-variant account.

    When the claim matches multiple users case-insensitively but neither exactly,
    authentication should fail without changing their passwords or OIDC metadata.
    """
    # given
    oauth_url = "https://idp.example.com/oauth"
    claimed_email = "JOHN.DOE@example.com"
    capitalized_email = "John.doe@example.com"
    lowercase_email = claimed_email.lower()
    sub_id = "member-live-1234"
    oidc_metadata_key = f"oidc:{oauth_url}"
    capitalized_user = customer_user
    lowercase_user = customer_user2
    capitalized_user.email = capitalized_email
    capitalized_user.save(update_fields=("email",))
    lowercase_user.email = lowercase_email
    lowercase_user.save(update_fields=("email",))
    User.objects.bulk_create([User(email=email) for email in additional_emails])
    assert User.objects.filter(email=claimed_email).exists() is False
    assert User.objects.filter(email__iexact=claimed_email).count() == (
        2 + len(additional_emails)
    )
    capitalized_user_password = capitalized_user.password
    lowercase_user_password = lowercase_user.password
    mocked_cache_get = mocker.patch(
        "saleor.plugins.openid_connect.utils.cache.get", return_value=None
    )
    mocked_cache_set = mocker.patch("saleor.plugins.openid_connect.utils.cache.set")

    # when
    with pytest.raises(
        AuthenticationError, match="Unable to identify an account for this email."
    ):
        get_or_create_user_from_payload(
            payload={"sub": sub_id, "email": claimed_email},
            oauth_url=oauth_url,
        )

    # then
    mocked_cache_get.assert_called_once_with(f"{oidc_metadata_key}:{sub_id}")
    mocked_cache_set.assert_not_called()
    capitalized_user.refresh_from_db(fields=("password", "private_metadata"))
    lowercase_user.refresh_from_db(fields=("password", "private_metadata"))
    assert capitalized_user.password == capitalized_user_password
    assert oidc_metadata_key not in capitalized_user.private_metadata
    assert lowercase_user.password == lowercase_user_password
    assert oidc_metadata_key not in lowercase_user.private_metadata
    # All case-variant accounts, including the extra five, must remain unlinked.
    assert (
        User.objects.filter(
            email__iexact=claimed_email,
            private_metadata__has_key=oidc_metadata_key,
        ).exists()
        is False
    )


def test_get_or_create_user_recovers_from_integrity_error(mocker, customer_user):
    """Should handle raced-user creation.

    When user didn't exist but got created before our code could create it (race),
    then it should properly return the user created by the other process.
    """
    # given
    email = customer_user.email
    defaults = {"email": email}
    mocked_create = mocker.patch(
        "saleor.plugins.openid_connect.utils.User.objects.create",
        side_effect=IntegrityError("duplicate key value"),
    )
    mocked_retrieve_user_by_email = mocker.patch(
        "saleor.plugins.openid_connect.utils._retrieve_oidc_user_by_email",
        side_effect=[None, customer_user],
    )

    # when
    user, created = _get_or_create_user(email, defaults)

    # then
    mocked_create.assert_called_once_with(**defaults)
    assert mocked_retrieve_user_by_email.call_count == 2
    assert created is False
    assert user.pk == customer_user.pk


def test_get_or_create_user_reraises_unrecoverable_integrity_error(mocker):
    """Should properly handle a race where newly crated user is not retrievable.

    When user didn't exist and then got created in the meantime and then got deleted
    or we couldn't fetch it successfully, then Saleor should raise an error
    due to not being recoverable.
    """
    # given
    email = "john.doe@example.com"
    defaults = {"email": email}
    error_message = "duplicate key value"
    mocked_create = mocker.patch(
        "saleor.plugins.openid_connect.utils.User.objects.create",
        side_effect=IntegrityError(error_message),
    )
    mocked_retrieve_user_by_email = mocker.patch(
        "saleor.plugins.openid_connect.utils._retrieve_oidc_user_by_email",
        return_value=None,
    )

    # when
    with pytest.raises(IntegrityError, match=error_message):
        _get_or_create_user(email, defaults)

    # then
    mocked_create.assert_called_once_with(**defaults)
    assert mocked_retrieve_user_by_email.call_count == 2


def test_get_or_create_user_selects_exact_email_from_case_variants(
    customer_user, customer_user2
):
    """An exact claim identifies one account among case-variant users.

    When both email spellings exist, the email lookup should return the user
    whose stored email matches the claim exactly.
    """
    # given
    capitalized_email = "John.doe@example.com"
    lowercase_email = capitalized_email.lower()
    customer_user.email = capitalized_email
    customer_user.save(update_fields=("email",))
    customer_user2.email = lowercase_email
    customer_user2.save(update_fields=("email",))

    # when
    user, created = _get_or_create_user(capitalized_email, {})

    # then
    assert created is False
    assert user.pk == customer_user.pk


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
    mock_logger,
    mock_match_orders_with_new_user,
    customer_user,
    customer_user2,
    order,
    gift_card,
):
    """When a user already exists, it shouldn't merge anonymous objects."""

    existing_user = customer_user2
    existing_email = existing_user.email

    update_details = partial(
        _update_user_details,
        user=customer_user,
        oidc_key="test oidc_key",
        user_email=existing_email,
        user_first_name=customer_user.first_name,
        user_last_name=customer_user.last_name,
        sub="test oidc_sub",
        last_login=customer_user.last_login,
    )

    # Create anonymous objects assigned to the targeted email
    order.user = gift_card.created_by = None
    order.user_email = gift_card.created_by_email = existing_email
    gift_card.save(update_fields=["created_by", "created_by_email"])
    order.save(update_fields=["user", "user_email"])

    # given
    assert customer_user.email != customer_user2.email

    # when
    update_details()

    # then
    customer_user.refresh_from_db()
    assert customer_user.email != existing_email
    assert mock_logger.mock_calls == [
        call.warning(
            "Unable to update user email as the new one already exists in DB",
            extra={"oidc_key": "test oidc_key"},
        )
    ]
    mock_match_orders_with_new_user.assert_not_called()

    # Sanity check: if the user doesn't exist in DB, then it should merge
    # the anonymous objects
    existing_user.delete()
    update_details()
    customer_user.refresh_from_db(fields=("email",))
    assert customer_user.email == existing_email, "should have changed the email"
    mock_match_orders_with_new_user.assert_called_once_with(customer_user)


@patch(
    "saleor.plugins.openid_connect.utils.update_user_search_vector",
    wraps=update_user_search_vector,
)
def test_update_user_details_update_user_first_name(
    update_user_search_vector_mock,
    customer_user,
):
    # given
    assert customer_user.first_name != "test user_first_name"

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
    assert customer_user.search_vector
    assert updated is True
    update_user_search_vector_mock.assert_called_once()


@patch(
    "saleor.plugins.openid_connect.utils.update_user_search_vector",
    wraps=update_user_search_vector,
)
def test_update_user_details_update_user_last_name(
    update_user_search_vector_mock,
    customer_user,
):
    # given
    assert customer_user.last_name != "test user_last_name"

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
    assert customer_user.search_vector
    assert updated is True
    update_user_search_vector_mock.assert_called_once()


@patch(
    "saleor.plugins.openid_connect.utils.update_user_search_vector",
    wraps=update_user_search_vector,
)
def test_update_user_details_nothing_changed(
    update_user_search_vector_mock,
    customer_user,
):
    # given
    last_login = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(minutes=14)
    customer_user.last_login = last_login
    update_user_search_vector(customer_user, save=False)
    customer_user.save(update_fields=["search_vector", "last_login"])

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
    update_user_search_vector_mock.assert_not_called()


@mock.patch("saleor.plugins.openid_connect.utils.cache.set")
@mock.patch("saleor.plugins.openid_connect.utils.cache.get")
def test_get_or_create_user_from_payload_assigns_default_customer_type(
    mocked_cache_get, mocked_cache_set, default_customer_type
):
    # given
    oauth_url = "https://saleor.io/oauth"
    sub_id = "oauth|1234"
    customer_email = "email.customer@example.com"
    mocked_cache_get.side_effect = lambda cache_key: None

    # when
    user_from_payload, created, _ = get_or_create_user_from_payload(
        payload={"sub": sub_id, "email": customer_email},
        oauth_url=oauth_url,
    )

    # then
    assert created is True
    assert user_from_payload.customer_type == default_customer_type
