from celery.utils.log import get_task_logger
from django.utils import timezone

from ..celeryconf import app
from .events import gift_cards_deactivated_event
from .models import GiftCard

task_logger = get_task_logger(__name__)


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
