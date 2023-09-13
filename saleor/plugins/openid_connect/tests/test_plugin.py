from unittest.mock import MagicMock, Mock
from urllib.parse import parse_qs, urlparse

import pytest
from authlib.integrations.base_client.errors import OAuthError
from authlib.jose.errors import JoseError
from django.core import signing
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from ....account.models import Group
from ....core.jwt import (
    JWT_ACCESS_TYPE,
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    PERMISSIONS_FIELD,
    jwt_decode,
    jwt_encode,
    jwt_user_payload,
)
from ....graphql.account.mutations.authentication.utils import _get_new_csrf_token
from ...base_plugin import ExternalAccessTokens
from ...models import PluginConfiguration
from ..utils import (
    create_jwt_refresh_token,
    create_jwt_token,
    create_tokens_from_oauth_payload,
    get_or_create_user_from_payload,
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


def test_external_authentication_url_returns_redirect_url(openid_plugin, settings, rf):
    settings.ALLOWED_CLIENT_HOSTS = ["*"]
    authorize_path = "/authorize"
    domain = "saleor.io"
    authorize_url = f"https://{domain}{authorize_path}"
    client_id = "test_client"
    plugin = openid_plugin(oauth_authorization_url=authorize_url, client_id=client_id)

    redirect_uri = "http://localhost:3000/oauth-callback/"
    input = {"redirectUri": redirect_uri}
    response = plugin.external_authentication_url(input, rf.request(), None)
    assert isinstance(response, dict)
    auth_url = response.get("authorizationUrl")
    parsed_url = urlparse(auth_url)
    parsed_qs = parse_qs(parsed_url.query)
    state = signing.loads(parsed_qs["state"][0])
    assert parsed_url.netloc == domain
    assert parsed_url.path == authorize_path
    assert parsed_qs["redirect_uri"][0] == redirect_uri
    assert parsed_qs["client_id"][0] == client_id
    assert state["redirectUri"] == redirect_uri


def test_external_authentication_plugin_disabled(openid_plugin, rf):
    plugin = openid_plugin(active=False)
    input = {"redirectUrl": "http://localhost:3000/authorization/"}
    previous_value = "previous"
    response = plugin.external_authentication_url(input, rf.request(), previous_value)
    assert response == previous_value


def test_external_authentication_raises_error_when_missing_redirect(openid_plugin, rf):
    client_id = "test_client"
    plugin = openid_plugin(client_id=client_id)
    input = {}
    with pytest.raises(ValidationError):
        plugin.external_authentication_url(input, rf.request(), None)


def test_external_authentication_raises_error_when_redirect_is_wrong(openid_plugin, rf):
    client_id = "test_client"
    plugin = openid_plugin(client_id=client_id)
    input = {"redirectUrl": "localhost:3000/authorization/"}
    with pytest.raises(ValidationError):
        plugin.external_authentication_url(input, rf.request(), None)


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_from_cookie(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__
    mocked_jwt_validator.get.side_effect = id_payload.get

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
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
        "saleor.plugins.openid_connect.client.OAuth2Client.refresh_token",
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

    decoded_token = jwt_decode(response.token)
    assert decoded_token["exp"] == id_payload["exp"]
    assert decoded_token["oauth_access_key"] == oauth_payload["access_token"]

    decoded_refresh_token = jwt_decode(response.refresh_token)
    assert decoded_refresh_token["oauth_refresh_token"] == "new_refresh"
    assert decoded_refresh_token["csrf_token"] == response.csrf_token
    mocked_refresh_token.assert_called_once_with(
        "https://saleor.io/oauth/token",
        refresh_token=oauth_refresh_token,
    )


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_from_input(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__
    mocked_jwt_validator.get.side_effect = id_payload.get

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
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
        "saleor.plugins.openid_connect.client.OAuth2Client.refresh_token",
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

    decoded_token = jwt_decode(response.token)
    assert decoded_token["exp"] == id_payload["exp"]
    assert decoded_token["oauth_access_key"] == oauth_payload["access_token"]

    decoded_refresh_token = jwt_decode(response.refresh_token)
    assert decoded_refresh_token["oauth_refresh_token"] == "new_refresh"
    assert decoded_refresh_token["csrf_token"] == response.csrf_token
    mocked_refresh_token.assert_called_once_with(
        "https://saleor.io/oauth/token",
        refresh_token=oauth_refresh_token,
    )


@freeze_time("2019-03-18 12:00:00")
def test_external_refresh_with_scope_permissions(
    openid_plugin,
    admin_user,
    monkeypatch,
    rf,
    id_token,
    id_payload,
    permission_manage_users,
):
    # given
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__
    mocked_jwt_validator.get.side_effect = id_payload.get

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_parsed_id_token",
        Mock(return_value=mocked_jwt_validator),
    )
    oauth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "new_refresh",
        "id_token": id_token,
        "scope": (
            "openid profile email offline_access saleor:manage_orders saleor:staff"
        ),
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    mocked_refresh_token = Mock(return_value=oauth_payload)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.client.OAuth2Client.refresh_token",
        mocked_refresh_token,
    )

    oauth_refresh_token = "refresh"
    plugin = openid_plugin(use_oauth_scope_permissions=True)
    csrf_token = _get_new_csrf_token()
    saleor_refresh_token = create_jwt_refresh_token(
        admin_user, oauth_refresh_token, csrf_token, plugin.PLUGIN_ID
    )
    group = Group.objects.create(name=plugin.config.default_group_name)
    group.permissions.add(permission_manage_users)
    admin_user.groups.add(group)

    request = rf.request()
    data = {"refreshToken": saleor_refresh_token}

    # when
    response = plugin.external_refresh(data, request, None)

    # then
    decoded_token = jwt_decode(response.token)
    assert decoded_token["exp"] == id_payload["exp"]
    assert decoded_token["oauth_access_key"] == oauth_payload["access_token"]
    assert set(decoded_token["permissions"]) == {"MANAGE_ORDERS", "MANAGE_USERS"}

    decoded_refresh_token = jwt_decode(response.refresh_token)
    assert decoded_refresh_token["oauth_refresh_token"] == "new_refresh"
    assert decoded_refresh_token["csrf_token"] == response.csrf_token
    mocked_refresh_token.assert_called_once_with(
        "https://saleor.io/oauth/token",
        refresh_token=oauth_refresh_token,
    )

    user = response.user
    assert user.is_staff
    assert permission_manage_users in user.effective_permissions


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_refresh_raises_error_when_token_is_invalid(
    openid_plugin, admin_user, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        Mock(side_effect=JoseError()),
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
        "saleor.plugins.openid_connect.client.OAuth2Client.refresh_token",
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
def test_external_obtain_access_tokens(
    openid_plugin, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__
    mocked_jwt_validator.get.side_effect = id_payload.get

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        Mock(return_value=mocked_jwt_validator),
    )
    plugin = openid_plugin(use_oauth_scope_permissions=True)
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
        "saleor.plugins.openid_connect.client.OAuth2Client.fetch_token",
        mocked_fetch_token,
    )
    redirect_uri = "http://localhost:3000/used-logged-in"
    state = signing.dumps({"redirectUri": redirect_uri})
    code = "oauth-code"
    tokens = plugin.external_obtain_access_tokens(
        {"state": state, "code": code}, rf.request(), previous_value=None
    )

    mocked_fetch_token.assert_called_once_with(
        "https://saleor.io/oauth/token",
        code=code,
        redirect_uri=redirect_uri,
    )

    claims = get_parsed_id_token(
        oauth_payload,
        plugin.config.json_web_key_set_url,
    )
    user = get_or_create_user_from_payload(
        claims,
        oauth_url="https://saleor.io/oauth",
    )
    expected_tokens = create_tokens_from_oauth_payload(
        oauth_payload, user, claims, permissions=[], owner=plugin.PLUGIN_ID
    )

    decoded_access_token = jwt_decode(tokens.token)
    assert decoded_access_token["permissions"] == []
    assert decoded_access_token["is_staff"] is False
    assert tokens.token == expected_tokens["token"]
    decoded_refresh_token = jwt_decode(tokens.refresh_token)
    assert tokens.csrf_token == decoded_refresh_token["csrf_token"]
    assert decoded_refresh_token["oauth_refresh_token"] == "refresh"


@freeze_time("2019-03-18 12:00:00")
def test_external_obtain_access_tokens_with_permissions(
    openid_plugin, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__
    mocked_jwt_validator.get.side_effect = id_payload.get

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        Mock(return_value=mocked_jwt_validator),
    )
    plugin = openid_plugin(use_oauth_scope_permissions=True)
    oauth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "id_token": id_token,
        "scope": "openid profile email offline_access saleor:manage_orders",
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    mocked_fetch_token = Mock(return_value=oauth_payload)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.client.OAuth2Client.fetch_token",
        mocked_fetch_token,
    )
    redirect_uri = "http://localhost:3000/used-logged-in"
    state = signing.dumps({"redirectUri": redirect_uri})
    code = "oauth-code"
    tokens = plugin.external_obtain_access_tokens(
        {"state": state, "code": code}, rf.request(), previous_value=None
    )

    mocked_fetch_token.assert_called_once_with(
        "https://saleor.io/oauth/token",
        code=code,
        redirect_uri=redirect_uri,
    )

    claims = get_parsed_id_token(
        oauth_payload,
        plugin.config.json_web_key_set_url,
    )
    user = get_or_create_user_from_payload(claims, "https://saleor.io/oauth")
    user.is_staff = True
    expected_tokens = create_tokens_from_oauth_payload(
        oauth_payload,
        user,
        claims,
        permissions=[
            "MANAGE_ORDERS",
        ],
        owner=plugin.PLUGIN_ID,
    )

    decoded_access_token = jwt_decode(tokens.token)
    assert decoded_access_token["permissions"] == [
        "MANAGE_ORDERS",
    ]
    assert decoded_access_token["is_staff"] is True

    assert tokens.token == expected_tokens["token"]
    decoded_refresh_token = jwt_decode(tokens.refresh_token)
    assert tokens.csrf_token == decoded_refresh_token["csrf_token"]
    assert decoded_refresh_token["oauth_refresh_token"] == "refresh"


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_obtain_access_tokens_with_saleor_staff(
    openid_plugin, monkeypatch, rf, id_token, id_payload
):
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__
    mocked_jwt_validator.get.side_effect = id_payload.get

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        Mock(return_value=mocked_jwt_validator),
    )
    plugin = openid_plugin(use_oauth_scope_permissions=True)
    oauth_payload = {
        "access_token": "FeHkE_QbuU3cYy1a1eQUrCE5jRcUnBK3",
        "refresh_token": "refresh",
        "id_token": id_token,
        "scope": "openid profile email offline_access saleor:staff",
        "expires_in": 86400,
        "token_type": "Bearer",
        "expires_at": 1600851112,
    }
    mocked_fetch_token = Mock(return_value=oauth_payload)
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.client.OAuth2Client.fetch_token",
        mocked_fetch_token,
    )
    redirect_uri = "http://localhost:3000/used-logged-in"
    state = signing.dumps({"redirectUri": redirect_uri})
    code = "oauth-code"
    tokens = plugin.external_obtain_access_tokens(
        {"state": state, "code": code}, rf.request(), previous_value=None
    )

    mocked_fetch_token.assert_called_once_with(
        "https://saleor.io/oauth/token",
        code=code,
        redirect_uri=redirect_uri,
    )

    claims = get_parsed_id_token(
        oauth_payload,
        plugin.config.json_web_key_set_url,
    )
    user = get_or_create_user_from_payload(
        claims,
        "https://saleor.io/oauth",
    )
    user.refresh_from_db()

    assert user.is_staff is True

    expected_tokens = create_tokens_from_oauth_payload(
        oauth_payload, user, claims, permissions=[], owner=plugin.PLUGIN_ID
    )

    decoded_access_token = jwt_decode(tokens.token)
    assert decoded_access_token["permissions"] == []
    assert decoded_access_token["is_staff"] is True

    assert tokens.token == expected_tokens["token"]
    decoded_refresh_token = jwt_decode(tokens.refresh_token)
    assert tokens.csrf_token == decoded_refresh_token["csrf_token"]
    assert decoded_refresh_token["oauth_refresh_token"] == "refresh"


@freeze_time("2019-03-18 12:00:00")
@pytest.mark.vcr
def test_external_obtain_access_tokens_user_which_is_no_more_staff(
    openid_plugin, monkeypatch, rf, id_token, id_payload, staff_user
):
    staff_user.is_staff = False
    staff_user.email = "admin@example.com"
    staff_user.save()

    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__
    mocked_jwt_validator.get.side_effect = id_payload.get

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        Mock(return_value=mocked_jwt_validator),
    )
    plugin = openid_plugin(use_oauth_scope_permissions=True)
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
        "saleor.plugins.openid_connect.client.OAuth2Client.fetch_token",
        mocked_fetch_token,
    )
    redirect_uri = "http://localhost:3000/used-logged-in"
    state = signing.dumps({"redirectUri": redirect_uri})
    code = "oauth-code"
    tokens = plugin.external_obtain_access_tokens(
        {"state": state, "code": code}, rf.request(), previous_value=None
    )

    mocked_fetch_token.assert_called_once_with(
        "https://saleor.io/oauth/token",
        code=code,
        redirect_uri=redirect_uri,
    )

    claims = get_parsed_id_token(
        oauth_payload,
        plugin.config.json_web_key_set_url,
    )
    user = get_or_create_user_from_payload(claims, "https://saleor.io/oauth")

    staff_user.refresh_from_db()
    assert staff_user == user
    assert user.is_staff is False

    decoded_access_token = jwt_decode(tokens.token)
    assert decoded_access_token["permissions"] == []
    assert decoded_access_token["is_staff"] is False


@freeze_time("2019-03-18 12:00:00")
def test_external_obtain_access_tokens_plugin_disabled(openid_plugin, rf):
    plugin = openid_plugin(active=False)
    redirect_uri = "http://localhost:3000/used-logged-in"
    state = signing.dumps({"redirectUri": redirect_uri})
    code = "oauth-code"
    previous_value = ExternalAccessTokens(token="previous")
    tokens = plugin.external_obtain_access_tokens(
        {"state": state, "code": code}, rf.request(), previous_value=previous_value
    )
    assert tokens == previous_value


@freeze_time("2019-03-18 12:00:00")
def test_external_obtain_access_tokens_missing_code(openid_plugin, rf):
    plugin = openid_plugin()
    redirect_uri = "http://localhost:3000/used-logged-in"
    state = signing.dumps({"redirectUri": redirect_uri})
    with pytest.raises(ValidationError):
        plugin.external_obtain_access_tokens(
            {"state": state}, rf.request(), previous_value=None
        )


@freeze_time("2019-03-18 12:00:00")
def test_external_obtain_access_tokens_missing_state(openid_plugin, rf):
    plugin = openid_plugin()
    code = "oauth-code"
    with pytest.raises(ValidationError):
        plugin.external_obtain_access_tokens(
            {"code": code}, rf.request(), previous_value=None
        )


@freeze_time("2019-03-18 12:00:00")
def test_external_obtain_access_tokens_missing_redirect_uri_in_state(openid_plugin, rf):
    plugin = openid_plugin()
    state = signing.dumps({})
    code = "oauth-code"
    with pytest.raises(ValidationError):
        plugin.external_obtain_access_tokens(
            {"state": state, "code": code}, rf.request(), previous_value=None
        )


def test_external_obtain_access_tokens_fetch_token_raises_error(
    openid_plugin, monkeypatch, rf, id_token, id_payload
):
    # given
    mocked_jwt_validator = MagicMock()
    mocked_jwt_validator.__getitem__.side_effect = id_payload.__getitem__
    mocked_jwt_validator.get.side_effect = id_payload.get

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_decoded_token",
        Mock(return_value=mocked_jwt_validator),
    )
    plugin = openid_plugin(use_oauth_scope_permissions=True)

    monkeypatch.setattr(
        "saleor.plugins.openid_connect.client.OAuth2Client.fetch_token",
        Mock(side_effect=OAuthError()),
    )

    redirect_uri = "http://localhost:3000/used-logged-in"
    state = signing.dumps({"redirectUri": redirect_uri})
    code = "oauth-code"

    # when & then
    with pytest.raises(ValidationError):
        plugin.external_obtain_access_tokens(
            {"state": state, "code": code}, rf.request(), previous_value=None
        )


test_url = "http://saleor.io/"


@pytest.mark.parametrize(
    "c_id,c_secret,authorization_url,token_url,jwks_url,user_info_url",
    (
        ["", "ss", f"{test_url}auth", f"{test_url}token", f"{test_url}jwks", ""],
        ["cc", "", f"{test_url}auth", f"{test_url}token", f"{test_url}jwks", ""],
        ["cc", "123", "", f"{test_url}token", f"{test_url}jwks", ""],
        ["cc", "123", f"{test_url}auth", "", f"{test_url}jwks", ""],
        ["cc", "123", f"{test_url}auth", f"{test_url}token", "", ""],
        [
            "cc",
            "123",
            "saleor.io/auth",
            f"{test_url}token",
            f"{test_url}token",
            "",
        ],
        ["cc", "123", f"{test_url}auth", "http://", f"{test_url}token", ""],
        ["cc", "123", f"{test_url}auth", "http://", f"{test_url}token", ""],
        ["cc", "123", "not_url", f"{test_url}token", f"{test_url}token", ""],
        ["cc", "123", "", "", "", "not_url"],
        ["cc", "123", "", "", "", f"{test_url}/userinfo"],
        ["cc", "123", "", "", "", ""],
    ),
)
def test_validate_plugin_configuration_raises_error(
    c_id,
    c_secret,
    authorization_url,
    token_url,
    jwks_url,
    user_info_url,
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
        user_info_url=user_info_url,
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
        oauth_authorization_url="http://saleor.io/auth",
        oauth_token_url="http://saleor.io/token",
        json_web_key_set_url="http://saleor.io/jwks",
    )
    conf = PluginConfiguration(active=True, configuration=configuration)
    plugin = openid_plugin()
    plugin.validate_plugin_configuration(conf)


def test_external_logout_missing_logout_url(openid_plugin, rf):
    plugin = openid_plugin(oauth_logout_url="")
    response = plugin.external_logout({}, rf.request(), None)
    assert response == {}


def test_external_logout_plugin_inactive(openid_plugin, rf):
    plugin = openid_plugin(oauth_logout_url="", active=False)
    response = plugin.external_logout({}, rf.request(), None)
    assert response is None


def test_external_logout(openid_plugin, rf):
    client_id = "AVC"
    domain = "saleor.io"
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


def test_external_verify_plugin_disabled(openid_plugin, rf):
    plugin = openid_plugin(active=False)
    input = {"token": "token"}
    previous_value = "previous"
    response = plugin.external_verify(input, rf.request(), previous_value)
    assert response == previous_value


def test_external_verify_missing_token(openid_plugin, rf):
    plugin = openid_plugin(active=True)
    input = {}
    previous_value = "previous"
    response = plugin.external_verify(input, rf.request(), previous_value)
    assert response == previous_value


def test_external_verify_wrong_token_owner(openid_plugin, rf):
    plugin = openid_plugin(active=True)
    input = {"token": "wrong_format"}
    previous_value = "previous"
    response = plugin.external_verify(input, rf.request(), previous_value)
    assert response == previous_value


@freeze_time("2019-03-18 12:00:00")
def test_external_verify(id_payload, customer_user, openid_plugin, rf):
    plugin = openid_plugin()
    token = create_jwt_token(
        id_payload,
        customer_user,
        access_token="access",
        permissions=[],
        owner=plugin.PLUGIN_ID,
    )
    input = {"token": token}
    previous_value = "previous"
    response = plugin.external_verify(input, rf.request(), previous_value)
    user, data = response
    assert user == customer_user
    assert list(user.effective_permissions) == []
    assert user.is_staff is False
    assert Group.objects.count() == 0
    assert user.groups.count() == 0


@freeze_time("2019-03-18 12:00:00")
def test_external_verify_user_with_effective_permissions(
    permission_manage_orders, id_payload, customer_user, openid_plugin, rf
):
    plugin = openid_plugin()
    token = create_jwt_token(
        id_payload,
        customer_user,
        access_token="access",
        permissions=["MANAGE_ORDERS"],
        owner=plugin.PLUGIN_ID,
    )
    input = {"token": token}
    previous_value = "previous"
    response = plugin.external_verify(input, rf.request(), previous_value)
    user, data = response
    assert user == customer_user
    assert list(user.effective_permissions) == [permission_manage_orders]
    assert user.is_staff is True
    assert Group.objects.count() == 1
    group = Group.objects.get()
    assert group.name == plugin.config.default_group_name
    assert user.groups.count() == 1
    assert user.groups.first() == group


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


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_user_with_access_token(
    openid_plugin,
    decoded_access_token,
    user_info_response,
    customer_user,
    monkeypatch,
    rf,
):
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
        staff_user_domains="",
    )
    decoded_access_token["scope"] = ""

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )

    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token", lambda x, y: None
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    user = plugin.authenticate_user(rf.request(), None)

    assert user == customer_user
    assert user.is_staff is False
    assert list(user.effective_permissions) == []


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_user_with_access_token_unable_to_fetch_user_info(
    openid_plugin, decoded_access_token, monkeypatch, rf
):
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
    )
    decoded_access_token["scope"] = ""

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )

    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token", lambda x, y: None
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info", lambda x, z: None
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    user = plugin.authenticate_user(rf.request(), None)

    assert user is None


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_user_with_jwt_access_token(
    openid_plugin,
    decoded_access_token,
    user_info_response,
    customer_user,
    monkeypatch,
    rf,
):
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
    )
    decoded_access_token["scope"] = ""
    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    user = plugin.authenticate_user(rf.request(), None)

    assert user == customer_user
    assert user.is_staff is False
    assert list(user.effective_permissions) == []


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_user_with_jwt_access_token_which_is_no_more_staff(
    openid_plugin,
    decoded_access_token,
    user_info_response,
    customer_user,
    monkeypatch,
    rf,
):
    customer_user.is_staff = True
    customer_user.email = "test@example.com"
    customer_user.save()

    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
    )
    decoded_access_token["scope"] = ""
    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    user = plugin.authenticate_user(rf.request(), None)

    user.refresh_from_db()
    assert user == customer_user
    assert user.is_staff is False
    assert list(user.effective_permissions) == []


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_staff_user_with_jwt_access_token_and_staff_scope(
    openid_plugin,
    decoded_access_token,
    user_info_response,
    customer_user,
    monkeypatch,
    rf,
):
    # given
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
    )
    decoded_access_token["scope"] = "openid profile email saleor:staff"
    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get
    assert Group.objects.count() == 0

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    # when
    user = plugin.authenticate_user(rf.request(), None)

    # then
    user.refresh_from_db()
    assert user == customer_user
    assert user.is_staff is True
    assert list(user.effective_permissions) == []
    assert Group.objects.count() == 1
    group = Group.objects.get()
    assert group.name == plugin.config.default_group_name
    assert user.groups.count() == 1
    assert user.groups.first() == group


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_staff_user_with_jwt_access_token_and_staff_in_permissions_field(
    openid_plugin,
    decoded_access_token,
    user_info_response,
    customer_user,
    monkeypatch,
    rf,
):
    # given
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
    )
    decoded_access_token["scope"] = "openid profile email"
    decoded_access_token["permissions"] = ["saleor:staff"]
    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get
    assert Group.objects.count() == 0

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    # when
    user = plugin.authenticate_user(rf.request(), None)

    # then
    user.refresh_from_db()
    assert user == customer_user
    assert user.is_staff is True
    assert list(user.effective_permissions) == []
    assert Group.objects.count() == 1
    group = Group.objects.get()
    assert group.name == plugin.config.default_group_name
    assert user.groups.count() == 1
    assert user.groups.first() == group


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_staff_user_with_jwt_access_token_with_permissions_field(
    permission_manage_orders,
    permission_manage_apps,
    openid_plugin,
    decoded_access_token,
    user_info_response,
    customer_user,
    monkeypatch,
    rf,
):
    # given
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
    )
    decoded_access_token["scope"] = "openid profile email"
    decoded_access_token["permissions"] = ["saleor:manage_orders", "saleor:manage_apps"]
    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    # when
    user = plugin.authenticate_user(rf.request(), None)

    # then
    user.refresh_from_db()
    assert user == customer_user
    assert user.is_staff is True
    assert set(user.effective_permissions) == {
        permission_manage_apps,
        permission_manage_orders,
    }
    assert Group.objects.count() == 1
    group = Group.objects.get()
    assert group.name == plugin.config.default_group_name
    assert user.groups.count() == 1
    assert user.groups.first() == group


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_user_with_jwt_access_token_unable_to_fetch_user_info(
    openid_plugin, decoded_access_token, monkeypatch, rf
):
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
    )
    decoded_access_token["scope"] = ""

    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info", Mock(return_value=None)
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    user = plugin.authenticate_user(rf.request(), None)

    assert user is None


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_user_with_jwt_invalid_access_token(
    openid_plugin,
    decoded_access_token,
    user_info_response,
    monkeypatch,
    rf,
):
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
    )
    decoded_access_token["scope"] = ""

    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get
    decoded_token.validate.side_effect = JoseError()

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )

    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    user = plugin.authenticate_user(rf.request(), None)

    assert user is None


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_staff_user_with_jwt_access_token(
    openid_plugin,
    decoded_access_token,
    user_info_response,
    staff_user,
    monkeypatch,
    rf,
    permission_manage_orders,
    permission_manage_apps,
    permission_manage_products,
):
    # given
    staff_user.is_staff = False
    staff_user.save()

    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
        audience=decoded_access_token["aud"][0],
    )

    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get
    assert Group.objects.count() == 0

    user_info_response["email"] = staff_user.email

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    # when
    user = plugin.authenticate_user(rf.request(), None)

    # then
    user.refresh_from_db()
    assert user == staff_user
    assert user.is_staff is True
    assert set(user.effective_permissions) == {
        permission_manage_orders,
        permission_manage_apps,
        permission_manage_products,
    }
    assert Group.objects.count() == 1
    group = Group.objects.get()
    assert group.name == plugin.config.default_group_name
    assert user.groups.count() == 1
    assert user.groups.first() == group


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_staff_user_with_jwt_access_token_and_disabled_scope_permission(
    openid_plugin, decoded_access_token, user_info_response, staff_user, monkeypatch, rf
):
    # given
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=False,
    )

    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get
    assert Group.objects.count() == 0

    user_info_response["email"] = staff_user.email

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )

    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )

    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )

    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    # when
    user = plugin.authenticate_user(rf.request(), None)

    # then
    assert user == staff_user
    assert user.is_staff is False
    assert list(user.effective_permissions) == []
    assert Group.objects.count() == 0
    assert user.groups.count() == 0


@freeze_time("2021-03-08 12:00:00")
def test_authenticate_user_with_jwt_access_token_user_email_in_staff_domains_group(
    openid_plugin,
    decoded_access_token,
    user_info_response,
    customer_user,
    monkeypatch,
    rf,
    permission_manage_users,
):
    # given
    plugin = openid_plugin(
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        user_info_url="https://saleor.io/userinfo",
        use_oauth_scope_permissions=True,
        staff_user_domains=user_info_response["email"].split("@")[1],
    )
    decoded_access_token["scope"] = ""
    decoded_token = MagicMock()
    decoded_token.__getitem__.side_effect = decoded_access_token.__getitem__
    decoded_token.get.side_effect = decoded_access_token.get

    group = Group.objects.create(name=plugin.config.default_group_name)
    group.permissions.add(permission_manage_users)
    group_count = Group.objects.count()

    # mock get token from request
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request",
        lambda _: "OAuth_access_token",
    )
    # decode access token returns payload when access token is in JWT format
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.decode_access_token",
        lambda x, y: decoded_token,
    )
    # mock request to api to fetch user info details
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.utils.get_user_info",
        lambda x, z: user_info_response,
    )
    # mock cache used for caching user info details
    monkeypatch.setattr("saleor.plugins.openid_connect.utils.cache.set", Mock())

    # when
    user = plugin.authenticate_user(rf.request(), None)

    # then
    assert user == customer_user
    assert user.is_staff is True
    assert Group.objects.count() == group_count
    assert group in user.groups.all()
    assert {perm.name for perm in user.effective_permissions} == set(
        group.permissions.values_list("name", flat=True)
    )


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user_wrong_owner(
    openid_plugin, id_payload, customer_user, staff_user, monkeypatch, rf
):
    plugin = openid_plugin(user_info_url="")
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
    plugin = openid_plugin(user_info_url="")
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
def test_authenticate_user_plugin_is_disabled(
    openid_plugin, customer_user, monkeypatch, id_payload, rf
):
    plugin = openid_plugin(active=False)
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
    assert user is None


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user_unable_to_decode_token(openid_plugin, monkeypatch, rf):
    plugin = openid_plugin(user_info_url="")
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
    # given
    plugin = openid_plugin()
    assert Group.objects.count() == 0
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

    # when
    user = plugin.authenticate_user(rf.request(), None)

    # then
    assert user == staff_user
    assert set(user.effective_permissions) == {
        permission_manage_orders,
        permission_manage_users,
    }
    assert Group.objects.count() == 1
    group = Group.objects.get()
    assert group.name == plugin.config.default_group_name
    assert user.groups.count() == 1
    assert user.groups.first() == group


@freeze_time("2019-03-18 12:00:00")
def test_authenticate_user_staff_user_without_permissions(
    openid_plugin,
    id_payload,
    staff_user,
    monkeypatch,
    rf,
):
    # given
    plugin = openid_plugin()
    token = create_jwt_token(
        id_payload,
        staff_user,
        access_token="access",
        permissions=[],
        owner=plugin.PLUGIN_ID,
    )
    monkeypatch.setattr(
        "saleor.plugins.openid_connect.plugin.get_token_from_request", lambda _: token
    )

    # when
    user = plugin.authenticate_user(rf.request(), None)

    # then
    assert user == staff_user
    assert user.groups.count() == 1
