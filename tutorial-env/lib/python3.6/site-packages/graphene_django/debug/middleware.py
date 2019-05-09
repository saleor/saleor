from django.db import connections

from promise import Promise

from .sql.tracking import unwrap_cursor, wrap_cursor
from .types import DjangoDebug


class DjangoDebugContext(object):
    def __init__(self):
        self.debug_promise = None
        self.promises = []
        self.enable_instrumentation()
        self.object = DjangoDebug(sql=[])

    def get_debug_promise(self):
        if not self.debug_promise:
            self.debug_promise = Promise.all(self.promises)
        return self.debug_promise.then(self.on_resolve_all_promises)

    def on_resolve_all_promises(self, values):
        self.disable_instrumentation()
        return self.object

    def add_promise(self, promise):
        if self.debug_promise and not self.debug_promise.is_fulfilled:
            self.promises.append(promise)

    def enable_instrumentation(self):
        # This is thread-safe because database connections are thread-local.
        for connection in connections.all():
            wrap_cursor(connection, self)

    def disable_instrumentation(self):
        for connection in connections.all():
            unwrap_cursor(connection)


class DjangoDebugMiddleware(object):
    def resolve(self, next, root, info, **args):
        context = info.context
        django_debug = getattr(context, "django_debug", None)
        if not django_debug:
            if context is None:
                raise Exception("DjangoDebug cannot be executed in None contexts")
            try:
                context.django_debug = DjangoDebugContext()
            except Exception:
                raise Exception(
                    "DjangoDebug need the context to be writable, context received: {}.".format(
                        context.__class__.__name__
                    )
                )
        if info.schema.get_type("DjangoDebug") == info.return_type:
            return context.django_debug.get_debug_promise()
        promise = next(root, info, **args)
        context.django_debug.add_promise(promise)
        return promise
