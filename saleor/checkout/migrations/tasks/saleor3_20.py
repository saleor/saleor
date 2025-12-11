from django.db.models import Exists, OuterRef

from ....celeryconf import app
from ....discount import DiscountType
from ....discount.models import CheckoutLineDiscount
from ...models import Checkout, CheckoutLine

# Takes about 0.1 second to process
DUPLICATED_LINES_CHECKOUT_BATCH_SIZE = 250


@app.task
def clean_duplicated_gift_lines_task(created_after=None):
    extra_order_filter = {}
    if created_after:
        extra_order_filter["created_at__gt"] = created_after

    # fetch gift line discounts to narrow down the filter on checkout lines
    gift_line_discounts = CheckoutLineDiscount.objects.filter(
        type=DiscountType.ORDER_PROMOTION, line__isnull=False
    )
    gift_lines = CheckoutLine.objects.filter(
        Exists(gift_line_discounts.filter(line_id=OuterRef("id")))
    )

    checkout_data = list(
        Checkout.objects.filter(Exists(gift_lines.filter(checkout_id=OuterRef("pk"))))
        .order_by("created_at")
        .filter(**extra_order_filter)
        .values_list("pk", "created_at")[:DUPLICATED_LINES_CHECKOUT_BATCH_SIZE]
    )

    checkout_ids = [data[0] for data in checkout_data]
    if not checkout_ids:
        return

    checkout_created_after = checkout_data[-1][1]
    lines = CheckoutLine.objects.filter(
        checkout_id__in=checkout_ids, is_gift=True
    ).order_by("checkout_id", "id")
    seen_checkouts = set()
    lines_to_delete = []
    for line in lines:
        if line.checkout_id in seen_checkouts:
            lines_to_delete.append(line.id)
        else:
            seen_checkouts.add(line.checkout_id)

    CheckoutLine.objects.filter(id__in=lines_to_delete).delete()
    clean_duplicated_gift_lines_task.delay(created_after=checkout_created_after)
