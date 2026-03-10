import django_filters

from ...inventory.models import PurchaseOrder


class PurchaseOrderFilter(django_filters.FilterSet):
    class Meta:
        model = PurchaseOrder
        fields = ["status"]
