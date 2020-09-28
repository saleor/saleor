from unittest.mock import MagicMock, Mock
from urllib.parse import parse_qs, urlparse

import pytest
from authlib.jose.errors import JoseError
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.middleware.csrf import _get_new_csrf_token
from freezegun import freeze_time

from saleor.account.models import User
from saleor.core.jwt import JWT_REFRESH_TOKEN_COOKIE_NAME, jwt_decode

from ..utils import create_jwt_refresh_token, get_valid_auth_tokens_from_auth_payload


def test_get_oauth_session_adds_refresh_scope_when_enabled(openid_plugin):
    plugin = openid_plugin(enable_refresh_token=True)
    session = plugin._get_oauth_session()
    assert "offline_access" in session.scope


def test_get_oauth_session_dont_add_refresh_scope_when_disabled(openid_plugin):
    plugin = openid_plugin(enable_refresh_token=False)
    session = plugin._get_oauth_session()
    assert "offline_access" not in session.scope


def test_external_authentication_returns_redirect_url(openid_plugin, settings):
    settings.ALLOWED_CLIENT_HOSTS = ["*"]
    authorize_path = "/authorize"
    domain = "saleor-test.eu.auth0.com"
    authorize_url = f"https://{domain}{authorize_path}"
    client_id = "test_client"
    plugin = openid_plugin(oauth_authorization_url=authorize_url, client_id=client_id)
    input = {"redirectUrl": "http://localhost:3000/authorization/"}
    response = plugin.external_authentication(input, None)
    assert isinstance(response, dict)
    auth_url = response.get("authorizationUrl")
    parsed_url = urlparse(auth_url)
    parsed_qs = parse_qs(parsed_url.query)
    expected_redirect_url = (
        "http://mirumee.com/plugins/mirumee.authentication.openidconnect/callback?"
        "redirectUrl=http%3A%2F%2Flocalhost%3A3000%2Fauthorization%2F"
    )
    assert parsed_url.netloc == domain
    assert parsed_url.path == authorize_path
    assert parsed_qs["redirect_uri"][0] == expected_redirect_url
    assert parsed_qs["client_id"][0] == client_id


def test_external_authentication_raises_error_when_missing_redirect(openid_plugin):
    client_id = "test_client"
    plugin = openid_plugin(client_id=client_id)
    input = {}
    with pytest.raises(ValidationError):
        plugin.external_authentication(input, None)


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_from_cookie(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.jwt.decode",
        Mock(return_value=mocked_jwt_validator),
    )
    oauth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "new_refresh",
        "id_token": id_token,
        "scope": "openid profile email offline_access",
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    mocked_refresh_token = Mock(return_value=oauth_payload)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.OAuth2Session.refresh_token",
        mocked_refresh_token,
    )

    oauth_refresh_token = "refresh"
    plugin = openid_plugin()
    csrf_token = _get_new_csrf_token()
    saleor_refresh_token = create_jwt_refresh_token(
        admin_user, oauth_refresh_token, csrf_token
    )
    request = rf.request()
    request.COOKIES[JWT_REFRESH_TOKEN_COOKIE_NAME] = saleor_refresh_token

    data = {"csrfToken": csrf_token}
    response = plugin.external_refresh(data, request, None)

    assert "token" in response
    assert "refreshToken" in response
    assert "csrfToken" in response

    decoded_token = jwt_decode(response.get("token"))
    assert decoded_token["exp"] == id_payload["exp"]
    assert decoded_token["oauth_access_key"] == oauth_payload["access_token"]

    decoded_refresh_token = jwt_decode(response.get("refreshToken"))
    assert decoded_refresh_token["oauth_refresh_token"] == "new_refresh"
    assert decoded_refresh_token["csrf_token"] == response["csrfToken"]
    mocked_refresh_token.assert_called_once_with(
        "https://saleor-test.eu.auth0.com/oauth/token",
        refresh_token=oauth_refresh_token,
    )


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_from_input(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.jwt.decode",
        Mock(return_value=mocked_jwt_validator),
    )
    oauth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "new_refresh",
        "id_token": id_token,
        "scope": "openid profile email offline_access",
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    mocked_refresh_token = Mock(return_value=oauth_payload)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.OAuth2Session.refresh_token",
        mocked_refresh_token,
    )

    oauth_refresh_token = "refresh"
    plugin = openid_plugin()
    csrf_token = _get_new_csrf_token()
    saleor_refresh_token = create_jwt_refresh_token(
        admin_user, oauth_refresh_token, csrf_token
    )

    request = rf.request()
    data = {"refreshToken": saleor_refresh_token}
    response = plugin.external_refresh(data, request, None)

    assert "token" in response
    assert "refreshToken" in response
    assert "csrfToken" in response

    decoded_token = jwt_decode(response.get("token"))
    assert decoded_token["exp"] == id_payload["exp"]
    assert decoded_token["oauth_access_key"] == oauth_payload["access_token"]

    decoded_refresh_token = jwt_decode(response.get("refreshToken"))
    assert decoded_refresh_token["oauth_refresh_token"] == "new_refresh"
    assert decoded_refresh_token["csrf_token"] == response["csrfToken"]
    mocked_refresh_token.assert_called_once_with(
        "https://saleor-test.eu.auth0.com/oauth/token",
        refresh_token=oauth_refresh_token,
    )


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_raises_error_when_token_is_invalid(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.jwt.decode", Mock(side_effect=JoseError())
    )
    oauth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "new_refresh",
        "id_token": id_token,
        "scope": "openid profile email offline_access",
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    mocked_refresh_token = Mock(return_value=oauth_payload)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.OAuth2Session.refresh_token",
        mocked_refresh_token,
    )

    oauth_refresh_token = "refresh"
    plugin = openid_plugin()
    csrf_token = _get_new_csrf_token()
    saleor_refresh_token = create_jwt_refresh_token(
        admin_user, oauth_refresh_token, csrf_token
    )

    request = rf.request()
    data = {"refreshToken": saleor_refresh_token}
    with pytest.raises(ValidationError):
        plugin.external_refresh(data, request, None)


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_raises_error(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):

    plugin = openid_plugin()
    csrf_token = _get_new_csrf_token()
    oauth_refresh_token = "refresh"
    saleor_refresh_token = create_jwt_refresh_token(
        admin_user, oauth_refresh_token, csrf_token
    )
    request = rf.request()
    request.COOKIES[JWT_REFRESH_TOKEN_COOKIE_NAME] = saleor_refresh_token

    data = {"csrfToken": csrf_token}
    with pytest.raises(ValidationError):
        plugin.external_refresh(data, request, None)


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_incorrect_csrf(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):
    plugin = openid_plugin()
    csrf_token = _get_new_csrf_token()
    oauth_refresh_token = "refresh"
    saleor_refresh_token = create_jwt_refresh_token(
        admin_user, oauth_refresh_token, csrf_token
    )
    request = rf.request()
    request.COOKIES[JWT_REFRESH_TOKEN_COOKIE_NAME] = saleor_refresh_token

    data = {"csrfToken": "incorrect"}
    with pytest.raises(ValidationError):
        plugin.external_refresh(data, request, None)


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_handle_oauth_callback(openid_plugin, monkeypatch, rf, id_token, id_payload):

    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.jwt.decode",
        Mock(return_value=mocked_jwt_validator),
    )
    oauth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "id_token": id_token,
        "scope": "openid profile email offline_access",
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    mocked_fetch_token = Mock(return_value=oauth_payload)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.OAuth2Session.fetch_token",
        mocked_fetch_token,
    )
    storefront_redirect_url = "http://localhost:3000/used-logged-in"
    request = rf.get(f"/callback?redirectUrl={storefront_redirect_url}")
    plugin = openid_plugin()

    redirect_response = plugin.handle_auth_callback(request)

    # new user created
    User.objects.get(email=id_payload["email"])

    expected_auth_response = (
        "http://testserver/callback?redirectUrl=http://localhost:3000/used-logged-in"
    )
    expected_redirect_uri = (
        "http://mirumee.com/plugins/mirumee.authentication.openidconnect/callback"
    )
    mocked_fetch_token.assert_called_once_with(
        "https://saleor-test.eu.auth0.com/oauth/token",
        authorization_response=expected_auth_response,
        redirect_uri=expected_redirect_uri,
    )

    assert isinstance(redirect_response, HttpResponseRedirect)
    redirect_url = redirect_response.url
    parsed_url = urlparse(redirect_url)
    parsed_qs = parse_qs(parsed_url.query)
    expected_tokens = get_valid_auth_tokens_from_auth_payload(
        oauth_payload, plugin.config.json_web_key_set_url,
    )
    assert parsed_url.netloc == "localhost:3000"
    assert parsed_url.path == "/used-logged-in"
    assert set(parsed_qs.keys()) == set(["token", "refreshToken", "csrfToken"])
    assert parsed_qs["token"][0] == expected_tokens["token"]
    decoded_refresh_token = jwt_decode(parsed_qs["refreshToken"][0])
    assert parsed_qs["csrfToken"][0] == decoded_refresh_token["csrf_token"]
    assert decoded_refresh_token["oauth_refresh_token"] == "refresh"


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_handle_oauth_callback_missing_redirect_url(
    openid_plugin, monkeypatch, rf, id_token, id_payload
):
    request = rf.get(f"/callback")
    plugin = openid_plugin()

    redirect_response = plugin.handle_auth_callback(request)
    assert redirect_response.status_code == 400

    # new user created
    assert not User.objects.filter(email=id_payload["email"]).first()
