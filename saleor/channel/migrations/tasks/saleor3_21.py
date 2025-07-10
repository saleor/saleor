from django.conf import settings
from django.db import transaction
from django.db.models import Q

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import Channel

BATCH_SIZE = 5000


@app.task
@allow_writer()
def migrate_env_variable_setting_to_channels():
    turn_on = int(settings.TRANSACTION_BATCH_FOR_RELEASING_FUNDS) > 0
    channels = Channel.objects.order_by("pk").filter(
        ~Q(
            checkout_ttl_before_releasing_funds=settings.CHECKOUT_TTL_BEFORE_RELEASING_FUNDS
        )
        | ~Q(release_funds_for_expired_checkouts=turn_on)
    )
    ids = channels.values_list("pk", flat=True)[:BATCH_SIZE]

    qs = Channel.objects.filter(pk__in=ids).order_by("pk")
    if ids:
        with transaction.atomic():
            # lock the batch of objects
            _channels = list(qs.select_for_update(of=(["self"])))
            qs.update(
                checkout_ttl_before_releasing_funds=settings.CHECKOUT_TTL_BEFORE_RELEASING_FUNDS,
                release_funds_for_expired_checkouts=turn_on,
            )
        migrate_env_variable_setting_to_channels.delay()
