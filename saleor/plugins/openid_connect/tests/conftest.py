import jwt
import pytest

from ...manager import get_plugins_manager
from ..plugin import OpenIDConnectPlugin


@pytest.fixture()
def plugin_configuration():
    def fun(
        client_id=None,
        client_secret=None,
        enable_refresh_token=True,
        oauth_authorization_url=None,
        oauth_token_url=None,
        json_web_key_set_url=None,
        oauth_logout_url=None,
        user_info_url=None,
        use_oauth_scope_permissions=False,
        audience=None,
    ):
        return [
            {"name": "client_id", "value": client_id},
            {"name": "client_secret", "value": client_secret},
            {"name": "enable_refresh_token", "value": enable_refresh_token},
            {"name": "oauth_authorization_url", "value": oauth_authorization_url},
            {"name": "oauth_token_url", "value": oauth_token_url},
            {"name": "json_web_key_set_url", "value": json_web_key_set_url},
            {"name": "oauth_logout_url", "value": oauth_logout_url},
            {"name": "user_info_url", "value": user_info_url},
            {
                "name": "use_oauth_scope_permissions",
                "value": use_oauth_scope_permissions,
            },
            {"name": "audience", "value": audience},
        ]

    return fun


@pytest.fixture
def openid_plugin(settings, plugin_configuration):
    def fun(
        active=True,
        client_id="client_id",
        client_secret="client_secret",
        enable_refresh_token=True,
        oauth_authorization_url="https://saleor.io/oauth/authorize",
        oauth_token_url="https://saleor.io/oauth/token",
        json_web_key_set_url="https://saleor.io/.well-known/jwks.json",
        oauth_logout_url="",
        use_oauth_scope_permissions=False,
        user_info_url="https://saleor.io/userinfo",
        audience="perms",
    ):
        settings.PLUGINS = ["saleor.plugins.openid_connect.plugin.OpenIDConnectPlugin"]
        manager = get_plugins_manager()
        manager.save_plugin_configuration(
            OpenIDConnectPlugin.PLUGIN_ID,
            None,
            {
                "active": active,
                "configuration": plugin_configuration(
                    client_id=client_id,
                    client_secret=client_secret,
                    enable_refresh_token=enable_refresh_token,
                    oauth_authorization_url=oauth_authorization_url,
                    oauth_token_url=oauth_token_url,
                    json_web_key_set_url=json_web_key_set_url,
                    oauth_logout_url=oauth_logout_url,
                    use_oauth_scope_permissions=use_oauth_scope_permissions,
                    user_info_url=user_info_url,
                    audience=audience,
                ),
            },
        )
        manager = get_plugins_manager()
        return manager.all_plugins[0]

    return fun


@pytest.fixture
def decoded_access_token():
    return {
        "iss": "https://saleor-test.eu.auth0.com/",
        "sub": "google-oauth2|114622651317794521039",
        "aud": ["perms", "https://saleor.io/userinfo"],
        "iat": 1615374231,
        "exp": 1615460631,
        "azp": "mnrVS8QkVOjtvC2zeapSkLLkwowr37Lt",
        "scope": (
            "openid profile email saleor:manage_apps saleor:manage_orders "
            "saleor:manage_products saleor:staff"
        ),
    }


@pytest.fixture
def user_info_response():
    return {
        "sub": "google-oauth2|114622651317794521011",
        "given_name": "John",
        "family_name": "Doe",
        "nickname": "doe",
        "name": "John Doe",
        "picture": "https://lh3.googleusercontent.com/a-/123",
        "locale": "pl",
        "updated_at": "2021-03-08T12:40:53.894Z",
        "email": "test@example.com",
        "email_verified": True,
    }


@pytest.fixture()
def id_payload():
    return {
        "given_name": "Saleor",
        "family_name": "Admin",
        "nickname": "saloer",
        "name": "Saleor Admin",
        "picture": "",
        "locale": "pl",
        "updated_at": "2020-09-22T08:50:50.110Z",
        "email": "admin@example.com",
        "email_verified": True,
        "iss": "https://saleor.io/",
        "sub": "google-oauth2|",
        "aud": "",
        "iat": 1600764712,
        "exp": 1600800712,
    }


@pytest.fixture()
def id_token(id_payload):
    private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAnzyis1ZjfNB0bBgKFMSvvkTtwlvBsaJq7S5wA+kzeVOVpVWw
kWdVha4s38XM/pa/yr47av7+z3VTmvDRyAHcaT92whREFpLv9cj5lTeJSibyr/Mr
m/YtjCZVWgaOYIhwrXwKLqPr/11inWsAkfIytvHWTxZYEcXLgAXFuUuaS3uF9gEi
NQwzGTU1v0FqkqTBr4B8nW3HCN47XUu0t8Y0e+lf4s4OxQawWD79J9/5d3Ry0vbV
3Am1FtGJiJvOwRsIfVChDpYStTcHTCMqtvWbV6L11BWkpzGXSW4Hv43qa+GSYOD2
QU68Mb59oSk2OB+BtOLpJofmbGEGgvmwyCI9MwIDAQABAoIBACiARq2wkltjtcjs
kFvZ7w1JAORHbEufEO1Eu27zOIlqbgyAcAl7q+/1bip4Z/x1IVES84/yTaM8p0go
amMhvgry/mS8vNi1BN2SAZEnb/7xSxbflb70bX9RHLJqKnp5GZe2jexw+wyXlwaM
+bclUCrh9e1ltH7IvUrRrQnFJfh+is1fRon9Co9Li0GwoN0x0byrrngU8Ak3Y6D9
D8GjQA4Elm94ST3izJv8iCOLSDBmzsPsXfcCUZfmTfZ5DbUDMbMxRnSo3nQeoKGC
0Lj9FkWcfmLcpGlSXTO+Ww1L7EGq+PT3NtRae1FZPwjddQ1/4V905kyQFLamAA5Y
lSpE2wkCgYEAy1OPLQcZt4NQnQzPz2SBJqQN2P5u3vXl+zNVKP8w4eBv0vWuJJF+
hkGNnSxXQrTkvDOIUddSKOzHHgSg4nY6K02ecyT0PPm/UZvtRpWrnBjcEVtHEJNp
bU9pLD5iZ0J9sbzPU/LxPmuAP2Bs8JmTn6aFRspFrP7W0s1Nmk2jsm0CgYEAyH0X
+jpoqxj4efZfkUrg5GbSEhf+dZglf0tTOA5bVg8IYwtmNk/pniLG/zI7c+GlTc9B
BwfMr59EzBq/eFMI7+LgXaVUsM/sS4Ry+yeK6SJx/otIMWtDfqxsLD8CPMCRvecC
2Pip4uSgrl0MOebl9XKp57GoaUWRWRHqwV4Y6h8CgYAZhI4mh4qZtnhKjY4TKDjx
QYufXSdLAi9v3FxmvchDwOgn4L+PRVdMwDNms2bsL0m5uPn104EzM6w1vzz1zwKz
5pTpPI0OjgWN13Tq8+PKvm/4Ga2MjgOgPWQkslulO/oMcXbPwWC3hcRdr9tcQtn9
Imf9n2spL/6EDFId+Hp/7QKBgAqlWdiXsWckdE1Fn91/NGHsc8syKvjjk1onDcw0
NvVi5vcba9oGdElJX3e9mxqUKMrw7msJJv1MX8LWyMQC5L6YNYHDfbPF1q5L4i8j
8mRex97UVokJQRRA452V2vCO6S5ETgpnad36de3MUxHgCOX3qL382Qx9/THVmbma
3YfRAoGAUxL/Eu5yvMK8SAt/dJK6FedngcM3JEFNplmtLYVLWhkIlNRGDwkg3I5K
y18Ae9n7dHVueyslrb6weq7dTkYDi3iOYRW8HRkIQh06wEdbxt0shTzAJvvCQfrB
jg/3747WSsf/zBTcHihTRBdAv6OmdhV4/dD5YBfLAkLrd+mX7iE=
-----END RSA PRIVATE KEY-----"""
    return jwt.encode(
        id_payload,
        private_key,
        "RS256",  # type: ignore
    )
