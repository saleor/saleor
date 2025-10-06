import logging

from django.conf import settings
from django.db import transaction

from ..celeryconf import app
from ..core.db.connection import allow_writer
from .lock_objects import page_qs_select_for_update
from .models import Page
from .search import update_pages_search_vector

logger = logging.getLogger(__name__)

# TODO: validate the batch size
UPDATE_SEARCH_BATCH_SIZE = 200

# Results in update time ~0.2s, consumes ~30 MB
MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE = 1000


@app.task
@allow_writer()
def mark_pages_search_vector_as_dirty(page_ids: list[int]):
    """Mark pages as needing search index updates."""
    page_ids_to_update = page_ids[:MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE]
    if not page_ids_to_update:
        return
    with transaction.atomic():
        _pages = list(
            page_qs_select_for_update()
            .filter(pk__in=page_ids_to_update)
            .values_list("id", flat=True)
        )
        Page.objects.filter(id__in=page_ids_to_update).update(search_index_dirty=True)

    if len(page_ids) > MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE:
        mark_pages_search_vector_as_dirty.delay(
            page_ids[MARK_SEARCH_VECTOR_DIRTY_BATCH_SIZE:]
        )


@app.task(
    queue=settings.UPDATE_SEARCH_VECTOR_INDEX_QUEUE_NAME,
    expires=settings.BEAT_UPDATE_SEARCH_EXPIRE_AFTER_SEC,
)
def update_pages_search_vector_task():
    pages = list(
        Page.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).filter(
            search_index_dirty=True
        )[:UPDATE_SEARCH_BATCH_SIZE]
    )
    if not pages:
        return

    update_pages_search_vector(pages)
