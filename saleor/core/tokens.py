from django.conf import settings
from django.utils.module_loading import import_string

token_generator_cls = import_string(settings.TOKEN_GENERATOR_CLASS)


class AccountDeleteTokenGenerator(token_generator_cls):  # type: ignore[valid-type,misc]
    def _make_hash_value(self, user, timestamp):
        # Override this method to remove the user `last_login` value from the hash.
        # As this token is used for deleting the user, so there is no worry
        # that the token will be used again.
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, "") or ""
        return f"{user.pk}{user.password}{timestamp}{email}"


account_delete_token_generator = AccountDeleteTokenGenerator()
token_generator = token_generator_cls()
