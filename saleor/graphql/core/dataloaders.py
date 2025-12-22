import threading
from collections import defaultdict
from collections.abc import Iterable
from typing import TypeVar

from promise import Promise
from promise.dataloader import DataLoader as BaseLoader

from ...core.db.connection import allow_writer_in_context
from ...core.telemetry import saleor_attributes, tracer
from ...thumbnail.models import Thumbnail
from ...thumbnail.utils import get_thumbnail_format
from . import SaleorContext
from .context import get_database_connection_name

K = TypeVar("K")
R = TypeVar("R")


class DataLoader[K, R](BaseLoader):
    context_key: str
    thread_id: int
    context: SaleorContext
    database_connection_name: str

    def __new__(cls, context: SaleorContext):
        key = cls.context_key
        if key is None:
            raise TypeError(f"Data loader {cls} does not define a context key")
        if not hasattr(context, "dataloaders"):
            context.dataloaders = {}
        if key not in context.dataloaders:
            context.dataloaders[key] = super().__new__(cls)
        loader = context.dataloaders[key]
        assert isinstance(loader, cls)
        return loader

    def __init__(self, context: SaleorContext) -> None:
        thread_id = threading.get_native_id()
        current_thread_id = getattr(self, "thread_id", None)
        if current_thread_id != thread_id:
            assert current_thread_id is None, (
                "Dataloaders cannot be shared between threads"
            )

            self.thread_id = thread_id
            self.context = context
            self.database_connection_name = get_database_connection_name(context)
            super().__init__()

    def batch_load_fn(  # pylint: disable=method-hidden
        self, keys: Iterable[K]
    ) -> Promise[list[R]]:
        with tracer.start_as_current_span(
            self.__class__.__name__, end_on_exit=False
        ) as span:
            span.set_attribute(
                saleor_attributes.OPERATION_NAME, "dataloader.batch_load"
            )

            with allow_writer_in_context(self.context):
                results = self.batch_load(keys)

            if not isinstance(results, Promise):
                span.set_attribute(
                    saleor_attributes.GRAPHQL_RESOLVER_ROW_COUNT, len(results)
                )
                span.end()
                return Promise.resolve(results)

            def did_fulfill(results: list[R]) -> list[R]:
                span.set_attribute(
                    saleor_attributes.GRAPHQL_RESOLVER_ROW_COUNT, len(results)
                )
                span.end()
                return results

            def did_reject(error: Exception) -> list[R]:
                span.end()
                raise error

            return results.then(did_fulfill, did_reject)

    def batch_load(self, keys: Iterable[K]) -> Promise[list[R]] | list[R]:
        raise NotImplementedError()


class BaseThumbnailBySizeAndFormatLoader(
    DataLoader[tuple[int, int, str | None], Thumbnail]
):
    model_name: str

    def batch_load(self, keys: Iterable[tuple[int, int, str | None]]):
        model_name = self.model_name.lower()
        instance_ids = [id for id, _, _ in keys]
        lookup = {f"{model_name}_id__in": instance_ids}
        thumbnails = Thumbnail.objects.using(self.database_connection_name).filter(
            **lookup
        )
        thumbnails_by_instance_id_size_and_format_map: defaultdict[
            tuple[int, int, str | None], Thumbnail
        ] = defaultdict()
        for thumbnail in thumbnails:
            format = get_thumbnail_format(thumbnail.format)
            thumbnails_by_instance_id_size_and_format_map[
                (getattr(thumbnail, f"{model_name}_id"), thumbnail.size, format)
            ] = thumbnail
        return [thumbnails_by_instance_id_size_and_format_map.get(key) for key in keys]
