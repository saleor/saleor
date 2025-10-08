from django.conf import settings
from django.db import transaction

from ..celeryconf import app
from ..core.db.connection import allow_writer
from .lock_objects import page_qs_select_for_update
from .models import Page
from .search import update_pages_search_vector

# Results in update time ~1s, consumes ~25 MB
UPDATE_SEARCH_BATCH_SIZE = 200


@app.task
@allow_writer()
def mark_pages_search_vector_as_dirty(page_ids: list[int]):
    """Mark pages as needing search index updates."""
    if not page_ids:
        return
    with transaction.atomic():
        ids = page_qs_select_for_update().filter(pk__in=page_ids).values("id")
        Page.objects.filter(id__in=ids).update(search_index_dirty=True)


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
