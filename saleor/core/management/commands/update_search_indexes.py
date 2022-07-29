from django.core.management.base import BaseCommand

from saleor.order.models import Order

from ...search_tasks import set_order_search_document_values


class Command(BaseCommand):
    help = "Populate search indexes."

    def handle(self, *args, **options):
        # Update orders
        self.stdout.write("Updating orders")
        Order.objects.update(search_vector=None, search_document="")
        set_order_search_document_values.delay()
