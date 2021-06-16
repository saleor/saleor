import logging

from django.core.management.base import BaseCommand

from ....discount.utils import fetch_active_discounts
from ...models import Product
from ...utils.variant_prices import update_product_discounted_price

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Recalculates the discounted prices for products in all channels."

    def handle(self, *args, **options):
        self.stdout.write('Updating "discounted_price" field of all the products.')
        # Fetching the discounts just once and reusing them
        discounts = fetch_active_discounts()
        # Run the update on all the products
        qs = Product.objects.all()
        for product in qs.iterator():
            self.stdout.write(f"Updating product PK: {product.pk}")
            update_product_discounted_price(product, discounts=discounts)
