from typing import Any

from django.core.management import BaseCommand

from ....product.models import Product
from ...search_tasks import set_product_search_document_values


class Command(BaseCommand):
    help = "Used to set search document values for product."

    def handle(self, *args: Any, **options: Any):
        total_count = Product.objects.filter(search_document="").count()
        set_product_search_document_values.delay(total_count, 0)
