from decimal import Decimal

from django.db import transaction
from django.db.models import Exists, OuterRef

from ....celeryconf import app
from ....core.prices import quantize_price
from ....discount import DiscountType
from ....discount.models import CheckoutLineDiscount
from ....product.models import ProductVariantChannelListing
from ....tax.models import TaxConfiguration
from ...models import Checkout, CheckoutLine

# The batch uses 11.39MB of memory. It takes 0.42 seconds to process batch when having
# over 5 mln records to process.
UNDISCOUNTED_UNIT_PRICE_BATCH_SIZE = 500

# Takes about 0.1 second to process
DUPLICATED_LINES_CHECKOUT_BATCH_SIZE = 250


@app.task
def propagate_lines_undiscounted_unit_price_task(start_pk=0):
    with transaction.atomic():
        checkout_line_pks = list(
            CheckoutLine.objects.filter(
                pk__gt=start_pk, undiscounted_unit_price_amount__isnull=True
            )
            .order_by("id")
            .select_for_update()
            .values_list("id", flat=True)[:UNDISCOUNTED_UNIT_PRICE_BATCH_SIZE]
        )
        if checkout_line_pks:
            lines = (
                CheckoutLine.objects.select_related("checkout")
                .annotate(
                    listing_price_amount=ProductVariantChannelListing.objects.filter(
                        variant_id=OuterRef("variant_id"),
                        channel_id=OuterRef("checkout__channel_id"),
                    ).values_list("price_amount", flat=True)
                )
                .order_by("id")
                .filter(
                    id__in=checkout_line_pks,
                )
            )

            channel_ids = {line.checkout.channel_id for line in lines}
            tax_configurations = TaxConfiguration.objects.filter(
                channel_id__in=channel_ids
            ).values_list("channel_id", "prices_entered_with_tax")
            channel_id_to_prices_with_tax_map = dict(tax_configurations)

            for line in lines:
                if line.price_override is not None:
                    line.undiscounted_unit_price_amount = line.price_override
                    continue

                if line.listing_price_amount is not None:
                    line.undiscounted_unit_price_amount = line.listing_price_amount
                    continue

                channel_id = line.checkout.channel_id
                if channel_id_to_prices_with_tax_map.get(channel_id):
                    base_total_price = line.total_price_gross_amount
                else:
                    base_total_price = line.total_price_net_amount

                if base_total_price is Decimal(0) or line.quantity == 0:
                    line.undiscounted_unit_price_amount = Decimal(0)
                else:
                    line.undiscounted_unit_price_amount = quantize_price(
                        base_total_price / line.quantity, line.currency
                    )
            CheckoutLine.objects.bulk_update(lines, ["undiscounted_unit_price_amount"])
            propagate_lines_undiscounted_unit_price_task.delay(checkout_line_pks[-1])


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
