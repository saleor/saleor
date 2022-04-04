from typing import Dict, Tuple

from ...core.auth import DEFAULT_AUTH_HEADER, SALEOR_AUTH_HEADER

SENSITIVE_ENV_KEYS = (SALEOR_AUTH_HEADER, DEFAULT_AUTH_HEADER)
SENSITIVE_HEADERS = tuple(x[5:] for x in SENSITIVE_ENV_KEYS if x.startswith("HTTP_"))
MASK = "***"


def hide_sensitive_headers(
    headers: Dict[str, str], sensitive_headers: Tuple[str, ...] = SENSITIVE_HEADERS
) -> Dict[str, str]:
    return {
        key: val if key.upper().replace("-", "_") not in sensitive_headers else MASK
        for key, val in headers.items()
    }
