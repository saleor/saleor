from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from ..celeryconf import app
from .models import Checkout

task_logger = get_task_logger(__name__)


@app.task
def delete_expired_checkouts():
    now = timezone.now()
    expired_anonymous_checkouts = (
        Q(email__isnull=True)
        & Q(user__isnull=True)
        & Q(last_change__lt=now - settings.ANONYMOUS_CHECKOUTS_TIMEDELTA)
    )
    expired_user_checkout = (Q(email__isnull=False) | Q(user__isnull=False)) & Q(
        last_change__lt=now - settings.USER_CHECKOUTS_TIMEDELTA
    )
    empty_checkouts = Q(lines__isnull=True) & Q(
        last_change__lt=now - settings.EMPTY_CHECKOUTS_TIMEDELTA
    )
    count, _ = Checkout.objects.filter(
        empty_checkouts | expired_anonymous_checkouts | expired_user_checkout
    ).delete()
    if count:
        task_logger.debug("Removed %s checkouts.", count)
