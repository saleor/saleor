import unittest2

from .oauth import OAuth1Test, OAuth2Test
from .open_id_connect import OpenIdConnectTestMixin


class ElixirOpenIdConnectTest(OpenIdConnectTestMixin, OAuth2Test):
    backend_path = 'social_core.backends.elixir.ElixirOpenIdConnect'
    issuer = 'https://login.elixir-czech.org/oidc/'
    openid_config_body = """
    {
        "claims_supported": [
            "sub",
            "name",
            "preferred_username",
            "given_name",
            "family_name",
            "middle_name",
            "nickname",
            "profile",
            "picture",
            "website",
            "gender",
            "zoneinfo",
            "locale",
            "updated_at",
            "birthdate",
            "email",
            "email_verified",
            "phone_number",
            "phone_number_verified",
            "address"
        ],
        "op_policy_uri": "https://login.elixir-czech.org/oidc/about",
        "subject_types_supported": [
            "public",
            "pairwise"
        ],
        "request_parameter_supported": true,
        "userinfo_signing_alg_values_supported": [
            "HS256",
            "HS384",
            "HS512",
            "RS256",
            "RS384",
            "RS512",
            "ES256",
            "ES384",
            "ES512",
            "PS256",
            "PS384",
            "PS512"
        ],
        "revocation_endpoint": "https://login.elixir-czech.org/oidc/revoke",
        "issuer": "https://login.elixir-czech.org/oidc/",
        "id_token_encryption_enc_values_supported": [
            "A256CBC+HS512",
            "A256GCM",
            "A192GCM",
            "A128GCM",
            "A128CBC-HS256",
            "A192CBC-HS384",
            "A256CBC-HS512",
            "A128CBC+HS256"
        ],
        "require_request_uri_registration": false,
        "grant_types_supported": [
            "authorization_code",
            "implicit",
            "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "client_credentials",
            "urn:ietf:params:oauth:grant_type:redelegate",
            "urn:ietf:params:oauth:grant-type:device_code"
        ],
        "token_endpoint": "https://login.elixir-czech.org/oidc/token",
        "request_uri_parameter_supported": false,
        "service_documentation": "https://login.elixir-czech.org/oidc/about",
        "registration_endpoint": "https://login.elixir-czech.org/oidc/register",
        "jwks_uri": "https://login.elixir-czech.org/oidc/jwk",
        "userinfo_encryption_alg_values_supported": [
            "RSA-OAEP",
            "RSA-OAEP-256",
            "RSA1_5"
        ],
        "scopes_supported": [],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
            "client_secret_jwt",
            "private_key_jwt",
            "none"
        ],
        "userinfo_encryption_enc_values_supported": [
            "A256CBC+HS512",
            "A256GCM",
            "A192GCM",
            "A128GCM",
            "A128CBC-HS256",
            "A192CBC-HS384",
            "A256CBC-HS512",
            "A128CBC+HS256"
        ],
        "claim_types_supported": [
            "normal"
        ],
        "request_object_encryption_enc_values_supported": [
            "A256CBC+HS512",
            "A256GCM",
            "A192GCM",
            "A128GCM",
            "A128CBC-HS256",
            "A192CBC-HS384",
            "A256CBC-HS512",
            "A128CBC+HS256"
        ],
        "claims_parameter_supported": false,
        "id_token_encryption_alg_values_supported": [
            "RSA-OAEP",
            "RSA-OAEP-256",
            "RSA1_5"
        ],
        "code_challenge_methods_supported": [
            "plain",
            "S256"
        ],
        "token_endpoint_auth_signing_alg_values_supported": [
            "HS256",
            "HS384",
            "HS512",
            "RS256",
            "RS384",
            "RS512",
            "ES256",
            "ES384",
            "ES512",
            "PS256",
            "PS384",
            "PS512"
        ],
        "userinfo_endpoint": "https://login.elixir-czech.org/oidc/userinfo",
        "introspection_endpoint": "https://login.elixir-czech.org/oidc/introspect",
        "id_token_signing_alg_values_supported": [
            "HS256",
            "HS384",
            "HS512",
            "RS256",
            "RS384",
            "RS512",
            "ES256",
            "ES384",
            "ES512",
            "PS256",
            "PS384",
            "PS512",
            "none"
        ],
        "device_authorization_endpoint": "https://login.elixir-czech.org/oidc/devicecode",
        "op_tos_uri": "https://login.elixir-czech.org/oidc/about",
        "request_object_encryption_alg_values_supported": [
            "RSA-OAEP",
            "RSA-OAEP-256",
            "RSA1_5"
        ],
        "request_object_signing_alg_values_supported": [
            "HS256",
            "HS384",
            "HS512",
            "RS256",
            "RS384",
            "RS512",
            "ES256",
            "ES384",
            "ES512",
            "PS256",
            "PS384",
            "PS512"
        ],
        "response_types_supported": [
            "code",
            "token"
        ],
        "end_session_endpoint": "https://login.elixir-czech.org/oidc/endsession",
        "authorization_endpoint": "https://login.elixir-czech.org/oidc/authorize"
    }
    """
