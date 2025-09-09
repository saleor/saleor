import django_filters

from ..core.doc_category import DOC_CATEGORY_PAYMENTS
from ..core.filters import FilterInputObjectType, GlobalIDMultipleChoiceFilter
from ..directives import doc
from .types import Payment


class PaymentFilter(django_filters.FilterSet):
    ids = GlobalIDMultipleChoiceFilter(field_name="id", help_text="Filter by ids.")
    checkouts = GlobalIDMultipleChoiceFilter(field_name="checkout")

    class Meta:
        model = Payment
        fields = []


@doc(category=DOC_CATEGORY_PAYMENTS)
class PaymentFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = PaymentFilter
