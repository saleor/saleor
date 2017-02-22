from ...site.utils import get_authorization_key_for_backend


class BaseBackend(object):
    def get_key_and_secret(self):
        """Return tuple with Consumer Key and Consumer Secret for current
        service provider. Must return (key, secret), order *must* be respected.
        """
        return get_authorization_key_for_backend(self.DB_NAME).key_and_secret()
