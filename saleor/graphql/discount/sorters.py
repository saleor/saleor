import graphene
from django.db.models import Min, Q, QuerySet

from ...channel.models import Channel
from ..core.types import SortInputObjectType


class SaleSortField(graphene.Enum):
    NAME = ["name", "pk"]
    START_DATE = ["start_date", "name", "pk"]
    END_DATE = ["end_date", "name", "pk"]
    VALUE = ["value", "name", "pk"]
    TYPE = ["type", "name", "pk"]

    @property
    def description(self):
        if self.name in SaleSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort sales by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class SaleSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = SaleSortField
        type_name = "sales"


class VoucherSortField(graphene.Enum):
    CODE = ["code"]
    START_DATE = ["start_date", "name", "code"]
    END_DATE = ["end_date", "name", "code"]
    VALUE = ["discount_value", "name", "code"]
    TYPE = ["type", "name", "code"]
    USAGE_LIMIT = ["usage_limit", "name", "code"]
    MINIMUM_SPENT_AMOUNT = ["min_spent_amount", "name", "code"]

    @property
    def description(self):
        if self.name in VoucherSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort vouchers by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_minimum_spent_amount(queryset: QuerySet, channel: Channel) -> QuerySet:
        return queryset.annotate(
            min_spent_amount=Min(
                "channel_listing__min_spent_amount",
                filter=Q(channel_listing__channel=channel),
            )
        )

    @staticmethod
    def qs_with_value(queryset: QuerySet, channel: Channel) -> QuerySet:
        return queryset.annotate(
            discount_value=Min(
                "channel_listing__discount_value",
                filter=Q(channel_listing__channel=channel),
            )
        )


class VoucherSortingInput(SortInputObjectType):
    # TODO: Add description
    # TODO: Maybe move to SortInputObjectType
    channel = graphene.Argument(graphene.String)

    class Meta:
        sort_enum = VoucherSortField
        type_name = "vouchers"
