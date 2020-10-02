from unittest.mock import MagicMock, Mock
from urllib.parse import parse_qs, urlparse

import pytest
from authlib.jose.errors import JoseError
from django.core import signing
from django.core.exceptions import ValidationError
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.middleware.csrf import _get_new_csrf_token
from freezegun import freeze_time

from saleor.account.models import User
from saleor.core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    PERMISSIONS_FIELD,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)

from ...models import PluginConfiguration
from ..utils import (
    create_jwt_refresh_token,
    create_jwt_token,
    create_tokens_from_oauth_payload,
    get_or_create_user_from_token,
    get_parsed_id_token,
)


def test_get_oauth_session_adds_refresh_scope_when_enabled(openid_plugin):
    plugin = openid_plugin(enable_refresh_token=True)
    session = plugin._get_oauth_session()
    assert "offline_access" in session.scope


def test_get_oauth_session_dont_add_refresh_scope_when_disabled(openid_plugin):
    plugin = openid_plugin(enable_refresh_token=False)
    session = plugin._get_oauth_session()
    assert "offline_access" not in session.scope


def test_external_authentication_returns_redirect_url(openid_plugin, settings, rf):
    settings.ALLOWED_CLIENT_HOSTS = ["*"]
    authorize_path = "/authorize"
    domain = "saleor-test.eu.auth0.com"
    authorize_url = f"https://{domain}{authorize_path}"
    client_id = "test_client"
    plugin = openid_plugin(oauth_authorization_url=authorize_url, client_id=client_id)

    storefront_redirect_url = "http://localhost:3000/authorization/"
    input = {"redirectUrl": storefront_redirect_url}
    response = plugin.external_authentication(input, rf.request(), None)
    assert isinstance(response, dict)
    auth_url = response.get("authorizationUrl")
    parsed_url = urlparse(auth_url)
    parsed_qs = parse_qs(parsed_url.query)
    expected_redirect_url = (
        "http://mirumee.com/plugins/mirumee.authentication.openidconnect/callback"
    )
    state = signing.loads(parsed_qs["state"][0])
    assert parsed_url.netloc == domain
    assert parsed_url.path == authorize_path
    assert parsed_qs["redirect_uri"][0] == expected_redirect_url
    assert parsed_qs["client_id"][0] == client_id
    assert state["redirectUrl"] == storefront_redirect_url


def test_external_authentication_plugin_disabled(openid_plugin, rf):
    plugin = openid_plugin(active=False)
    input = {"redirectUrl": "http://localhost:3000/authorization/"}
    previous_value = "previous"
    response = plugin.external_authentication(input, rf.request(), previous_value)
    assert response == previous_value


def test_external_authentication_raises_error_when_missing_redirect(openid_plugin, rf):
    client_id = "test_client"
    plugin = openid_plugin(client_id=client_id)
    input = {}
    with pytest.raises(ValidationError):
        plugin.external_authentication(input, rf.request(), None)


def test_external_authentication_raises_error_when_redirect_is_wrong(openid_plugin, rf):
    client_id = "test_client"
    plugin = openid_plugin(client_id=client_id)
    input = {"redirectUrl": "localhost:3000/authorization/"}
    with pytest.raises(ValidationError):
        plugin.external_authentication(input, rf.request(), None)


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
        admin_user, oauth_refresh_token, csrf_token, plugin.PLUGIN_ID
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
        admin_user, oauth_refresh_token, csrf_token, plugin.PLUGIN_ID
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
        admin_user, oauth_refresh_token, csrf_token, plugin.PLUGIN_ID
    )

    request = rf.request()
    data = {"refreshToken": saleor_refresh_token}
    with pytest.raises(ValidationError):
        plugin.external_refresh(data, request, None)


@freeze_time("2019-03-18 12:00:00")
def test_external_refresh_disabled_refreshing(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):
    plugin = openid_plugin(enable_refresh_token=False)

    request = rf.request()
    data = {"refreshToken": "ABC"}
    with pytest.raises(ValidationError):
        plugin.external_refresh(data, request, None)


def test_external_refresh_when_plugin_is_disabled(openid_plugin, rf):
    request = rf.request()
    data = {"refreshToken": "token"}
    plugin = openid_plugin(active=False)
    previous_value = "previous"
    plugin.external_refresh(data, request, previous_value)


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_raises_error(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):

    plugin = openid_plugin()
    csrf_token = _get_new_csrf_token()
    oauth_refresh_token = "refresh"
    saleor_refresh_token = create_jwt_refresh_token(
        admin_user, oauth_refresh_token, csrf_token, plugin.PLUGIN_ID
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
        admin_user, oauth_refresh_token, csrf_token, plugin.PLUGIN_ID
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
    mocked_jwt_validator.get.side_effect = id_payload.get

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
    state = signing.dumps({"redirectUrl": storefront_redirect_url})
    request = rf.get(f"/callback?state={state}")
    plugin = openid_plugin()

    redirect_response = plugin.handle_auth_callback(request)

    # new user created
    User.objects.get(email=id_payload["email"])

    expected_auth_response = f"http://testserver/callback?state={state}"
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
    claims = get_parsed_id_token(oauth_payload, plugin.config.json_web_key_set_url,)
    user = get_or_create_user_from_token(claims)
    expected_tokens = create_tokens_from_oauth_payload(
        oauth_payload, user, claims, permissions=[], owner=plugin.PLUGIN_ID
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
    request = rf.get("/callback")
    plugin = openid_plugin()

    redirect_response = plugin.handle_auth_callback(request)
    assert redirect_response.status_code == 400

    # new user created
    assert not User.objects.filter(email=id_payload["email"]).first()


test_url = "http://saleor.auth.com/"


@pytest.mark.parametrize(
    "c_id,c_secret,authorization_url,token_url,jwks_url,",
    (
        ["", "ss", f"{test_url}auth", f"{test_url}token", f"{test_url}jwks"],
        ["cc", "", f"{test_url}auth", f"{test_url}token", f"{test_url}jwks"],
        ["cc", "123", "", f"{test_url}token", f"{test_url}jwks"],
        ["cc", "123", f"{test_url}auth", "", f"{test_url}jwks"],
        ["cc", "123", f"{test_url}auth", f"{test_url}token", ""],
        ["cc", "123", "saleor.auth.com/auth", f"{test_url}token", f"{test_url}token"],
        ["cc", "123", f"{test_url}auth", "http://", f"{test_url}token"],
        ["cc", "123", f"{test_url}auth", "http://", f"{test_url}token"],
        ["cc", "123", "not_url", f"{test_url}token", f"{test_url}token"],
        ["cc", "123", "", "", ""],
    ),
)
def test_validate_plugin_configuration_raises_error(
    c_id,
    c_secret,
    authorization_url,
    token_url,
    jwks_url,
    plugin_configuration,
    openid_plugin,
):
    configuration = plugin_configuration(
        client_id=c_id,
        client_secret=c_secret,
        enable_refresh_token=True,
        oauth_authorization_url=authorization_url,
        oauth_token_url=token_url,
        json_web_key_set_url=jwks_url,
    )
    conf = PluginConfiguration(active=True, configuration=configuration)
    plugin = openid_plugin()
    with pytest.raises(ValidationError):
        plugin.validate_plugin_configuration(conf)


def test_validate_plugin_configuration(plugin_configuration, openid_plugin):
    configuration = plugin_configuration(
        client_id="c_id",
        client_secret="c_secret",
        enable_refresh_token=True,
        oauth_authorization_url="http://saleor.auth.com/auth",
        oauth_token_url="http://saleor.auth.com/token",
        json_web_key_set_url="http://saleor.auth.com/jwks",
    )
    conf = PluginConfiguration(active=True, configuration=configuration)
    plugin = openid_plugin()
    plugin.validate_plugin_configuration(conf)


def test_external_logout_missing_logouat_url(openid_plugin, rf):
    plugin = openid_plugin(oauth_logout_url="")
    response = plugin.external_logout({}, rf.request(), None)
    assert response == {}


def test_external_logout(openid_plugin, rf):
    client_id = "AVC"
    domain = "saleor.auth.com"
    path = "/logout"
    plugin = openid_plugin(oauth_logout_url=f"http://{domain}{path}?client_id=AVC")
    input_data = {"redirectUrl": "http://localhost:3000/logout", "field1": "value1"}
    response = plugin.external_logout(input_data, rf.request(), None)
    logout_url = response["logoutUrl"]

    parsed_url = urlparse(logout_url)
    parsed_qs = parse_qs(parsed_url.query)
    assert parsed_url.netloc == domain
    assert parsed_url.path == path
    assert parsed_qs["redirectUrl"][0] == "http://localhost:3000/logout"
    assert parsed_qs["field1"][0] == "value1"
    assert parsed_qs["client_id"][0] == client_id


def test_webhook_when_plugin_is_disabled(openid_plugin, rf):
    plugin = openid_plugin(active=False)
    response = plugin.webhook(rf.request(), "/callback?some=value", None)
    assert isinstance(response, HttpResponseNotFound)


def test_webhook_wrong_path(openid_plugin, rf):
    plugin = openid_plugin(active=True)
    response = plugin.webhook(rf.request(), "/wrong?some=value", None)
    assert isinstance(response, HttpResponseNotFound)


def test_webhook_calls_callback(openid_plugin, rf, monkeypatch):
    mocked_callback = Mock()
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.OpenIDConnectPlugin.handle_auth_callback",
        mocked_callback,
    )
    plugin = openid_plugin(active=True)
    request = rf.request()
    plugin.webhook(request, "/callback?some=value", None)
    mocked_callback.assert_called_once_with(request)


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user(openid_plugin, id_payload, customer_user, monkeypatch, rf):
    plugin = openid_plugin()
    token = create_jwt_token(
        id_payload,
        customer_user,
        access_token="access",
        permissions=[],
        owner=plugin.PLUGIN_ID,
    )
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request", lambda _: token
    )
    user = plugin.authenticate_user(rf.request(), None)
    assert user == customer_user


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user_wrong_owner(
    openid_plugin, id_payload, customer_user, staff_user, monkeypatch, rf
):
    plugin = openid_plugin()
    token = create_jwt_token(
        id_payload,
        customer_user,
        access_token="access",
        permissions=[],
        owner="DifferentPlugin",
    )
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request", lambda _: token
    )
    user = plugin.authenticate_user(rf.request(), previous_value=staff_user)
    assert user == staff_user


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user_missing_owner(
    openid_plugin, id_payload, customer_user, monkeypatch, rf
):
    plugin = openid_plugin()
    additional_payload = {
        "exp": id_payload["exp"],
        "oauth_access_key": "access",
        PERMISSIONS_FIELD: [],
    }
    jwt_payload = jwt_user_payload(
        customer_user,
        JWT_ACCESS_TYPE,
        exp_delta=None,
        additional_payload=additional_payload,
    )
    token = jwt_encode(jwt_payload)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request", lambda _: token
    )
    user = plugin.authenticate_user(rf.request(), None)
    assert user is None


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user_missing_token_in_request(openid_plugin, id_payload, rf):
    plugin = openid_plugin()
    user = plugin.authenticate_user(rf.request(), None)
    assert user is None


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user_unable_to_decode_token(
    openid_plugin, id_payload, customer_user, monkeypatch, rf
):
    plugin = openid_plugin()
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request", lambda _: "ABC"
    )
    user = plugin.authenticate_user(rf.request(), None)
    assert user is None


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user_staff_user_with_effective_permissions(
    openid_plugin,
    id_payload,
    staff_user,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_checkouts,
    permission_manage_gift_card,
    monkeypatch,
    rf,
):
    plugin = openid_plugin()
    staff_user.user_permissions.add(
        permission_manage_gift_card, permission_manage_checkouts
    )
    permissions = ["MANAGE_USERS", "MANAGE_ORDERS"]
    token = create_jwt_token(
        id_payload,
        staff_user,
        access_token="access",
        permissions=permissions,
        owner=plugin.PLUGIN_ID,
    )
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request", lambda _: token
    )
    user = plugin.authenticate_user(rf.request(), None)
    assert user == staff_user
    assert set(user.effective_permissions) == {
        permission_manage_orders,
        permission_manage_users,
    }
