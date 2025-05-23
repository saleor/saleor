from uuid import UUID

import django_filters
import graphene
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Exists, OuterRef, Q, Value
from django.utils import timezone
from graphql.error import GraphQLError

from ...core.postgres import FlatConcat
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCardEvent
from ...order.models import Order, OrderLine
from ...order.search import search_orders
from ...payment import ChargeStatus
from ...payment.models import Payment
from ...product.models import ProductVariant
from ..channel.filters import get_currency_from_filter_data
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.filters import (
    BooleanWhereFilter,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
    ObjectTypeWhereFilter,
    OperationObjectTypeWhereFilter,
    WhereFilterSet,
)
from ..core.scalars import UUID as UUIDScalar
from ..core.types import (
    BaseInputObjectType,
    DateRangeInput,
    DateTimeRangeInput,
    NonNullList,
)
from ..core.types.filter_input import (
    DateTimeFilterInput,
    FilterInputDescriptions,
    GlobalIDFilterInput,
    IntFilterInput,
    StringFilterInput,
    UUIDFilterInput,
    WhereInputObjectType,
)
from ..core.utils import from_global_id_or_error
from ..discount.filters import DiscountedObjectWhere
from ..payment.enums import PaymentChargeStatusEnum
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import (
    filter_by_ids,
    filter_range_field,
    filter_where_by_id_field,
    filter_where_by_numeric_field,
    filter_where_by_value_field,
    filter_where_range_field,
)
from .enums import (
    OrderAuthorizeStatusEnum,
    OrderChargeStatusEnum,
    OrderStatusEnum,
    OrderStatusFilter,
)


def filter_payment_status(qs, _, value):
    if value:
        lookup = Q(payments__is_active=True, payments__charge_status__in=value)
        if ChargeStatus.FULLY_REFUNDED in value:
            lookup |= Q(payments__charge_status=ChargeStatus.FULLY_REFUNDED)
        qs = qs.filter(lookup)
    return qs


def filter_authorize_status(qs, _, value):
    if value:
        qs = qs.filter(authorize_status__in=value)
    return qs


def filter_charge_status(qs, _, value):
    if value:
        qs = qs.filter(charge_status__in=value)
    return qs


def get_payment_id_from_query(value):
    try:
        return from_global_id_or_error(value, only_type="Payment")[1]
    except Exception:
        return None


def filter_order_by_payment(qs, payment_id):
    if payment_id:
        qs = qs.filter(payments__pk=payment_id)
    return qs


def filter_status(qs, _, value):
    query_objects = qs.none()

    if value:
        query_objects |= qs.filter(status__in=value)

    if OrderStatusFilter.READY_TO_FULFILL in value:
        query_objects |= qs.ready_to_fulfill()

    if OrderStatusFilter.READY_TO_CAPTURE in value:
        query_objects |= qs.ready_to_capture()

    return qs & query_objects


def _filter_customer_by_email_first_or_last_name(qs, value):
    return qs.filter(
        Q(user_email__ilike=value)
        | Q(user__email__ilike=value)
        | Q(user__first_name__ilike=value)
        | Q(user__last_name__ilike=value)
    )


def _filter_by_customer_full_name(qs, value):
    try:
        first, last = value.split(" ", 1)
    except ValueError:
        qs = _filter_customer_by_email_first_or_last_name(qs, value)
    else:
        qs = qs.alias(
            user_full_name=FlatConcat(
                "user__first_name",
                Value(" "),
                "user__last_name",
            )
        ).filter(
            Q(user_full_name__iexact=value)
            | Q(user_full_name__iexact=f"{last} {first}")
        )

    return qs


def filter_customer(qs, _, value):
    try:
        validate_email(value)
    except ValidationError:
        qs = _filter_by_customer_full_name(qs, value)
    else:
        qs = qs.filter(Q(user_email__iexact=value) | Q(user__email__iexact=value))

    return qs


def filter_created_range(qs, _, value):
    return filter_range_field(qs, "created_at__date", value)


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at", value)


def filter_order_search(qs, _, value):
    return search_orders(qs, value)


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, "Channel")
        qs = qs.filter(channel_id__in=channels_ids)
    return qs


def filter_checkouts(qs, _, values):
    if values:
        _, checkout_ids = resolve_global_ids_to_primary_keys(values, "Checkout")
        qs = qs.filter(checkout_token__in=checkout_ids)
    return qs


def filter_is_click_and_collect(qs, _, values):
    if values is not None:
        lookup = Q(collection_point__isnull=False) | Q(
            collection_point_name__isnull=False
        )
        qs = qs.filter(lookup) if values is True else qs.exclude(lookup)
    return qs


def filter_is_preorder(qs, _, values):
    if values is not None:
        variants = (
            ProductVariant.objects.using(qs.db)
            .filter(
                Q(is_preorder=True)
                & (
                    Q(preorder_end_date__isnull=True)
                    | Q(preorder_end_date__gte=timezone.now())
                )
            )
            .values("id")
        )
        lines = OrderLine.objects.using(qs.db).filter(
            Exists(variants.filter(id=OuterRef("variant_id")))
        )
        lookup = Exists(lines.filter(order_id=OuterRef("id")))
        qs = qs.filter(lookup) if values is True else qs.exclude(lookup)
    return qs


def filter_gift_card_used(qs, _, value):
    return filter_by_gift_card(qs, value, GiftCardEvents.USED_IN_ORDER)


def filter_gift_card_bought(qs, _, value):
    return filter_by_gift_card(qs, value, GiftCardEvents.BOUGHT)


def filter_by_gift_card(qs, value, gift_card_type):
    gift_card_events = (
        GiftCardEvent.objects.using(qs.db)
        .filter(type=gift_card_type)
        .values("order_id")
    )
    lookup = Exists(gift_card_events.filter(order_id=OuterRef("id")))
    return qs.filter(lookup) if value is True else qs.exclude(lookup)


def filter_order_by_id(qs, _, value):
    if not value:
        return qs
    _, obj_pks = resolve_global_ids_to_primary_keys(value, "Order")
    pks = []
    old_pks = []
    for pk in obj_pks:
        try:
            pks.append(UUID(pk))
        except ValueError:
            old_pks.append(pk)
    return qs.filter(Q(id__in=pks) | (Q(use_old_id=True) & Q(number__in=old_pks)))


def filter_by_order_number(qs, _, values):
    if not values:
        return qs
    return qs.filter(number__in=values)


def filter_by_checkout_tokens(qs, _, values):
    if not values:
        return qs
    return qs.filter(checkout_token__in=values)


class DraftOrderFilter(MetadataFilterBase):
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    search = django_filters.CharFilter(method=filter_order_search)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)

    class Meta:
        model = Order
        fields = ["customer", "created", "search"]


class OrderFilter(DraftOrderFilter):
    payment_status = ListObjectTypeFilter(
        input_class=PaymentChargeStatusEnum, method=filter_payment_status
    )
    authorize_status = ListObjectTypeFilter(
        input_class=OrderAuthorizeStatusEnum, method=filter_authorize_status
    )
    charge_status = ListObjectTypeFilter(
        input_class=OrderChargeStatusEnum, method=filter_charge_status
    )
    status = ListObjectTypeFilter(input_class=OrderStatusFilter, method=filter_status)
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at_range
    )
    search = django_filters.CharFilter(method=filter_order_search)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)
    is_click_and_collect = django_filters.BooleanFilter(
        method=filter_is_click_and_collect
    )
    is_preorder = django_filters.BooleanFilter(method=filter_is_preorder)
    ids = GlobalIDMultipleChoiceFilter(method=filter_order_by_id)
    checkout_tokens = ListObjectTypeFilter(
        input_class=UUIDScalar, method=filter_by_checkout_tokens
    )
    gift_card_used = django_filters.BooleanFilter(method=filter_gift_card_used)
    gift_card_bought = django_filters.BooleanFilter(method=filter_gift_card_bought)
    numbers = ListObjectTypeFilter(
        input_class=graphene.String, method=filter_by_order_number
    )
    checkout_ids = GlobalIDMultipleChoiceFilter(method=filter_checkouts)

    class Meta:
        model = Order
        fields = ["payment_status", "status", "customer", "created", "search"]

    def is_valid(self):
        if "ids" in self.data and "numbers" in self.data:
            raise GraphQLError(
                message="'ids' and 'numbers` are not allowed to use together in filter."
            )
        return super().is_valid()


class OrderStatusEnumFilterInput(BaseInputObjectType):
    eq = OrderStatusEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        OrderStatusEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter by order status."


class PaymentStatusEnumFilterInput(BaseInputObjectType):
    eq = PaymentChargeStatusEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        PaymentChargeStatusEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderAuthorizeStatusEnumFilterInput(BaseInputObjectType):
    eq = OrderAuthorizeStatusEnum(
        description=FilterInputDescriptions.EQ, required=False
    )
    one_of = NonNullList(
        OrderAuthorizeStatusEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter by authorize status."


class OrderChargeStatusEnumFilterInput(BaseInputObjectType):
    eq = OrderChargeStatusEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        OrderChargeStatusEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter by charge status."


# TODO: metadata filter will be added later
class OrderWhere(WhereFilterSet):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Order"))
    number = OperationObjectTypeWhereFilter(
        input_class=IntFilterInput,
        method="filter_number",
        help_text="Filter by order number.",
    )
    channel_id = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_channel_id",
        help_text="Filter by channel.",
    )
    created_at = ObjectTypeWhereFilter(
        input_class=DateTimeFilterInput,
        method="filter_created_at_range",
        help_text="Filter order by created at date.",
    )
    updated_at = ObjectTypeWhereFilter(
        input_class=DateTimeFilterInput,
        method="filter_updated_at_range",
        help_text="Filter order by updated at date.",
    )
    user = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_user",
        help_text="Filter by user.",
    )
    user_email = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_user_email",
        help_text="Filter by user email.",
    )
    payment_status = OperationObjectTypeWhereFilter(
        input_class=PaymentStatusEnumFilterInput,
        method="filter_payment_status",
        help_text="Filter by payment status.",
    )
    authorize_status = OperationObjectTypeWhereFilter(
        input_class=OrderAuthorizeStatusEnumFilterInput,
        method="filter_authorize_status",
        help_text="Filter by authorize status.",
    )
    charge_status = OperationObjectTypeWhereFilter(
        input_class=OrderChargeStatusEnumFilterInput,
        method="filter_charge_status",
        help_text="Filter by charge status.",
    )
    status = OperationObjectTypeWhereFilter(
        input_class=OrderStatusEnumFilterInput,
        method="filter_status",
        help_text="Filter by order status.",
    )
    checkout_token = OperationObjectTypeWhereFilter(
        UUIDFilterInput,
        method="filter_checkout_token",
        help_text="Filter by checkout token.",
    )
    checkout_id = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_checkout_id",
        help_text="Filter by checkout id.",
    )
    is_click_and_collect = BooleanWhereFilter(
        method="filter_is_click_and_collect",
        help_text="Filter by whether the order uses the click and collect delivery method.",
    )
    is_preorder = BooleanWhereFilter(
        method="filter_is_preorder",
        help_text="Filter by whether the order contains preorder items.",
    )
    is_gift_card_used = BooleanWhereFilter(
        method="filter_is_gift_card_used",
        help_text="Filter based on whether a gift card was used in the order.",
    )
    is_gift_card_bought = BooleanWhereFilter(
        method="filter_is_gift_card_bought",
        help_text="Filter based on whether the order includes a gift card purchase.",
    )

    @staticmethod
    def filter_number(qs, _, value):
        return filter_where_by_numeric_field(qs, "number", value)

    @staticmethod
    def filter_channel_id(qs, _, value):
        if not value:
            return qs
        return filter_where_by_id_field(qs, "channel", value, "Channel")

    @staticmethod
    def filter_created_at_range(qs, _, value):
        return filter_where_range_field(qs, "created_at", value)

    @staticmethod
    def filter_updated_at_range(qs, _, value):
        return filter_where_range_field(qs, "updated_at", value)

    @staticmethod
    def filter_user(qs, _, value):
        return filter_where_by_id_field(qs, "user", value, "User")

    @staticmethod
    def filter_user_email(qs, _, value):
        return filter_where_by_value_field(qs, "user_email", value)

    @staticmethod
    def filter_payment_status(qs, _, value):
        if value is None:
            return qs.none()

        eq_value = value.get("eq")
        values = value.get("one_of")
        if eq_value:
            values = [eq_value]

        if values:
            lookup = Q(is_active=True, charge_status__in=values)
            if ChargeStatus.FULLY_REFUNDED in values:
                lookup |= Q(charge_status=ChargeStatus.FULLY_REFUNDED)
            payments = Payment.objects.using(qs.db).filter(lookup)
            return qs.filter(Exists(payments.filter(order_id=OuterRef("id"))))
        return qs.none()

    @staticmethod
    def filter_authorize_status(qs, _, value):
        return filter_where_by_value_field(qs, "authorize_status", value)

    @staticmethod
    def filter_charge_status(qs, _, value):
        return filter_where_by_value_field(qs, "charge_status", value)

    @staticmethod
    def filter_status(qs, _, value):
        return filter_where_by_value_field(qs, "status", value)

    @staticmethod
    def filter_checkout_token(qs, _, value):
        return filter_where_by_value_field(qs, "checkout_token", value)

    @staticmethod
    def filter_checkout_id(qs, _, value):
        return filter_where_by_id_field(qs, "checkout_token", value, "Checkout")

    @staticmethod
    def filter_is_click_and_collect(qs, _, value):
        if value is None:
            return qs.none()
        return filter_is_click_and_collect(qs, _, value)

    @staticmethod
    def filter_is_preorder(qs, _, value):
        if value is None:
            return qs.none()
        return filter_is_preorder(qs, _, value)

    @staticmethod
    def filter_is_gift_card_used(qs, _, value):
        if value is None:
            return qs.none()
        return filter_by_gift_card(qs, value, GiftCardEvents.USED_IN_ORDER)

    @staticmethod
    def filter_is_gift_card_bought(qs, _, value):
        if value is None:
            return qs.none()
        return filter_by_gift_card(qs, value, GiftCardEvents.BOUGHT)


class OrderWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        filterset_class = OrderWhere


class OrderDiscountedObjectWhere(DiscountedObjectWhere):
    class Meta:
        model = Order
        fields = ["subtotal_net_amount", "total_net_amount"]

    def filter_base_subtotal_price(self, queryset, name, value):
        currency = get_currency_from_filter_data(self.data)
        return _filter_price(queryset, name, "subtotal_net_amount", value, currency)

    def filter_base_total_price(self, queryset, name, value):
        currency = get_currency_from_filter_data(self.data)
        return _filter_price(queryset, name, "total_net_amount", value, currency)


def _filter_price(qs, _, field_name, value, currency):
    # We will have single channel/currency as the rule can be applied only
    # on channels with the same currencies
    if not currency:
        raise ValidationError(
            "You must provide a currency to filter by price field.", code="required"
        )
    qs = qs.filter(currency=currency)
    return filter_where_by_numeric_field(qs, field_name, value)
