import django_filters

from ..core.doc_category import DOC_CATEGORY_PAYMENTS
from ..core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    OperationObjectTypeWhereFilter,
    WhereFilterSet,
)
from ..core.filters.where_input import StringFilterInput, WhereInputObjectType
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_where_by_value_field
from .types import Payment


class PaymentFilter(django_filters.FilterSet):
    ids = GlobalIDMultipleChoiceFilter(field_name="id", help_text="Filter by ids.")
    checkouts = GlobalIDMultipleChoiceFilter(field_name="checkout")

    class Meta:
        model = Payment
        fields = []


class PaymentFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        filterset_class = PaymentFilter


def filter_transaction_by_ids(qs, _, value):
    """Filter TransactionItem by global IDs."""
    _, tokens = resolve_global_ids_to_primary_keys(value, "TransactionItem")
    return qs.filter(token__in=tokens)


class TransactionWhere(WhereFilterSet):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_transaction_by_ids)
    psp_reference = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_psp_reference",
        help_text="Filter by PSP reference.",
    )
    app_identifier = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_app_identifier",
        help_text="Filter by app identifier.",
    )

    @staticmethod
    def filter_psp_reference(qs, _, value):
        return filter_where_by_value_field(qs, "psp_reference", value)

    @staticmethod
    def filter_app_identifier(qs, _, value):
        return filter_where_by_value_field(qs, "app_identifier", value)

    class Meta:
        abstract = True


class TransactionWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        filterset_class = TransactionWhere
