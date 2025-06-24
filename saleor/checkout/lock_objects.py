from .models import Checkout, CheckoutLine


def checkout_qs_select_for_update():
    return Checkout.objects.order_by("pk").select_for_update(of=(["self"]))


def checkout_lines_qs_select_for_update():
    return CheckoutLine.objects.order_by("id").select_for_update(of=(["self"]))
