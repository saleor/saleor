"""Definitions of sensitive data for observability obfuscation methods.

SENSITIVE_HEADERS is a tuple of sensitive HTTP headers to anonymize before reporting.

SENSITIVE_GQL_FIELDS is a dict of sets representing fields of GraphGL types to anonymize
- Type
- Fields
"""
from typing import Dict, Set

from ...core.auth import DEFAULT_AUTH_HEADER, SALEOR_AUTH_HEADER

SENSITIVE_HEADERS = (
    SALEOR_AUTH_HEADER,
    DEFAULT_AUTH_HEADER,
    "COOKIE",
)
SENSITIVE_HEADERS = tuple(
    x[5:] if x.startswith("HTTP_") else x for x in SENSITIVE_HEADERS
)

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
