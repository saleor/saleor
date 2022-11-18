from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from ..celeryconf import app
from .models import Checkout

task_logger = get_task_logger(__name__)

# Batch size of 2000 is about ~27MB of memory usage in task.
CHECKOUT_BATCH_SIZE = 2000


def _batch_tokens(iterable, batch_size=1):
    length = len(iterable)
    for index in range(0, length, batch_size):
        yield iterable[index : min(index + batch_size, length)]


def queryset_in_batches(queryset):
    tokens = queryset.values_list("token", flat=True)
    for tokens_batch in _batch_tokens(tokens, CHECKOUT_BATCH_SIZE):
        yield tokens_batch


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
    qs = Checkout.objects.filter(
        empty_checkouts | expired_anonymous_checkouts | expired_user_checkout
    )

    deleted_count = 0
    for tokens_batch in queryset_in_batches(qs):
        batch_count, _ = Checkout.objects.filter(token__in=tokens_batch).delete()
        deleted_count += batch_count

    if deleted_count:
        task_logger.debug("Removed %s checkouts.", deleted_count)
