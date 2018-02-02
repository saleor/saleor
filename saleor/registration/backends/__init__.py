from ...site.utils import get_authorization_key_for_backend


class BaseBackend:
    def get_key_and_secret(self):
        """Return a tuple of `(key, secret)` for current provider."""
        # pylint: disable=maybe-no-member
        authorization_key = get_authorization_key_for_backend(self.DB_NAME)
        if authorization_key:
            return authorization_key.key_and_secret()
        return None
