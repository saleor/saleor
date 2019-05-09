from typing import Dict, Generator


def pageview(
        path: str=None, host_name: str=None, location: str=None,
        title: str=None, language: str=None, referrer: str=None,
        **extra_data) -> Generator[Dict, None, None]:
    payload = {'t': 'pageview'}

    if location:
        payload['dl'] = location
    if host_name:
        payload['dh'] = host_name
    if path:
        payload['dp'] = path
    if title:
        payload['dt'] = title
    if referrer:
        payload['dr'] = referrer
    if language:
        payload['ul'] = language

    payload.update(extra_data)
    yield payload
