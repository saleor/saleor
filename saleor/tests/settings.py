import re
from typing import List, Pattern, Union

from django.utils.functional import SimpleLazyObject

from ..settings import *  # noqa


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


POPULATE_DEFAULTS = False

CELERY_TASK_ALWAYS_EAGER = True

SECRET_KEY = "NOTREALLY"

ALLOWED_CLIENT_HOSTS = ["www.example.com"]

TIME_ZONE = "America/Chicago"
LANGUAGE_CODE = "en"


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

COUNTRIES_ONLY = None

MEDIA_ROOT = None
MEDIA_URL = "/media/"
MAX_CHECKOUT_LINE_QUANTITY = 50

AUTH_PASSWORD_VALIDATORS = []

PASSWORD_HASHERS = ["saleor.tests.dummy_password_hasher.DummyHasher"]

PLUGINS = []

PATTERNS_IGNORED_IN_QUERY_CAPTURES: List[Union[Pattern, SimpleLazyObject]] = [
    lazy_re_compile(r"^SET\s+")
]

INSTALLED_APPS.append("saleor.tests")  # noqa: F405

JWT_EXPIRE = True

DEFAULT_CHANNEL_SLUG = "main"

RSA_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAmjTsKENcArpmBM0E74xHAYj3bYJuPMsnBjvPC1sGJKYTvmzn
5r74ogouzYSqVJGMZcVCMi6IOyJZXsDWz9YB5bJvOu8rKgzkh2wBgDvYAwnOlaBo
MKAQn2dxdeP4D4cTGqFPTh17bTwP9aNyXUs8+RE3U6U28AUywBTHLAiq/NlaUETt
HFddB6FTxrMCA/8x9tarSW4+uYP15HgvKRdf5VtG7/RpMRpI2xvYwjVRqhJkcqhW
Z/zLWURu0IxH0PuzqeKRP1q95vQvFLk8EIQfQbDHLRctpdkLcOKsbftYgVaLJv9z
EivAZMZyJNx+bHhBhVOA9aLmnZizgZuCPfsnhQIDAQABAoIBAQCHYqNbjhgABSqA
WIdW0O+eN2QT7wldsnZmkKfsLlQsZOq8qtzGxy9/BDWnFix85vQ+fXrql9PfJv8T
o3Z1LkyoH4psUYKx/nO9OWPv85powHlxAE25My6k5KrGeAlXiJ2LKch4qoWsl6jj
XkaQBfhYK3dJpqme/NFbtmJPFKUaK1SdrtKDceuJGYrKw4xtzSN2ioiZEcb4jWNg
p0pt4/nE/oQwXdKyvL07I4OHEeugu4JXd8OIrnvDOFRrfliHXoe+89Up8n42Q8O1
+qrnorCUIheFRdzcHqTh4O0QUXz0nxSQ0O4Nq08LCdNLDfe7y14/NGNko5sQbNGE
5/AOJXuBAoGBAMrAS48NK1xU4wslM/B3DmeC+wvheCNZgUC0YhvaDe2Drd/KkqSK
+9NGQwkCOveHxROV5B4jgDijaimleLV8e9RAroJqYeCNmFP2Bja7EVzzOJjdItH0
PWVrcLfvGlUz//KpHsA1tDpKguSdTvaMrbIsUQ9pW0zxo9tm14AAyssVAoGBAMK0
zq47tzcCijpo5EZACr315m3jTSSFbVITlyJMIlrpd3kSj8S8QshxyuQv5XtpToVy
rbF9Rsw0ZbX1BhTYXHXy2MJXeDyRdHFIXn/PmW5Ilad3wE957HEwUZ0kig0pPvTA
YNLm48wWZeiKAxpKZh0mr5ZWq760/SfTv9lQiUaxAoGANxrUbmjR5CJeIuVVnIF/
NLrwqGX7VQA6lO9xysgVCPzFARH5kScFEoMCLSyiAiywb4ZJnbdgXgRsEi2bBRh0
P1flFiT7vSA+ynMPdUiai3y/YSyZDh8noKz20cb2jTm40qcMaIkwFrexo5jtoSzS
+J362gl0exEhy7vDzlJoy5ECgYEAgqlrealBTn053fC+IBaiHtCCDoRXJIcV0dqr
tax58aBzOKCoMlJUTsdubKtnyOXmd895mH6FoEwZZX5E0oBPrCeIJwMkASFrjwoN
wJ/ESyoSpAvM1ojvjxXp7xayPhrL0Nu5Hk8r163APclAQ8hhtnZbpvwKzTQQH0YO
nPta5EECgYEAtGnUpVb1lfBT6HByscXJHViGxAblACFySPpHEYzf3ioaGnvUgf14
FdkAmFzQhgLtnEtnb+eBI7DNOJEuPLD52Jwnq2pGnJ/LxlqjjWJ5FsQQVSoDHGfM
8yodVX6OCKwHYrgleLjVWs5ZmaGfGpqcy1YgquiYGVF4x8qBe5bpwHw=
-----END RSA PRIVATE KEY-----"""

DATABASE_CONNECTION_REPLICA_NAME = DATABASE_CONNECTION_DEFAULT_NAME  # noqa: F405
