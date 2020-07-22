from babel.numbers import UnknownCurrencyError, validate_currency
from django.core.management.base import BaseCommand, CommandError

from ....checkout.models import Checkout
from ....discount.models import Voucher
from ....giftcard.models import GiftCard
from ....order.models import Order, OrderLine
from ....payment.models import Payment, Transaction
from ....product.models import Product, ProductVariant
from ....shipping.models import ShippingMethod


class Command(BaseCommand):
    help = (
        "Change currency in all models in the database. "
        "Note, that this command only changes currency code "
        "without doing any conversion. "
        "Currency set by this command must match "
        "with the value set in DEFAULT_CURRENCY environment variable."
    )

    def add_arguments(self, parser):
        parser.add_argument("currency", type=str)

        parser.add_argument(
            "--force",
            action="store_true",
            help="Allows running command without validation.",
        )

    def handle(self, **options):
        force = options.get("force", False)
        currency = options["currency"]

        if not force:
            try:
                validate_currency(currency)
            except UnknownCurrencyError:
                raise CommandError(
                    "Unknown currency. "
                    "Use `--force` flag to force migration currencies."
                )

        Checkout.objects.update(currency=currency)
        Voucher.objects.update(currency=currency)
        GiftCard.objects.update(currency=currency)
        Order.objects.update(currency=currency)
        OrderLine.objects.update(currency=currency)
        Payment.objects.update(currency=currency)
        Transaction.objects.update(currency=currency)
        Product.objects.update(currency=currency)
        ProductVariant.objects.update(currency=currency)
        ShippingMethod.objects.update(currency=currency)
