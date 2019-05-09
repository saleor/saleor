from promise import Promise
from promise.promise import Promise
from typing import Any


def resolved(value):
    # type: (Any) -> Promise
    return Promise.fulfilled(value)


def rejected(error):
    # type: (Exception) -> Promise
    return Promise.rejected(error)
