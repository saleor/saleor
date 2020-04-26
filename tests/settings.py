import re
from typing import List, Pattern, Union

from django.utils.functional import SimpleLazyObject

from saleor.settings import *  # noqa


def lazy_re_compile(regex, flags=0):
    """Lazily compile a regex with flags."""

    def _compile():
        # Compile the regex if it was not passed pre-compiled.
        if isinstance(regex, str):
            return re.compile(regex, flags)
        else:
            assert not flags, "flags must be empty if regex is passed pre-compiled"
            return regex

    return SimpleLazyObject(_compile)


CELERY_TASK_ALWAYS_EAGER = True

SECRET_KEY = "NOTREALLY"

ALLOWED_CLIENT_HOSTS = ["www.example.com"]

DEFAULT_CURRENCY = "USD"

TIME_ZONE = "America/Chicago"
LANGUAGE_CODE = "en"

SEARCH_BACKEND = "saleor.search.backends.postgresql"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

VATLAYER_ACCESS_KEY = ""

COUNTRIES_ONLY = None

MEDIA_ROOT = None
MEDIA_URL = "/media/"
MAX_CHECKOUT_LINE_QUANTITY = 50

AUTH_PASSWORD_VALIDATORS = []

PASSWORD_HASHERS = ["tests.dummy_password_hasher.DummyHasher"]
PLUGINS_MANAGER = "saleor.plugins.manager.PluginsManager"

PLUGINS = []

PATTERNS_IGNORED_IN_QUERY_CAPTURES: List[Union[Pattern, SimpleLazyObject]] = [
    lazy_re_compile(r"^SET\s+")
]

INSTALLED_APPS.append("tests.api.pagination")  # noqa: F405
