import django_filters
import graphene
from django.db.models import Exists, OuterRef, Q

from ...payment.models import TransactionEvent
from ..core.descriptions import ADDED_IN_323
from ..core.doc_category import DOC_CATEGORY_PAYMENTS
from ..core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeWhereFilter,
    ObjectTypeWhereFilter,
    OperationObjectTypeWhereFilter,
    WhereFilterSet,
)
from ..core.filters.where_input import (
    FilterInputDescriptions,
    StringFilterInput,
    WhereInputObjectType,
)
from ..core.types.base import BaseInputObjectType
from ..core.types.common import DateTimeRangeInput
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_where_by_range_field, filter_where_by_value_field
from .enums import TransactionEventTypeEnum
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


class TransactionEventTypeEnumFilterInput(BaseInputObjectType):
    eq = TransactionEventTypeEnum(
        description=FilterInputDescriptions.EQ, required=False
    )
    one_of = graphene.List(
        graphene.NonNull(TransactionEventTypeEnum),
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS


class TransactionEventFilterInput(BaseInputObjectType):
    created_at = DateTimeRangeInput(
        description="Filter transaction events by created at date." + ADDED_IN_323,
    )
    type = TransactionEventTypeEnumFilterInput(
        description="Filter transaction events by type." + ADDED_IN_323,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAYMENTS
        description = "Filter input for transaction events data." + ADDED_IN_323


def filter_transaction_by_ids(qs, _, value):
    """Filter TransactionItem by global IDs."""
    _, tokens = resolve_global_ids_to_primary_keys(value, "TransactionItem")
    return qs.filter(token__in=tokens)


def filter_where_created_at_range(qs, _, value):
    return filter_where_by_range_field(qs, "created_at", value)


def filter_where_modified_at_range(qs, _, value):
    return filter_where_by_range_field(qs, "modified_at", value)


def filter_where_transaction_events(qs, _, value: list | None):
    if not value:
        return qs.none()

    lookup = Q()
    for input_data in value:
        if not {"created_at", "type"}.intersection(input_data.keys()):
            return qs.none()

        event_qs = None
        if filter_value := input_data.get("created_at"):
            event_qs = filter_where_by_range_field(
                TransactionEvent.objects.using(qs.db), "created_at", filter_value
            )
        if filter_value := input_data.get("type"):
            event_qs = filter_where_by_value_field(
                event_qs or TransactionEvent.objects.using(qs.db),
                "type",
                filter_value,
            )
        if event_qs is not None:
            lookup &= Q(Exists(event_qs.filter(transaction_id=OuterRef("id"))))
    if lookup:
        return qs.filter(lookup)
    return qs.none()


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
    created_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method=filter_where_created_at_range,
        help_text="Filter transactions by created at date." + ADDED_IN_323,
    )
    modified_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method=filter_where_modified_at_range,
        help_text="Filter transactions by modified at date." + ADDED_IN_323,
    )
    events = ListObjectTypeWhereFilter(
        input_class=TransactionEventFilterInput,
        method=filter_where_transaction_events,
        help_text=(
            "Filter by transaction events. "
            "Each list item represents conditions that must be satisfied by a single "
            "event. The filter matches transactions that have related events "
            "meeting all specified groups of conditions."
        )
        + ADDED_IN_323,
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
