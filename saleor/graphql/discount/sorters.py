import graphene
from django.db.models import F, Min, OuterRef, Q, QuerySet, Subquery

from ...discount.models import VoucherCode
from ..core.descriptions import (
    ADDED_IN_318,
    CHANNEL_REQUIRED,
    DEFAULT_DEPRECATION_REASON,
)
from ..core.doc_category import DOC_CATEGORY_DISCOUNTS
from ..core.types import BaseEnum, ChannelSortInputObjectType, SortInputObjectType


class SaleSortField(BaseEnum):
    NAME = ["name", "pk"]
    START_DATE = ["start_date", "name", "pk"]
    END_DATE = ["end_date", "name", "pk"]
    VALUE = ["value", "name", "pk"]
    TYPE = ["value_type", "name", "pk"]
    CREATED_AT = ["created_at", "name", "pk"]
    LAST_MODIFIED_AT = ["updated_at", "name", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS

    @property
    def description(self):
        descriptions = {
            SaleSortField.NAME.name: "name.",  # type: ignore[attr-defined] # noqa: E501
            SaleSortField.START_DATE.name: "start date.",  # type: ignore[attr-defined] # noqa: E501
            SaleSortField.END_DATE.name: "end date.",  # type: ignore[attr-defined] # noqa: E501
            SaleSortField.VALUE.name: "value." + CHANNEL_REQUIRED,  # type: ignore[attr-defined] # noqa: E501
            SaleSortField.TYPE.name: "type.",  # type: ignore[attr-defined] # noqa: E501
            SaleSortField.CREATED_AT.name: "creation date.",  # type: ignore[attr-defined] # noqa: E501
            SaleSortField.LAST_MODIFIED_AT.name: "last modification date.",  # type: ignore[attr-defined] # noqa: E501
        }
        if self.name in descriptions:
            return f"Sort sales by {descriptions[self.name]}"
        raise ValueError(f"Unsupported enum value: {self.value}")

    @staticmethod
    def qs_with_value(queryset: QuerySet, channel_slug: str) -> QuerySet:
        return queryset.annotate(
            value=Min(
                "rules__reward_value",
                filter=Q(rules__channels__slug=str(channel_slug)),
            )
        )

    @staticmethod
    def qs_with_type(queryset: QuerySet, **kwargs) -> QuerySet:
        return queryset.annotate(value_type=F("rules__reward_value_type"))


class SaleSortingInput(ChannelSortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        sort_enum = SaleSortField
        type_name = "sales"


class VoucherSortField(graphene.Enum):
    CODE = ["first_code", "pk"]
    NAME = ["name", "pk"]
    START_DATE = ["start_date", "name", "pk"]
    END_DATE = ["end_date", "name", "pk"]
    VALUE = ["discount_value", "name", "pk"]
    TYPE = ["type", "name", "pk"]
    USAGE_LIMIT = ["usage_limit", "name", "pk"]
    MINIMUM_SPENT_AMOUNT = ["min_spent_amount", "name", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS

    @property
    def description(self):
        descrption_extras = {
            VoucherSortField.VALUE.name: [CHANNEL_REQUIRED],  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            VoucherSortField.MINIMUM_SPENT_AMOUNT.name: [CHANNEL_REQUIRED],  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            VoucherSortField.NAME.name: [ADDED_IN_318],  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in VoucherSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            description = f"Sort vouchers by {sort_name}."
            if extras := descrption_extras.get(self.name):
                description += "".join(extras)
            return description
        raise ValueError(f"Unsupported enum value: {self.value}")

    @property
    def deprecation_reason(self):
        deprecations = {
            VoucherSortField.CODE.name: DEFAULT_DEPRECATION_REASON,  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in deprecations:
            return deprecations[self.name]
        return None

    @staticmethod
    def qs_with_minimum_spent_amount(queryset: QuerySet, channel_slug: str) -> QuerySet:
        return queryset.annotate(
            min_spent_amount=Min(
                "channel_listings__min_spent_amount",
                filter=Q(channel_listings__channel__slug=str(channel_slug)),
            )
        )

    @staticmethod
    def qs_with_value(queryset: QuerySet, channel_slug: str) -> QuerySet:
        return queryset.annotate(
            discount_value=Min(
                "channel_listings__discount_value",
                filter=Q(channel_listings__channel__slug=str(channel_slug)),
            )
        )

    @staticmethod
    def qs_with_code(queryset: QuerySet, channel_slug: str) -> QuerySet:
        # Added to keep compatibility with old API. Workaround for
        # https://docs.saleor.io/docs/3.x/developer/community/contributing#sorting-and-filtering

        subquery = VoucherCode.objects.filter(voucher_id=OuterRef("pk")).values("code")[
            :1
        ]

        return queryset.annotate(first_code=Subquery(subquery))


class VoucherSortingInput(ChannelSortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        sort_enum = VoucherSortField
        type_name = "vouchers"


class PromotionSortField(BaseEnum):
    NAME = ["name", "pk"]
    START_DATE = ["start_date", "name", "pk"]
    END_DATE = ["end_date", "name", "pk"]
    CREATED_AT = ["created_at", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS

    @property
    def description(self):
        descriptions = {
            PromotionSortField.NAME.name: "name.",  # type: ignore[attr-defined] # noqa: E501
            PromotionSortField.START_DATE.name: "start date.",  # type: ignore[attr-defined] # noqa: E501
            PromotionSortField.END_DATE.name: "end date.",  # type: ignore[attr-defined] # noqa: E501
            PromotionSortField.CREATED_AT.name: "creation date.",  # type: ignore[attr-defined] # noqa: E501
        }
        if self.name in descriptions:
            return f"Sort promotions by {descriptions[self.name]}"
        raise ValueError(f"Unsupported enum value: {self.value}")


class PromotionSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        sort_enum = PromotionSortField
        type_name = "promotions"
