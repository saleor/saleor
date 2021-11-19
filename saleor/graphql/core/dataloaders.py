from typing import Generic, Iterable, List, TypeVar, Union

import opentracing
import opentracing.tags
from django.http import HttpRequest
from promise import Promise
from promise.dataloader import DataLoader as BaseLoader

from ...core.db.utils import get_database_connection_name

K = TypeVar("K")
R = TypeVar("R")


class DataLoader(BaseLoader, Generic[K, R]):
    context_key = None
    context = None
    database_connection_name = None

    def __new__(cls, context: HttpRequest):
        key = cls.context_key
        if key is None:
            raise TypeError("Data loader %r does not define a context key" % (cls,))
        if not hasattr(context, "dataloaders"):
            context.dataloaders = {}
        if key not in context.dataloaders:
            context.dataloaders[key] = super().__new__(cls, context)
        loader = context.dataloaders[key]
        assert isinstance(loader, cls)
        cls.database_connection_name = get_database_connection_name(context)
        return loader

    def __init__(self, context):
        if self.context != context:
            self.context = context
            self.user = context.user
            super().__init__()

    def batch_load_fn(self, keys: Iterable[K]) -> Promise[List[R]]:
        with opentracing.global_tracer().start_active_span(
            self.__class__.__name__
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "dataloaders")
            results = self.batch_load(keys)
            if not isinstance(results, Promise):
                return Promise.resolve(results)
            return results

    def batch_load(self, keys: Iterable[K]) -> Union[Promise[List[R]], List[R]]:
        raise NotImplementedError()
