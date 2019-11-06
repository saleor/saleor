import requests
import datetime

from requests.adapters import HTTPAdapter


class ClientTokenProvider:
    access_token = None
    access_token_expires_at = None

    def __init__(self, client_id, client_secret_key, sandbox_mode):
        if not sandbox_mode:
            self._client_auth = (client_id, client_secret_key)
        else:
            # demo sandbox POS
            self._client_auth = ("300746", "2ee86a66e5d97e3fadc400c9f19b065d")
        self._session = self.setup_session()
        self._token_url = "https://secure.payu.com/pl/standard/user/oauth/authorize"


    @staticmethod
    def setup_session():
        """Returns a `request.Session` with some basic retry configuration applied."""
        session = requests.Session()
        adapter = HTTPAdapter()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def client_token_expired(self, reduce_token_lifetime_seconds=15):
        """Check whether client token is still considered valid.
        :param reduce_token_lifetime_seconds: Use given amount of fewer lifetime seconds
               when comparing client token's expiration time with _now_.
               I.e. effectively reducing token lifetime for the check by some safety margin.
        :return: True when client token is considered expired
        """
        if self.access_token_expires_at:
            now = datetime.datetime.now()
            jitter = datetime.timedelta(seconds=reduce_token_lifetime_seconds)
            return self.access_token_expires_at < (now + jitter)
        else:
            return True  # just assuming it is expired

    def get_client_token(self):
        if self.access_token or not self.client_token_expired():
            return self.access_token
        return self._retrieve_client_token()

    def _retrieve_client_token(self):
        request_data = {"grant_type": "client_credentials"}
        response = self._session.post(
            self._token_url, request_data, auth=self._client_auth
        )
        response.raise_for_status()

        response_data = response.json()
        self.access_token = response_data["access_token"]
        self._set_access_token_expire_at(response_data["expires_in"])
        return response_data["access_token"]

    def _set_access_token_expire_at(self, expires_in):
        now = datetime.datetime.now()
        token_lifetime = datetime.timedelta(seconds=expires_in)
        self.access_token_expires_at = now + token_lifetime

    def refresh_client_token(self):
        self.access_token = None
        self.access_token_expires_at = None
        return self.get_client_token()


def get_auth_header(token):
    return f"Bearer {token}"


class PayuSession(requests.Session):
    """
    Wrapper over requests.Session it adds OpenID authorization and retries
    the call in case of 401 error.
    """
    def __init__(self, client_token_provider):
        self.client_token_provider = client_token_provider

    def request(self, method, url, **kwargs):
        client_token = self.client_token_provider.get_client_token()
        self.headers["Authorization"] = get_auth_header(client_token)
        response = super().request(method, url, **kwargs)
        if response.status_code == 401:
            token = self.client_token_provider.refresh_client_token()
            self.headers["Authorization"] = get_auth_header(token)
            response = super().request(method, url, **kwargs)
        return response
