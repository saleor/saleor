from functools import partial, wraps
from typing import Optional

from django.utils.functional import LazyObject
from promise import Promise

from ....app.models import App
from ....core.auth import get_token_from_request
from ....core.utils.lazyobjects import unwrap_lazy
from ...core import SaleorContext
from .app import AppByTokenLoader


def promise_app(context: SaleorContext) -> Promise[Optional[App]]:
    auth_token = get_token_from_request(context)
    if not auth_token or len(auth_token) != 30:
        return Promise.resolve(None)
    return AppByTokenLoader(context).load(auth_token)


def get_app_promise(context: SaleorContext) -> Promise[Optional[App]]:
    if hasattr(context, "app"):
        app = context.app
        if isinstance(app, LazyObject):
            app = unwrap_lazy(app)
        return Promise.resolve(app)

    return promise_app(context)


def app_promise_callback(func):
    @wraps(func)
    def _wrapper(root, info, *args, **kwargs):
        return get_app_promise(info.context).then(
            partial(func, root, info, *args, **kwargs)
        )

    return _wrapper
