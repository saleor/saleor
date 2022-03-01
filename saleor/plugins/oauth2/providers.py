import json
from datetime import datetime, timedelta

import jwt
import requests
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.requests_client import OAuth2Session
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .graphql.enums import OAuth2ErrorCode

User = get_user_model()


class Provider:
    name = None
    urls = {}
    scope = []

    def __init__(self, client_id, scope=None, **kwargs):
        self.client_id = client_id
        self.kwargs = kwargs

        if scope:
            self.scope = scope

    @property
    def client_secret(self):
        return self.kwargs["client_secret"]

    def get_url_for(self, _for):
        """URL validators are functions that return the validated URLs of the service.

        They follow the naming convention of: validate_{_for}_url

        e.g:

            validate_auth_url,
            validate_profileinfo_url,

        """
        validator = getattr(self, f"validate_{_for}_url", None)

        if validator:
            return validator(_for)

        url = self.urls.get(_for)

        if url is None:
            raise TypeError(f"Missing URL in {self.__class__.__name__} urls map")

        return url

    def get_scope(self):
        return " ".join(self.scope)

    def validate(self):
        if not isinstance(self.client_id, str):
            raise TypeError(
                "client_id cannot be of type {t}".format(
                    t=type(self.client_secret).__name__
                )
            )

        client_secret = self.client_secret
        if not isinstance(client_secret, str):
            raise TypeError(
                "client_secret cannot be of type {t}".format(
                    t=type(client_secret).__name__
                )
            )

    def get_session(self, **kwargs):
        scope = kwargs.get("scope", self.get_scope())
        try:
            return OAuth2Session(
                client_id=self.client_id,
                scope=scope,
                **kwargs,
            )
        except OAuthError as e:
            raise ValidationError(str(e), code=OAuth2ErrorCode.OAUTH2_ERROR)

    def get_authorization_url(self, redirect_uri):
        session = self.get_session(redirect_uri=redirect_uri)
        auth_endpoint = self.get_url_for("auth")

        url, state = session.create_authorization_url(auth_endpoint)

        return url, state

    def fetch_tokens(self, code, state, redirect_uri):
        session = self.get_session(redirect_uri=redirect_uri, state=state)
        token_uri = self.get_url_for("token")

        try:
            return session.fetch_token(
                token_uri,
                client_id=self.client_id,
                client_secret=self.client_secret,
                code=code,
                grant_type="authorization_code",
                redirect_uri=redirect_uri,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except OAuthError as e:
            raise ValidationError(
                str(e),
                code=OAuth2ErrorCode.OAUTH2_ERROR,
            )

    def fetch_profile(self, access_token):
        if access_token is None:
            raise TypeError("access_token must not be None")

        profile_url = self.get_url_for("userinfo")
        response = requests.get(
            profile_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code == 200:
            try:
                return response.json()  # TODO show a better error
            except json.JSONDecodeError:
                raise ValidationError(
                    "Invalid provider response", code=OAuth2ErrorCode.INVALID
                )

        raise ValidationError(
            message="An error occured while requesting {}: {}".format(
                self.name, str(response.text)
            ),
            code=OAuth2ErrorCode.USER_NOT_FOUND,
        )

    def decode_token(self, token):
        try:
            return jwt.decode(
                token, algorithms=["ES256"], options={"verify_signature": False}
            )
        except jwt.exceptions.DecodeError:
            raise ValidationError({"token": "Invalid token provided"})

    def get_email(self, access_token, **kwargs):
        profile = self.fetch_profile(access_token)

        email = profile.get("email")

        if email is None:
            raise ValidationError("Provider missing email")

        return email


class Facebook(Provider):
    name = "facebook"
    urls = {
        "auth": "https://www.facebook.com/v12.0/dialog/oauth",
        "token": "https://graph.facebook.com/v12.0/oauth/access_token",
        "userinfo": "https://graph.facebook.com/me",
    }
    scope = [
        "email",
        "public_profile",
        "openid",
    ]

    def validate_userinfo_url(self, _for):
        return self.urls["userinfo"] + "?fields=email"


class Google(Provider):
    name = "google"
    urls = {
        "auth": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
    }
    scope = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid",
    ]


class Apple(Provider):
    name = "apple"
    urls = {
        "auth": "https://appleid.apple.com/auth/authorize",
        "token": "https://appleid.apple.com/auth/token",
    }

    @property
    def client_secret(self):
        kwargs = self.kwargs
        kid = kwargs["key_id"]
        team_id = kwargs["team_id"]

        headers = {"kid": kid, "alg": "ES256", "typ": "JWT"}
        claims = {
            "iss": team_id,
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int(datetime.utcnow().timestamp())
            + timedelta(minutes=10).total_seconds(),
            "aud": "https://appleid.apple.com",
            "sub": self.client_id,
        }

        pv = self.kwargs["private_key"]
        return jwt.encode(claims, pv, algorithm="ES256", headers=headers)

    def get_email(self, access_token, **kwargs):
        """access_token is the ID token of apple.

        This introduces a vulneribility which should be solved
        if the ID token is crafted # FIXME

        """
        payload = self.decode_token(access_token)
        email = payload.get("email")

        if email is None:
            raise ValidationError(
                "Missing email in auth response, did you add email scope?"
            )

        return email

    def fetch_profile(self, access_token):
        email = self.get_email(access_token)

        return User.objects.get(email=email)

    def validate(self):
        kwargs = self.kwargs
        message = "{name} can't be of type {t}"

        kid = kwargs.get("key_id")

        if not kid:
            raise ValidationError(
                message.format(name="Apple Key ID", t=type(kid).__name__),
                code=OAuth2ErrorCode.OAUTH2_ERROR,
            )

        team_id = kwargs.get("team_id")
        if not kid:
            raise ValidationError(
                message.format(name="Apple Team ID", t=type(team_id).__name__),
                code=OAuth2ErrorCode.OAUTH2_ERROR,
            )

        return super().validate()
