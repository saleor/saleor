from authlib.integrations import requests_client

from ...core.http_client import HTTPConfig, HTTPSession


class OAuth2Client(HTTPSession, requests_client.OAuth2Session):
    """Override the 3rd party OAuth client with our custom HTTP client."""

    def __init__(self, **kwargs):
        kwargs.setdefault("config", HTTPConfig)
        super().__init__(**kwargs)
