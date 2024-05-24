from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

from ..celeryconf import app
from .events import gift_cards_deactivated_event
from .models import GiftCard
from .search import update_gift_cards_search_vector

task_logger = get_task_logger(__name__)
GIFT_CARD_BATCH_SIZE = 300


@app.task
def deactivate_expired_cards_task():
    today = timezone.now().date()
    gift_cards = GiftCard.objects.filter(expiry_date__lt=today, is_active=True)
    if not gift_cards:
        return
    gift_card_ids = list(gift_cards.values_list("id", flat=True))
    count = gift_cards.update(is_active=False)
    gift_cards_deactivated_event(gift_card_ids, user=None, app=None)
    task_logger.debug("Deactivate %s gift cards", count)


@app.task(
    queue=settings.UPDATE_SEARCH_VECTOR_INDEX_QUEUE_NAME,
    expires=settings.BEAT_UPDATE_SEARCH_EXPIRE_AFTER_SEC,
)
def update_gift_cards_search_vector_task():
    gift_cards = GiftCard.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).filter(search_index_dirty=True)
    if not gift_cards:
        return
    gift_cards_batch = list(gift_cards[:GIFT_CARD_BATCH_SIZE])
    update_gift_cards_search_vector(gift_cards_batch)
