import inspect
from functools import partial
from itertools import chain

from promise import Promise, promisify

# Necessary for static type checking
if False:  # flake8: noqa
    from .base import ResolveInfo
    from typing import Any, Callable, Iterator, Tuple, Union, List, Dict, Iterable

MIDDLEWARE_RESOLVER_FUNCTION = "resolve"


class MiddlewareManager(object):
    __slots__ = (
        "middlewares",
        "wrap_in_promise",
        "_middleware_resolvers",
        "_cached_resolvers",
    )

    def __init__(self, *middlewares, **kwargs):
        # type: (*Callable, **bool) -> None
        self.middlewares = middlewares
        self.wrap_in_promise = kwargs.get("wrap_in_promise", True)
        self._middleware_resolvers = (
            list(get_middleware_resolvers(middlewares)) if middlewares else []
        )
        self._cached_resolvers = {}  # type: Dict[Callable, Callable]

    def get_field_resolver(self, field_resolver):
        # type: (Callable) -> Callable
        if field_resolver not in self._cached_resolvers:
            self._cached_resolvers[field_resolver] = middleware_chain(
                field_resolver,
                self._middleware_resolvers,
                wrap_in_promise=self.wrap_in_promise,
            )

        return self._cached_resolvers[field_resolver]


middlewares = MiddlewareManager


def get_middleware_resolvers(middlewares):
    # type: (Tuple[Any, ...]) -> Iterator[Callable]
    for middleware in middlewares:
        # If the middleware is a function instead of a class
        if inspect.isfunction(middleware):
            yield middleware
        if not hasattr(middleware, MIDDLEWARE_RESOLVER_FUNCTION):
            continue
        yield getattr(middleware, MIDDLEWARE_RESOLVER_FUNCTION)


def middleware_chain(func, middlewares, wrap_in_promise):
    # type: (Callable, Iterable[Callable], bool) -> Callable
    if not middlewares:
        return func
    if wrap_in_promise:
        middlewares = chain((func, make_it_promise), middlewares)
    else:
        middlewares = chain((func,), middlewares)
    last_func = None
    for middleware in middlewares:
        last_func = partial(middleware, last_func) if last_func else middleware

    return last_func  # type: ignore


@promisify
def make_it_promise(next, *args, **kwargs):
    # type: (Callable, *Any, **Any) -> Any
    return next(*args, **kwargs)
