from django.db.models import QuerySet

from .models import Voucher


def voucher_qs_select_for_update() -> QuerySet[Voucher]:
    return Voucher.objects.order_by("pk").select_for_update(of=["self"])
