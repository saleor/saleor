# flake8: noqa
if False:
    from .promise import Promise
    from typing import Iterator


def iterate_promise(promise):
    # type: (Promise) -> Iterator
    if not promise.is_fulfilled:
        yield from promise.future  # type: ignore
    assert promise.is_fulfilled
    return promise.get()
