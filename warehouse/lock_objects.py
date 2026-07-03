from .models import Allocation, Stock


def stock_select_for_update_for_existing_qs(qs):
    return qs.order_by("pk").select_for_update(of=(["self"]))


def stock_qs_select_for_update():
    return stock_select_for_update_for_existing_qs(Stock.objects.all())


def allocation_with_stock_qs_select_for_update():
    return (
        Allocation.objects.select_related("stock")
        .select_for_update(
            of=(
                "self",
                "stock",
            )
        )
        .order_by("stock__pk")
    )
