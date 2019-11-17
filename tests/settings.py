import re

from django.utils.functional import SimpleLazyObject
from typing import List, Pattern, Union

# pylint: disable=W0401, W0614
# flake8: noqa
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

ES_URL = None
SEARCH_BACKEND = "saleor.search.backends.postgresql"
INSTALLED_APPS = [a for a in INSTALLED_APPS if a != "django_elasticsearch_dsl"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

RECAPTCHA_PUBLIC_KEY = ""
RECAPTCHA_PRIVATE_KEY = ""

VATLAYER_ACCESS_KEY = ""

if "sqlite" in DATABASES["default"]["ENGINE"]:  # noqa
    DATABASES["default"]["TEST"] = {  # noqa
        "SERIALIZE": False,
        "NAME": ":memory:",
        "MIRROR": None,
    }

COUNTRIES_ONLY = None

MEDIA_ROOT = None
MAX_CHECKOUT_LINE_QUANTITY = 50

USE_JSON_CONTENT = False

AUTH_PASSWORD_VALIDATORS = []

PASSWORD_HASHERS = ["tests.dummy_password_hasher.DummyHasher"]
EXTENSIONS_MANAGER = "saleor.extensions.manager.ExtensionsManager"

PLUGINS = []

PATTERNS_IGNORED_IN_QUERY_CAPTURES: List[Union[Pattern, SimpleLazyObject]] = [
    lazy_re_compile(r"^SET\s+")
]
