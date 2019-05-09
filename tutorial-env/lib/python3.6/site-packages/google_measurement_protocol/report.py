from typing import Dict, Generator, Iterable

import requests

TRACKING_URI = 'https://ssl.google-analytics.com/collect'


def report(
        tracking_id: str, client_id: str, payloads: Iterable[Dict],
        extra_headers: Dict[str, str]=None,
        **extra_data) -> Iterable[requests.Response]:
    """Actually report measurements to Google Analytics."""
    return [
        _make_request(data, extra_headers) for data in _finalize_payloads(
            tracking_id, client_id, payloads, **extra_data)]


def _make_request(
        data: Dict, extra_headers: Dict[str, str]) -> requests.Response:
    return requests.post(
        TRACKING_URI, data=data, headers=extra_headers, timeout=5.0)


def _finalize_payloads(
        tracking_id: str, client_id: str, payloads: Iterable[Dict],
        **extra_data) -> Generator[Dict, None, None]:
    """Get final data for API requests for Google Analytics.

    Updates payloads setting required non-specific values on data.
    """
    extra_payload = {
        'v': '1', 'tid': tracking_id, 'cid': client_id, 'aip': '1'}

    for payload in payloads:
        final_payload = dict(payload)
        final_payload.update(extra_payload)
        final_payload.update(extra_data)
        yield final_payload
