"""Clear the transactions data preserving shop's catalog and configuration.

This command clears the database from data such as orders, checkouts, payments and 
optionally customer accounts. It doesn't remove shop's catalog (products, variants) nor
configuration, such as: warehouses, shipping zones, staff accounts, plugin configurations etc.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q

from ....account.models import User
from ....checkout.models import Checkout
from ....order.models import Order
from ....payment.models import Payment, Transaction


class Command(BaseCommand):
    help = "Removes transactions data preserving shop's catalog and configuration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-customers",
            action="store_true",
            help="Delete cutomers user accounts (doesn't delete staff and superuser accounts).",
        )

    def handle(self, **options):
        Checkout.objects.all().delete()
        self.stdout.write("Removed checkouts")

        Transaction.objects.all().delete()
        self.stdout.write("Removed transactions")

        Payment.objects.all().delete()
        self.stdout.write("Removed payments")

        Order.objects.all().delete()
        self.stdout.write("Removed orders")

        should_delete_customers = options.get("delete_customers")
        if should_delete_customers:
            # Delete all users except for staff members.
            staff = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
            User.objects.exclude(pk__in=staff).delete()
            self.stdout.write("Removed customers")
