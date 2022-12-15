"""Definitions of sensitive data for observability obfuscation methods.

ALLOWED_HEADERS is a set of lowercase HTTP headers allowed for reporting.

SENSITIVE_HEADERS is a set of lowercase HTTP headers to anonymize before reporting.

SENSITIVE_GQL_FIELDS is a dict of sets representing fields of GraphGL types to anonymize
- Type
- Fields
"""
from typing import Dict, Set

from ...app.headers import AppHeaders, DeprecatedAppHeaders

ALLOWED_HEADERS = {
    header.lower()
    for header in {
        "Content-Length",
        "Content-Type",
        "Host",
        "Origin",
        "Referer",
        "Content-Encoding",
        "User-Agent",
        "Cookie",
        "Authorization",
        "Authorization-Bearer",
        DeprecatedAppHeaders.DOMAIN,
        DeprecatedAppHeaders.EVENT_TYPE,
        DeprecatedAppHeaders.SIGNATURE,
        AppHeaders.DOMAIN,
        AppHeaders.EVENT_TYPE,
        AppHeaders.SIGNATURE,
        AppHeaders.API_URL,
    }
}
SENSITIVE_HEADERS = {
    header.lower()
    for header in {
        "Cookie",
        "Authorization",
        "Authorization-Bearer",
    }
}

SensitiveFieldsMap = Dict[str, Set[str]]
SENSITIVE_GQL_FIELDS: SensitiveFieldsMap = {
    "RefreshToken": {"token"},
    "CreateToken": {"token", "refreshToken", "csrfToken"},
    "User": {"email", "firstName", "lastName"},
    "Address": {
        "firstName",
        "lastName",
        "companyName",
        "streetAddress1",
        "streetAddress2",
        "phone",
    },
    "AppTokenCreate": {"authToken"},
    "AppToken": {"authToken"},
    "App": {"accessToken"},
    "Order": {"userEmail"},
    "Payment": {"creditCard"},
    "Checkout": {"email"},
}
