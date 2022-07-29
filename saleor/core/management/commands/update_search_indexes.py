from django.core.management.base import BaseCommand

from ...search_tasks import (
    set_order_search_document_values,
    set_product_search_document_values,
    set_user_search_document_values,
)


class Command(BaseCommand):
    help = "Populate search indexes."

    def handle(self, *args, **options):
        # Update products
        self.stdout.write("Updating products")
        set_product_search_document_values.delay()

        # Update orders
        self.stdout.write("Updating orders")
        set_order_search_document_values.delay()

        # Update users
        self.stdout.write("Updating users")
        set_user_search_document_values.delay()
