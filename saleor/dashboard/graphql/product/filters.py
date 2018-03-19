from django_filters import OrderingFilter

from ....graphql.core.filters import DistinctFilterSet
from ....product.models import Product
from ...product.filters import PRODUCT_SORT_BY_FIELDS


class ProductFilter(DistinctFilterSet):
    sort_by = OrderingFilter(
        fields=PRODUCT_SORT_BY_FIELDS.keys(),
        field_labels=PRODUCT_SORT_BY_FIELDS)

    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'product_type__name': ['exact'],
            'price': ['exact', 'range', 'lte', 'gte'],
            'is_published': ['exact'],
            'is_featured': ['exact'],
        }
