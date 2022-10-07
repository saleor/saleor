import django_filters

from ..core.descriptions import ADDED_IN_38
from ..core.filters import GlobalIDMultipleChoiceFilter
from ..core.types import FilterInputObjectType
from .types import Payment


class PaymentFilter(django_filters.FilterSet):
    ids = GlobalIDMultipleChoiceFilter(
        field_name="id", help_text=f"Filter by ids. {ADDED_IN_38}"
    )
    checkouts = GlobalIDMultipleChoiceFilter(field_name="checkout")

    class Meta:
        model = Payment
        fields = []


class PaymentFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PaymentFilter
