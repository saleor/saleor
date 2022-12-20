"""Clear the transactions data preserving shop's catalog and configuration.

This command clears the database from data such as orders, checkouts, payments and
optionally customer accounts. It doesn't remove shop's catalog (products, variants) nor
configuration, such as: warehouses, shipping zones, staff accounts, plugin config etc.
"""

from django.core.management.base import BaseCommand

from ....account.models import User, CustomerEvent
from ....checkout.models import Checkout, CheckoutLine
from ....giftcard.models import GiftCard, GiftCardEvent, GiftCardTag
from ....invoice.models import Invoice, InvoiceEvent
from ....order.models import Fulfillment, FulfillmentLine, Order, OrderEvent, OrderLine
from ....payment.models import Payment, Transaction
from ....warehouse.models import Allocation


class Command(BaseCommand):
    help = "Removes transactions data preserving shop's catalog and configuration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-gift-cards",
            action="store_true",
            help="Delete cutomers gift cards.",
        )
        parser.add_argument(
            "--delete-customers",
            action="store_true",
            help="Delete cutomers user accounts (doesn't delete staff accounts).",
        )

    def handle(self, **options):
        self.delete_checkouts()
        self.delete_payments()
        self.delete_invoices()

        should_delete_gift_cards = options.get("delete_gift_cards")
        should_delete_customers = options.get("delete_customers")

        if should_delete_gift_cards:
            self.delete_gift_cards()
        else:
            self.clear_gift_cards()

        self.delete_orders()

        if should_delete_customers:
            self.delete_customers()

    def delete_checkouts(self):
        checkout_lines = CheckoutLine.objects.all()
        checkout_lines._raw_delete(checkout_lines.db)

        checkout = Checkout.objects.all()
        checkout._raw_delete(checkout.db)
        self.stdout.write("Removed checkouts")

    def delete_payments(self):
        transaction = Transaction.objects.all()
        transaction._raw_delete(transaction.db)
        self.stdout.write("Removed transactions")

        payments = Payment.objects.all()
        payments._raw_delete(payments.db)
        self.stdout.write("Removed payments")
    
    def delete_invoices(self):
        invoice_events = InvoiceEvent.objects.all()
        invoice_events._raw_delete(invoice_events.db)

        invoice = Invoice.objects.all()
        invoice._raw_delete(invoice.db)
        self.stdout.write("Removed invoices")

    def delete_gift_cards(self):
        GiftCard.objects.all().delete()
        GiftCardTag.objects.all().delete()
        self.stdout.write("Removed gift cards")

    def clear_gift_cards(self):
        GiftCard.objects.all().update(fulfillment_line=None)
        GiftCardEvent.objects.all().update(order=None)

    def delete_orders(self):
        fulfillment_lines = FulfillmentLine.objects.all()
        fulfillment_lines._raw_delete(fulfillment_lines.db)

        fulfillments = Fulfillment.objects.all()
        fulfillments._raw_delete(fulfillments.db)

        allocations = Allocation.objects.all()
        allocations._raw_delete(allocations.db)

        order_lines = OrderLine.objects.all()
        order_lines._raw_delete(order_lines.db)

        order_events = OrderEvent.objects.all()
        order_events._raw_delete(order_events.db)

        customer_order_events = CustomerEvent.objects.filter(order__isnull=False)
        customer_order_events._raw_delete(customer_order_events.db)

        orders = Order.objects.all()
        orders._raw_delete(orders.db)
        self.stdout.write("Removed orders")

    def delete_customers(self):
        customers = User.objects.filter(is_staff=False, is_superuser=False)
        for user in customers:
            user.addresses.all().delete()
            user.delete()
        self.stdout.write("Removed customers")
