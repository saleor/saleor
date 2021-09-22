from dataclasses import dataclass
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth

REQUEST_TIMEOUT = 15


@dataclass
class ApiConfig:
    test_mode: bool
    merchant_code: str
    terminal_id: str
    sp_code: str


def get_url(config: ApiConfig, path="") -> str:
    """Resolve test/production URLs based on the api config."""
    if config.test_mode:
        return f"https://ctcp.np-payment-gateway.com/v1{path}"
    return f"https://cp.np-payment-gateway.com/v1{path}"


def _request(
    config: ApiConfig, method: str, path="", json: Optional[dict] = None
) -> requests.Response:
    if json is None:
        json = {}
    return requests.request(
        method=method,
        url=get_url(config, path),
        timeout=REQUEST_TIMEOUT,
        json=json,
        auth=HTTPBasicAuth(config.merchant_code, config.sp_code),
        headers={"X-NP-Terminal-Id": config.terminal_id},
    )


def health_check(config: ApiConfig) -> bool:
    response = _request(config, "post", "/authorizations/find")
    return response.status_code not in [401, 403]
