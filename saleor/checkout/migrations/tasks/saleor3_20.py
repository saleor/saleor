from decimal import Decimal

from django.db import transaction
from django.db.models import OuterRef

from ....celeryconf import app
from ....core.prices import quantize_price
from ....product.models import ProductVariantChannelListing
from ....tax.models import TaxConfiguration
from ...models import CheckoutLine

# The batch uses 11.39MB of memory. It takes 0.42 seconds to process batch when having
# over 5 mln records to process.
BATCH_SIZE = 500


@app.task
def propagate_lines_undiscounted_unit_price_task(start_pk=0):
    with transaction.atomic():
        checkout_line_pks = list(
            CheckoutLine.objects.filter(
                pk__gt=start_pk, undiscounted_unit_price_amount__isnull=True
            )
            .order_by("id")
            .select_for_update()
            .values_list("id", flat=True)[:BATCH_SIZE]
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
