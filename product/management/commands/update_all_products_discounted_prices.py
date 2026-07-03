import logging

from django.core.management.base import BaseCommand

from ...models import Product
from ...utils.variant_prices import update_discounted_prices_for_promotion

logger = logging.getLogger(__name__)

DISCOUNTED_PRODUCT_BATCH = 500


class Command(BaseCommand):
    help = "Recalculates the discounted prices for products in all channels."

    def handle(self, *args, **options):
        self.stdout.write('Updating "discounted_price" field of all the products.')
        # Run the update on all the products
        for batch_pks in queryset_in_batches(Product.objects.all()):
            product_batch = Product.objects.filter(pk__in=batch_pks)
            product_ids = ", ".join([str(product.pk) for product in product_batch])
            self.stdout.write(f"Updating products with PK: {product_ids}")
            update_discounted_prices_for_promotion(product_batch)


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.order_by("pk").filter(pk__gt=start_pk)[:DISCOUNTED_PRODUCT_BATCH]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]
