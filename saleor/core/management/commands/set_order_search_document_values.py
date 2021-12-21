from typing import Any

from django.core.management import BaseCommand

from ....order.models import Order
from ...search_tasks import set_order_search_document_values


class Command(BaseCommand):
    help = "Used to set search document values for order."

    def handle(self, *args: Any, **options: Any):
        total_count = Order.objects.filter(search_document="").count()
        set_order_search_document_values.delay(total_count, 0)
