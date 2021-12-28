import json

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

    def __init__(self, client_id, client_secret, redirect_uri, scope=None, **kwargs):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.kwargs = kwargs

        if scope:
            self.scope = scope

    def get_url_for(self, _for):
        return self.urls[_for]

    def get_scope(self):
        return " ".join(self.scope)

    def get_session(self, error_message="Invalid session", **kwargs):
        scope = kwargs.get("scope", self.get_scope())

        try:
            return OAuth2Session(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=scope,
                **kwargs,
            )
        except OAuthError:
            raise ValidationError(error_message, code=OAuth2ErrorCode.OAUTH2_ERROR)

    def get_authorization_url(self):
        session = self.get_session(
            f"Invalid {self.name} API authentication credentials provided"
        )
        auth_endpoint = self.get_url_for("auth")

        url, state = session.create_authorization_url(auth_endpoint)

        return url, state

    def fetch_tokens(self, info, code, state):
        session = self.get_session()
        token_uri = self.get_url_for("token")

        plugin = info.context.app
        config = plugin.get_oauth2_info(self.name)
        redirect_uri = config["redirect_uri"]

        try:
            return session.fetch_token(
                token_uri,
                code=code,
                state=state,
                grant_type="authorization_code",
                redirect_uri=redirect_uri,
            )
        except OAuthError:
            raise ValidationError(
                "Invalid authentication details",
                code=OAuth2ErrorCode.OAUTH2_ERROR,
            )

    def fetch_profile_info(self, auth_response):
        provider = auth_response["provider"]
        access_token = auth_response["access_token"]
        profile_url = self.get_url_for("userinfo")

        response = requests.get(
            profile_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code == 200:
            return response.json()

        raise ValidationError(
            message="An error occured while requesting {}: {}".format(
                provider, json.dumps(response)
            ),
            code=OAuth2ErrorCode.USER_NOT_FOUND,
        )

    def fetch_user_oauth2(self, auth_response):
        profile_info = self.fetch_profile_info(auth_response)
        email = profile_info["email"]

        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError(
                message="No user found with the specified email",
                code=OAuth2ErrorCode.USER_NOT_FOUND,
            )


class Facebook(Provider):
    name = "facebook"
    urls = {
        "auth": "https://www.facebook.com/v12.0/dialog/oauth",
        "token": "https://graph.facebook.com/v12.0/oauth/access_token",
        "userinfo": "https://graph.facebook.com/me",
    }
    # fields_map = {
    #     'first_name': '',
    #     'last_name': '',
    #     'email': 'email',
    #     'gender': '',
    #     'phone_number': '',
    # }


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
    # fields_map = {
    #     'first_name': '',
    #     'last_name': '',
    #     'email': 'email',
    #     'gender': '',
    #     'phone_number': '',
    # }


class Apple(Provider):
    name = "apple"
    urls = {
        "auth": "",
        "token": "https://appleid.apple.com/auth/token",
        "userinfo": "",
    }
    # fields_map = {
    #     'first_name': '',
    #     'last_name': '',
    #     'email': 'email',
    #     'gender': '',
    #     'phone_number': '',
    # }
