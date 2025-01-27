from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.auth import TokenAuth


def __del_OAuth2Session__(self):
    del self.session


def __del_TokenAuth__(self):
    del self.client
    del self.hooks


def patch_authlib():
    """Patch `__del__` in `OAuth2Session` and `TokenAuth` to avoid memory leaks.

    Those changes will remove the circular references between `OAuth2Session` and `TokenAuth`
    allowing memory to be freed immediately, without the need of a deep garbage collection cycle.
    Issue: https://github.com/lepture/authlib/issues/698
    """
    OAuth2Session.__del__ = __del_OAuth2Session__
    TokenAuth.__del__ = __del_TokenAuth__
