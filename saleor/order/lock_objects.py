from .models import Order, OrderLine


def order_lines_qs_select_for_update():
    return OrderLine.objects.order_by("pk").select_for_update(of=["self"])


def order_qs_select_for_update():
    return Order.objects.order_by("pk").select_for_update(of=["self"])
