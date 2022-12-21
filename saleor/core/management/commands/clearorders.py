"""Clear the transactions data preserving shop's catalog and configuration.

This command clears the database from data such as orders, checkouts, payments and
optionally customer accounts. It doesn't remove shop's catalog (products, variants) nor
configuration, such as: warehouses, shipping zones, staff accounts, plugin config etc.
"""

from django.core.management.base import BaseCommand

from ....account.models import Address, CustomerEvent, CustomerNote, User
from ....checkout.models import Checkout, CheckoutLine, CheckoutMetadata
from ....giftcard.models import GiftCard, GiftCardEvent, GiftCardTag
from ....invoice.models import Invoice, InvoiceEvent
from ....order.models import Fulfillment, FulfillmentLine, Order, OrderEvent, OrderLine
from ....payment.models import Payment, Transaction, TransactionEvent, TransactionItem
from ....warehouse.models import Allocation


class Command(BaseCommand):
    help = "Removes transactions data preserving shop's catalog and configuration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-customers",
            action="store_true",
            help="Delete cutomers user accounts (doesn't delete staff accounts).",
        )

    def handle(self, **options):
        self.delete_checkouts()
        self.delete_payments()
        self.delete_invoices()
        self.delete_gift_cards()
        self.delete_orders()

        should_delete_customers = options.get("delete_customers")
        if should_delete_customers:
            self.delete_customers()

    def delete_checkouts(self):
        metadata = CheckoutMetadata.objects.all()
        metadata._raw_delete(metadata.db)

        checkout_lines = CheckoutLine.objects.all()
        checkout_lines._raw_delete(checkout_lines.db)

        checkout = Checkout.objects.all()
        checkout._raw_delete(checkout.db)
        self.stdout.write("Removed checkouts")

    def delete_payments(self):
        transaction_events = TransactionEvent.objects.all()
        transaction_events._raw_delete(transaction_events.db)

        transaction_items = TransactionItem.objects.all()
        transaction_items._raw_delete(transaction_items.db)

        transactions = Transaction.objects.all()
        transactions._raw_delete(transactions.db)

        payments = Payment.objects.all()
        payments._raw_delete(payments.db)
        self.stdout.write("Removed payments and trnsactions")

    def delete_invoices(self):
        invoice_events = InvoiceEvent.objects.all()
        invoice_events._raw_delete(invoice_events.db)

        invoice = Invoice.objects.all()
        invoice._raw_delete(invoice.db)
        self.stdout.write("Removed invoices")

    def delete_gift_cards(self):
        gift_card_events = GiftCardEvent.objects.all()
        gift_card_events._raw_delete(gift_card_events.db)

        gift_card_tags = GiftCardTag.objects.all()
        gift_card_tags.delete()

        gift_cards = GiftCard.objects.all()
        gift_cards._raw_delete(gift_cards.db)
        self.stdout.write("Removed gift cards")

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

        customer_addresses = Address.objects.filter(user_addresses__in=customers)
        customer_events = CustomerEvent.objects.all()
        customer_notes = CustomerNote.objects.all()

        customer_addresses.delete()
        customer_events._raw_delete(customer_events.db)
        customer_notes._raw_delete(customer_notes.db)

        customers._raw_delete(customers.db)
        self.stdout.write("Removed customers")
