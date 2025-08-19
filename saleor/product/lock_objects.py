from django.db.models import QuerySet

from .models import Product


def product_qs_select_for_update() -> QuerySet[Product]:
    return Product.objects.order_by("pk").select_for_update(of=(["self"]))
