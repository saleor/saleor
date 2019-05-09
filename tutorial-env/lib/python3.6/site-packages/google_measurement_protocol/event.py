from typing import Dict, Generator


def event(
        category: str, action: str, label: str=None, value: int=None,
        **extra_data) -> Generator[Dict, None, None]:
    payload = {'t': 'event', 'ec': category, 'ea': action}
    if label:
        payload['el'] = label
    if value:
        payload['ev'] = str(int(value))
    payload.update(extra_data)
    yield payload
