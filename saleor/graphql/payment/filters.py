import django_filters

from ..core.types import FilterInputObjectType
from ..django.filters import GlobalIDMultipleChoiceFilter
from .types import Payment


class PaymentFilter(django_filters.FilterSet):
    checkouts = GlobalIDMultipleChoiceFilter(field_name="checkout")

    class Meta:
        model = Payment
        fields = []


class PaymentFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PaymentFilter
