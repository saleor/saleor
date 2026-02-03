from django.conf import settings

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import GiftCard


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def mark_gift_cards_search_index_as_dirty_task():
    GiftCard.objects.filter(search_index_dirty=False).update(search_index_dirty=True)
