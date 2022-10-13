import django_filters

from ..core.filters import GlobalIDMultipleChoiceFilter
from ..core.types import FilterInputObjectType
from .types import Payment


class PaymentFilter(django_filters.FilterSet):
    checkouts = GlobalIDMultipleChoiceFilter(field_name="checkout")

    class Meta:
        model = Payment
        fields = []


class PaymentFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PaymentFilter
