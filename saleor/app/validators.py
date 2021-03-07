import re

from django.core.validators import URLValidator
from django.utils.regex_helper import _lazy_re_compile  # type: ignore


class AppURLValidator(URLValidator):
    validator = URLValidator
    host_re = "(" + validator.hostname_re + validator.domain_re + "|localhost)"
    regex = _lazy_re_compile(
        r"^(?:[a-z0-9.+-]*)://"  # scheme is validated separately
        r"(?:[^\s:@/]+(?::[^\s:@/]*)?@)?"  # user:pass authentication
        r"(?:" + validator.ipv4_re + "|" + validator.ipv6_re + "|" + host_re + ")"
        r"(?::\d{2,5})?"  # port
        r"(?:[/?#][^\s]*)?"  # resource path
        r"\Z",
        re.IGNORECASE,
    )
