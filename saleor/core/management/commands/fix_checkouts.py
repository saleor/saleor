from django.core.management.base import BaseCommand

from ....order import OrderStatus
from ....order.models import Order


class Command(BaseCommand):
    help = (
        "Find all orders in cancelled state. "
        "Changed their checkout_token to empty string (like DB default)."
    )

    def handle(self, *args, **options):
        Order.objects.filter(status=OrderStatus.CANCELED).update(checkout_token="")
