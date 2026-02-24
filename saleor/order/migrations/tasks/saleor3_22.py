from decimal import Decimal

from django.conf import settings
from django.db import transaction

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ....giftcard import GiftCardEvents
from ....giftcard.models import GiftCardEvent
from ....product.models import Product, ProductVariant
from ...models import OrderGiftCardApplication, OrderLine

ORDER_LINE_PRODUCT_ID_BATCH_SIZE = 250
GIFT_CARD_APPLICATION_BATCH_SIZE = 500


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def populate_order_line_product_type_id_task(line_pk=None):
    """Populate product id for order lines."""
    if line_pk is None:
        line_pk = 0
    lines = OrderLine.objects.filter(
        pk__gte=line_pk, variant__isnull=False, product_type_id__isnull=True
    )
    qs = lines.order_by("pk")

    line_id_with_variant_id = qs.values_list("pk", "variant_id")[
        :ORDER_LINE_PRODUCT_ID_BATCH_SIZE
    ]

    variant_id_to_product_id = dict(
        ProductVariant.objects.filter(
            pk__in=[variant_id for _, variant_id in line_id_with_variant_id]
        ).values_list("id", "product_id")
    )

    product_id_to_product_type_id_map = dict(
        Product.objects.filter(pk__in=variant_id_to_product_id.values()).values_list(
            "id", "product_type_id"
        )
    )
    variant_id_to_product_type_id = {
        variant_id: product_id_to_product_type_id_map[product_id]
        for variant_id, product_id in variant_id_to_product_id.items()
    }

    line_pks = [line_id for (line_id, _) in line_id_with_variant_id]
    if line_pks:
        lines = OrderLine.objects.filter(pk__in=line_pks).order_by("pk")
        with transaction.atomic():
            to_save = []
            _lines_lock = list(lines.select_for_update(of=(["self"])))
            for line in lines:
                product_type_id = variant_id_to_product_type_id.get(line.variant_id)
                if not product_type_id:
                    continue
                line.product_type_id = product_type_id
                to_save.append(line)
            OrderLine.objects.bulk_update(to_save, ["product_type_id"])
        populate_order_line_product_type_id_task.delay(line_pks[-1])


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
def populate_order_gift_card_applications_task(start_event_pk=None):
    start_event_pk = start_event_pk or 0
    events = list(
        GiftCardEvent.objects.filter(
            pk__gte=start_event_pk,
            type=GiftCardEvents.USED_IN_ORDER,
            order__isnull=False,
        )
        .using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .order_by("pk")
        .values("pk", "order_id", "gift_card_id", "parameters")[
            :GIFT_CARD_APPLICATION_BATCH_SIZE
        ]
    )
    if not events:
        return

    to_create = []
    for event in events:
        balance = event["parameters"].get("balance", {})
        currency = balance.get("currency")
        old_balance = balance.get("old_current_balance")
        current_balance = balance.get("current_balance")
        if None in (currency, old_balance, current_balance):
            continue
        amount_used = Decimal(str(old_balance)) - Decimal(str(current_balance))
        if amount_used > 0:
            to_create.append(
                OrderGiftCardApplication(
                    order_id=event["order_id"],
                    gift_card_id=event["gift_card_id"],
                    amount_used_amount=amount_used,
                    currency=currency,
                )
            )

    with allow_writer():
        OrderGiftCardApplication.objects.bulk_create(to_create, ignore_conflicts=True)

    populate_order_gift_card_applications_task.delay(events[-1]["pk"] + 1)
