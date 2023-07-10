import django_filters

from ..core.descriptions import ADDED_IN_38
from ..core.doc_category import DOC_CATEGORY_PAYMENTS
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
        doc_category = DOC_CATEGORY_PAYMENTS
        filterset_class = PaymentFilter
