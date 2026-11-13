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


class SessionIndependentTokenGenerator(BaseTokenGenerator):
    """Django's token generator with `last_login` left out of the hash.

    `last_login` tracks activity here, not just authentication: it is stamped on
    token refresh and on requests carrying an OIDC access token. Django hashes it
    so a link expires once its owner signs back in; here that would expire links
    while the user simply has a session open.

    The password hash is still part of the value, so a link is spent by the reset
    that uses it.
    """

    def _make_hash_value(self, user, timestamp):
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
account_delete_token_generator = SessionIndependentTokenGenerator(
    key_salt=f"{__name__}.account_delete_token_generator"
)
legacy_account_delete_token_generator = SessionIndependentTokenGenerator(
    key_salt=LEGACY_SALT
)

# Password reset
password_reset_token_generator = SessionIndependentTokenGenerator(
    key_salt=f"{__name__}.password_reset_token_generator"
)
legacy_password_reset_token_generator = SessionIndependentTokenGenerator(
    key_salt=LEGACY_SALT
)

# Account confirmation
account_confirm_token_generator = BaseTokenGenerator(
    key_salt=f"{__name__}.account_confirm_token_generator"
)
legacy_account_confirm_token_generator = BaseTokenGenerator(key_salt=LEGACY_SALT)
