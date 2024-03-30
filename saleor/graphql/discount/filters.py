import decimal

import django_filters
from django.db.models import Exists, OuterRef, Q, Sum
from django.utils import timezone

from ...discount import DiscountValueType
from ...discount.models import (
    Promotion,
    PromotionRule,
    Voucher,
    VoucherCode,
    VoucherQueryset,
)
from ..core.doc_category import DOC_CATEGORY_DISCOUNTS
from ..core.filters import (
    BooleanWhereFilter,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    MetadataWhereFilterBase,
    ObjectTypeFilter,
    ObjectTypeWhereFilter,
    OperationObjectTypeWhereFilter,
    WhereFilterSet,
)
from ..core.types import (
    BaseInputObjectType,
    DateTimeFilterInput,
    DateTimeRangeInput,
    IntRangeInput,
    NonNullList,
    StringFilterInput,
)
from ..core.types.filter_input import (
    DecimalFilterInput,
    FilterInputDescriptions,
    WhereInputObjectType,
)
from ..utils.filters import (
    filter_by_id,
    filter_by_ids,
    filter_range_field,
    filter_where_by_string_field,
    filter_where_range_field,
)
from .enums import (
    DiscountStatusEnum,
    DiscountValueTypeEnum,
    PromotionTypeEnum,
    VoucherDiscountType,
)


def filter_status(
    qs: VoucherQueryset, _, value: list[DiscountStatusEnum]
) -> VoucherQueryset:
    if not value:
        return qs
    query_objects = qs.none()
    now = timezone.now()
    if DiscountStatusEnum.ACTIVE in value:
        query_objects |= qs.active(now)
    if DiscountStatusEnum.EXPIRED in value:
        query_objects |= qs.expired(now)
    if DiscountStatusEnum.SCHEDULED in value:
        query_objects |= qs.filter(start_date__gt=now)
    return qs & query_objects


def filter_times_used(qs, _, value):
    qs = qs.annotate(used=Sum("codes__used"))
    return filter_range_field(qs, "used", value)


def filter_discount_type(
    qs: VoucherQueryset, _, values: list[VoucherDiscountType]
) -> VoucherQueryset:
    if values:
        query = Q()
        if VoucherDiscountType.FIXED in values:
            query |= Q(
                discount_value_type=VoucherDiscountType.FIXED.value  # type: ignore[attr-defined] # mypy does not understand graphene enums # noqa: E501
            )
        if VoucherDiscountType.PERCENTAGE in values:
            query |= Q(
                discount_value_type=VoucherDiscountType.PERCENTAGE.value  # type: ignore[attr-defined] # mypy does not understand graphene enums # noqa: E501
            )
        if VoucherDiscountType.SHIPPING in values:
            query |= Q(type=VoucherDiscountType.SHIPPING.value)  # type: ignore[attr-defined] # mypy does not understand graphene enums # noqa: E501
        qs = qs.filter(query)
    return qs


def filter_started(qs, _, value):
    return filter_range_field(qs, "start_date", value)


def filter_sale_type(qs, _, value):
    if value in [DiscountValueType.FIXED, DiscountValueType.PERCENTAGE]:
        rules = PromotionRule.objects.using(qs.db).filter(reward_value_type=value)
        qs = qs.filter(Exists(rules.filter(promotion_id=OuterRef("pk"))))
    return qs


def filter_sale_search(qs, _, value):
    try:
        value = decimal.Decimal(value)
    except decimal.DecimalException:
        return qs.filter(
            Q(name__ilike=value) | Q(rules__reward_value_type__ilike=value)
        )
    rules = PromotionRule.objects.using(qs.db).filter(reward_value=value)
    return qs.filter(Exists(rules.filter(promotion_id=OuterRef("pk"))))


def filter_voucher_search(qs, _, value):
    return qs.filter(
        Q(name__ilike=value)
        | Q(
            Exists(
                VoucherCode.objects.using(qs.db).filter(
                    code__ilike=value, voucher_id=OuterRef("pk")
                )
            )
        )
    )


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at", value)


class VoucherFilter(MetadataFilterBase):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    times_used = ObjectTypeFilter(input_class=IntRangeInput, method=filter_times_used)

    discount_type = ListObjectTypeFilter(
        input_class=VoucherDiscountType, method=filter_discount_type
    )
    started = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_started)
    search = django_filters.CharFilter(method=filter_voucher_search)
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id("Voucher"))

    class Meta:
        model = Voucher
        fields = ["status", "times_used", "discount_type", "started", "search"]


class SaleFilter(MetadataFilterBase):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    sale_type = ObjectTypeFilter(
        input_class=DiscountValueTypeEnum, method=filter_sale_type
    )
    started = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_started)
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at_range
    )
    search = django_filters.CharFilter(method=filter_sale_search)

    class Meta:
        model = Promotion
        fields = ["status", "sale_type", "started", "search"]


class PromotionTypeEnumFilterInput(BaseInputObjectType):
    eq = PromotionTypeEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        PromotionTypeEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionWhere(MetadataWhereFilterBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Promotion"))
    name = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_promotion_name",
        help_text="Filter by promotion name.",
    )
    end_date = ObjectTypeWhereFilter(
        input_class=DateTimeFilterInput,
        method="filter_end_date_range",
        help_text="Filter promotions by end date.",
    )
    start_date = ObjectTypeWhereFilter(
        input_class=DateTimeFilterInput,
        method="filter_start_date_range",
        help_text="Filter promotions by start date.",
    )
    is_old_sale = BooleanWhereFilter(method="filter_is_old_sale")
    type = OperationObjectTypeWhereFilter(
        input_class=PromotionTypeEnumFilterInput, method="filter_type"
    )

    @staticmethod
    def filter_promotion_name(qs, _, value):
        return filter_where_by_string_field(qs, "name", value)

    @staticmethod
    def filter_end_date_range(qs, _, value):
        return filter_where_range_field(qs, "end_date", value)

    @staticmethod
    def filter_start_date_range(qs, _, value):
        return filter_where_range_field(qs, "start_date", value)

    @staticmethod
    def filter_is_old_sale(qs, _, value):
        return qs.exclude(old_sale_id__isnull=value)

    @staticmethod
    def filter_type(qs, _, value):
        return filter_where_by_string_field(qs, "type", value)


class PromotionWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        filterset_class = PromotionWhere


class DiscountedObjectWhere(WhereFilterSet):
    base_subtotal_price = OperationObjectTypeWhereFilter(
        input_class=DecimalFilterInput,
        method="filter_base_subtotal_price",
        help_text="Filter by the base subtotal price.",
    )
    base_total_price = OperationObjectTypeWhereFilter(
        input_class=DecimalFilterInput,
        method="filter_base_total_price",
        help_text="Filter by the base total price.",
    )

    class Meta:
        abstract = True


class DiscountedObjectWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        filterset_class = DiscountedObjectWhere
