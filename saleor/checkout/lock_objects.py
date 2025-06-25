from django.db.models import QuerySet

from .models import Checkout, CheckoutLine


def checkout_qs_select_for_update() -> QuerySet[Checkout]:
    return Checkout.objects.order_by("pk").select_for_update(of=(["self"]))


def checkout_lines_qs_select_for_update() -> QuerySet[CheckoutLine]:
    return CheckoutLine.objects.order_by("pk").select_for_update(of=(["self"]))
