from django.conf import settings

# nosemgrep: django-no-default-token-generator # _DjangoGenerator is used safely
from django.contrib.auth.tokens import PasswordResetTokenGenerator as _DjangoGenerator
from django.utils.module_loading import import_string

from saleor.account.models import User

_base_token_generator_cls = import_string(settings.TOKEN_GENERATOR_CLASS)

LEGACY_SALT = _base_token_generator_cls.key_salt


class BaseTokenGenerator(_base_token_generator_cls):  # type: ignore[valid-type,misc]
    def __init__(self, *, key_salt: str):
        """Initialize a token generator.

        Args:
            key_salt:
                A custom salt to support.

                This overrides Django's default salt [1] which allows us to create
                different scopes for generated tokens (i.e., token from generator A
                cannot be used in generator B).

        [1]: https://github.com/django/django/blob/73dd0169a54f4bbcb41b29bf7d51a36f86c89afe/django/contrib/auth/tokens.py#L14

        """

        self.key_salt = key_salt
        super().__init__()


class AccountDeleteTokenGenerator(BaseTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Override this method to remove the user `last_login` value from the hash.
        # As this token is used for deleting the user, so there is no worry
        # that the token will be used again.
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, "") or ""
        return f"{user.pk}{user.password}{timestamp}{email}"


def try_generators(
    *,
    current_generator: _DjangoGenerator,
    fallback_generator: _DjangoGenerator,
    user: User,
    token: str,
) -> bool:
    """Try generators with different salts to ensure old tokens work.

    Args:
        current_generator: the generator with the current salt, will be tried first.
        fallback_generator:
            the legacy/old generator to try if `current_generator` rejects the token.
        user: the user who is attempting to use the token.
        token: the token to compare against.

    """
    if current_generator.check_token(user, token) is True:
        return True
    return fallback_generator.check_token(user, token)


# Account delete
account_delete_token_generator = AccountDeleteTokenGenerator(
    key_salt=f"{__name__}.account_delete_token_generator"
)
legacy_account_delete_token_generator = AccountDeleteTokenGenerator(
    key_salt=LEGACY_SALT
)

# Password reset
password_reset_token_generator = BaseTokenGenerator(
    key_salt=f"{__name__}.password_reset_token_generator"
)
legacy_password_reset_token_generator = BaseTokenGenerator(key_salt=LEGACY_SALT)

# Account confirmation
account_confirm_token_generator = BaseTokenGenerator(
    key_salt=f"{__name__}.account_confirm_token_generator"
)
legacy_account_confirm_token_generator = BaseTokenGenerator(key_salt=LEGACY_SALT)
