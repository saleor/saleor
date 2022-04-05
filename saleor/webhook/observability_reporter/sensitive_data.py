from typing import Dict, Set

from ...core.auth import DEFAULT_AUTH_HEADER, SALEOR_AUTH_HEADER

SensitiveFieldsMap = Dict[str, Set[str]]

SENSITIVE_HEADERS = (
    SALEOR_AUTH_HEADER,
    DEFAULT_AUTH_HEADER,
)
SENSITIVE_HEADERS = tuple(
    x[5:] if x.startswith("HTTP_") else x for x in SENSITIVE_HEADERS
)

SENSITIVE_GQL_FIELDS: SensitiveFieldsMap = {
    "RefreshToken": {"token"},
}
