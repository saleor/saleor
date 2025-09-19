import logging

from django.conf import settings

from ..celeryconf import app
from .models import Page
from .search import update_pages_search_vector

logger = logging.getLogger(__name__)


PAGE_BATCH_SIZE = 200


@app.task(
    queue=settings.UPDATE_SEARCH_VECTOR_INDEX_QUEUE_NAME,
    expires=settings.BEAT_UPDATE_SEARCH_EXPIRE_AFTER_SEC,
)
def update_pages_search_vector_task():
    pages = list(
        Page.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME).filter(
            search_index_dirty=True
        )[:PAGE_BATCH_SIZE]
    )
    if not pages:
        return
    update_pages_search_vector(pages)
