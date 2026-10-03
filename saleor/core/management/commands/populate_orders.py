from django.core.management.base import BaseCommand

from ...utils.random_data import create_orders


class Command(BaseCommand):
    help = (
        "Create sample orders placed within the last 30 days. "
        "Requires the catalog and customers created by populatedb."
    )

    def handle(self, *args, **options):
        for msg in create_orders(20):
            self.stdout.write(msg)
