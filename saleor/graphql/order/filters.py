from collections.abc import Mapping
from uuid import UUID

import django_filters
import graphene
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Exists, OuterRef, Q, QuerySet, Value
from django.utils import timezone
from graphql.error import GraphQLError

from ...core.postgres import FlatConcat
from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCardEvent
from ...invoice.models import Invoice
from ...order.models import Fulfillment, FulfillmentLine, Order, OrderEvent, OrderLine
from ...order.search import search_orders
from ...payment import ChargeStatus, PaymentMethodType
from ...payment.models import TransactionItem
from ...product.models import ProductVariant
from ...warehouse.models import Stock, Warehouse
from ..account.filters import AddressFilterInput, filter_address
from ..channel.filters import get_currency_from_filter_data
from ..core.doc_category import DOC_CATEGORY_ORDERS
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.filters.where_filters import (
    BooleanWhereFilter,
    GlobalIDMultipleChoiceWhereFilter,
    ListObjectTypeWhereFilter,
    MetadataWhereBase,
    ObjectTypeWhereFilter,
    OperationObjectTypeWhereFilter,
    filter_where_metadata,
)
from ..core.filters.where_input import (
    FilterInputDescriptions,
    GlobalIDFilterInput,
    IntFilterInput,
    MetadataFilterInput,
    PriceFilterInput,
    StringFilterInput,
    UUIDFilterInput,
    WhereInputObjectType,
)
from ..core.scalars import UUID as UUIDScalar
from ..core.types import (
    BaseInputObjectType,
    DateRangeInput,
    DateTimeRangeInput,
    NonNullList,
)
from ..core.utils import from_global_id_or_error
from ..discount.filters import DiscountedObjectWhere
from ..payment.enums import PaymentChargeStatusEnum, PaymentMethodTypeEnum
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import (
    filter_by_ids,
    filter_range_field,
    filter_where_by_id_field,
    filter_where_by_numeric_field,
    filter_where_by_price_field,
    filter_where_by_range_field,
    filter_where_by_value_field,
)
from .enums import (
    FulfillmentStatusEnum,
    OrderAuthorizeStatusEnum,
    OrderChargeStatusEnum,
    OrderEventsEnum,
    OrderStatusEnum,
    OrderStatusFilter,
)

LIST_INPUT_OBJECT_DESCRIPTION = (
    " Each list item represents conditions that must be satisfied by a single "
    "object. The filter matches orders that have related objects "
    "meeting all specified groups of conditions."
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


def filter_has_invoices(qs, value):
    if value is None:
        return qs.none()
    invoices = Invoice.objects.using(qs.db).filter(order_id=OuterRef("id"))
    if value:
        return qs.filter(Exists(invoices))
    return qs.filter(~Exists(invoices))


def filter_has_fulfillments(qs, value):
    if value is None:
        return qs.none()
    fulfillments = Fulfillment.objects.using(qs.db).filter(order_id=OuterRef("id"))
    if value:
        return qs.filter(Exists(fulfillments))
    return qs.filter(~Exists(fulfillments))


def filter_fulfillments_by_warehouse_details(
    value: Mapping[str, Mapping[str, list[str] | str]], qs: QuerySet[Fulfillment]
) -> QuerySet[Fulfillment]:
    if not value:
        return qs.none()

    warehouse_qs = None
    if warehouse_id_filter := value.get("id"):
        warehouse_qs = filter_where_by_id_field(
            Warehouse.objects.using(qs.db), "id", warehouse_id_filter, "Warehouse"
        )
    if warehouse_slug_filter := value.get("slug"):
        if warehouse_qs is None:
            warehouse_qs = Warehouse.objects.using(qs.db)
        warehouse_qs = filter_where_by_value_field(
            warehouse_qs, "slug", warehouse_slug_filter
        )
    if warehouse_external_reference := value.get("external_reference"):
        if warehouse_qs is None:
            warehouse_qs = Warehouse.objects.using(qs.db)
        warehouse_qs = filter_where_by_value_field(
            warehouse_qs, "external_reference", warehouse_external_reference
        )
    if warehouse_qs is None:
        return qs.none()

    stocks_qs = Stock.objects.using(qs.db).filter(
        Exists(warehouse_qs.filter(id=OuterRef("warehouse_id")))
    )
    fulfillment_lines_qs = FulfillmentLine.objects.using(qs.db).filter(
        Exists(stocks_qs.filter(id=OuterRef("stock_id")))
    )
    return qs.filter(Exists(fulfillment_lines_qs.filter(fulfillment_id=OuterRef("id"))))


def filter_fulfillments(qs, value):
    if not value:
        return qs.none()

    lookup = Q()
    for input_data in value:
        fulfillment_qs = None
        if status_value := input_data.get("status"):
            fulfillment_qs = filter_where_by_value_field(
                Fulfillment.objects.using(qs.db), "status", status_value
            )
        if metadata_value := input_data.get("metadata"):
            if fulfillment_qs is None:
                fulfillment_qs = Fulfillment.objects.using(qs.db)
            fulfillment_qs = filter_where_metadata(fulfillment_qs, None, metadata_value)
        if warehouse_value := input_data.get("warehouse"):
            if fulfillment_qs is None:
                fulfillment_qs = Fulfillment.objects.using(qs.db)
            fulfillment_qs = filter_fulfillments_by_warehouse_details(
                value=warehouse_value, qs=fulfillment_qs
            )
        if fulfillment_qs is not None:
            lookup &= Q(Exists(fulfillment_qs.filter(order_id=OuterRef("id"))))
    if lookup:
        return qs.filter(lookup)
    return qs.none()


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


class InvoiceFilterInput(BaseInputObjectType):
    created_at = DateTimeRangeInput(
        description="Filter invoices by creation date.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter input for invoices."


class FulfillmentStatusEnumFilterInput(BaseInputObjectType):
    eq = FulfillmentStatusEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        FulfillmentStatusEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter by fulfillment status."


class FulfillmentWarehouseFilterInput(BaseInputObjectType):
    id = GlobalIDFilterInput(
        description="Filter fulfillments by warehouse ID.",
        required=False,
    )
    slug = StringFilterInput(
        description="Filter fulfillments by warehouse slug.",
        required=False,
    )
    external_reference = StringFilterInput(
        description="Filter fulfillments by warehouse external reference.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter input for fulfillment warehouses."


class FulfillmentFilterInput(BaseInputObjectType):
    status = FulfillmentStatusEnumFilterInput(
        description="Filter by fulfillment status."
    )
    metadata = MetadataFilterInput(description="Filter by metadata fields.")
    warehouse = FulfillmentWarehouseFilterInput(
        description="Filter by fulfillment warehouse.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter input for order fulfillments data."


class LinesFilterInput(BaseInputObjectType):
    metadata = MetadataFilterInput(
        description="Filter by metadata fields of order lines."
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter input for order lines data."


class OrderEventTypeEnumFilterInput(BaseInputObjectType):
    eq = OrderEventsEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        OrderEventsEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )


class OrderEventFilterInput(BaseInputObjectType):
    date = DateTimeRangeInput(
        description="Filter order events by date.",
    )
    type = OrderEventTypeEnumFilterInput(
        description="Filter order events by type.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter input for order events data."


class PaymentMethodTypeEnumFilterInput(BaseInputObjectType):
    eq = PaymentMethodTypeEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        PaymentMethodTypeEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )


class PaymentMethodDetailsCardFilterInput(BaseInputObjectType):
    brand = StringFilterInput(
        description="Filter by payment method brand used to pay for the order.",
    )


class PaymentMethodDetailsFilterInput(BaseInputObjectType):
    type = PaymentMethodTypeEnumFilterInput(
        description="Filter by payment method type used to pay for the order.",
    )
    card = PaymentMethodDetailsCardFilterInput(
        description="Filter by card details used to pay for the order. Skips `type` filter if provided.",
    )

    @staticmethod
    def filter_card(qs, _, value):
        if value is None:
            return qs.none()
        transaction_qs = qs.filter(payment_method_type=PaymentMethodType.CARD)
        if brand_filter_value := value.get("brand"):
            transaction_qs = filter_where_by_value_field(
                transaction_qs, "cc_brand", brand_filter_value
            )
        return transaction_qs

    @staticmethod
    def filter_type(qs, _, value):
        if value is None:
            return qs.none()
        transaction_qs = filter_where_by_value_field(
            qs,
            "payment_method_type",
            value,
        )
        return transaction_qs


class TransactionFilterInput(BaseInputObjectType):
    payment_method_details = PaymentMethodDetailsFilterInput(
        description="Filter by payment method details used to pay for the order.",
    )
    metadata = MetadataFilterInput(
        description="Filter by metadata fields of transactions."
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        description = "Filter input for transactions."

    @staticmethod
    def filter_payment_method_details(qs, _, value):
        if value is None:
            return qs.none()

        if filter_value := value.get("card"):
            return PaymentMethodDetailsFilterInput.filter_card(qs, _, filter_value)
        if filter_value := value.get("type"):
            return PaymentMethodDetailsFilterInput.filter_type(qs, _, filter_value)
        return qs.none()

    @staticmethod
    def filter_metadata(qs, _, value):
        if value is None:
            return qs.none()

        return filter_where_metadata(qs, None, value)


def filter_where_number(qs, _, value):
    return filter_where_by_numeric_field(qs, "number", value)


def filter_where_channel_id(qs, _, value):
    if not value:
        return qs
    return filter_where_by_id_field(qs, "channel", value, "Channel")


def filter_where_created_at_range(qs, _, value):
    return filter_where_by_range_field(qs, "created_at", value)


def filter_where_updated_at_range(qs, _, value):
    return filter_where_by_range_field(qs, "updated_at", value)


def filter_where_user(qs, _, value):
    return filter_where_by_id_field(qs, "user", value, "User")


def filter_where_user_email(qs, _, value):
    return filter_where_by_value_field(qs, "user_email", value)


def filter_where_authorize_status(qs, _, value):
    return filter_where_by_value_field(qs, "authorize_status", value)


def filter_where_charge_status(qs, _, value):
    return filter_where_by_value_field(qs, "charge_status", value)


def filter_where_voucher_code(qs, _, value):
    return filter_where_by_value_field(qs, "voucher_code", value)


def filter_where_lines_count(qs, _, value):
    return filter_where_by_numeric_field(qs, "lines_count", value)


def filter_where_total_gross(qs, _, value):
    return filter_where_by_price_field(qs, "total_gross_amount", value)


def filter_where_total_net(qs, _, value):
    return filter_where_by_price_field(qs, "total_net_amount", value)


def filter_where_is_click_and_collect(qs, _, value):
    if value is None:
        return qs.none()
    return filter_is_click_and_collect(qs, _, value)


def filter_where_transactions(qs, _, value):
    if not value:
        return qs.none()

    lookup = Q()
    for input_data in value:
        metadata_value = input_data.get("metadata")
        payment_method_details_value = input_data.get("payment_method_details")

        if not any([metadata_value, payment_method_details_value]):
            return qs.none()

        transaction_qs = None
        if payment_method_details_value:
            transaction_qs = TransactionFilterInput.filter_payment_method_details(
                TransactionItem.objects.using(qs.db), _, payment_method_details_value
            )
        if metadata_value:
            transaction_qs = TransactionFilterInput.filter_metadata(
                transaction_qs or TransactionItem.objects.using(qs.db),
                _,
                metadata_value,
            )
        if transaction_qs is not None:
            lookup &= Q(Exists(transaction_qs.filter(order_id=OuterRef("id"))))

    if lookup:
        return qs.filter(lookup)
    return qs.none()


def filter_where_lines(qs, _, value: list | None):
    if not value:
        return qs.none()

    lookup = Q()
    for input_data in value:
        if metadata_value := input_data.get("metadata"):
            lines_qs = filter_where_metadata(
                OrderLine.objects.using(qs.db), None, metadata_value
            )
            lookup &= Q(Exists(lines_qs.filter(order_id=OuterRef("id"))))
    if lookup:
        return qs.filter(lookup)
    return qs.none()


def filter_where_product_type_id(qs, _, value):
    if not value:
        return qs

    line_qs = filter_where_by_id_field(
        OrderLine.objects.using(qs.db), "product_type_id", value, "ProductType"
    )
    return qs.filter(Exists(line_qs.filter(order_id=OuterRef("id"))))


def filter_where_events(qs, _, value: list | None):
    if not value:
        return qs.none()

    lookup = Q()
    for input_data in value:
        if not {"date", "type"}.intersection(input_data.keys()):
            return qs.none()

        event_qs = None
        if filter_value := input_data.get("date"):
            event_qs = filter_where_by_range_field(
                OrderEvent.objects.using(qs.db), "date", filter_value
            )
        if filter_value := input_data.get("type"):
            event_qs = filter_where_by_value_field(
                event_qs or OrderEvent.objects.using(qs.db), "type", filter_value
            )
        if event_qs is not None:
            lookup &= Q(Exists(event_qs.filter(order_id=OuterRef("id"))))
    if lookup:
        return qs.filter(lookup)
    return qs.none()


def filter_where_billing_address(qs, _, value):
    if not value:
        return qs.none()
    address_qs = filter_address(value)
    return qs.filter(Exists(address_qs.filter(id=OuterRef("billing_address_id"))))


def filter_where_shipping_address(qs, _, value):
    if not value:
        return qs.none()
    address_qs = filter_address(value)
    return qs.filter(Exists(address_qs.filter(id=OuterRef("shipping_address_id"))))


class OrderWhere(MetadataWhereBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Order"))
    number = OperationObjectTypeWhereFilter(
        input_class=IntFilterInput,
        method=filter_where_number,
        help_text="Filter by order number.",
    )
    channel_id = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method=filter_where_channel_id,
        help_text="Filter by channel.",
    )
    created_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method=filter_where_created_at_range,
        help_text="Filter order by created at date.",
    )
    updated_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method=filter_where_updated_at_range,
        help_text="Filter order by updated at date.",
    )
    user = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method=filter_where_user,
        help_text="Filter by user.",
    )
    user_email = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method=filter_where_user_email,
        help_text="Filter by user email.",
    )
    authorize_status = OperationObjectTypeWhereFilter(
        input_class=OrderAuthorizeStatusEnumFilterInput,
        method=filter_where_authorize_status,
        help_text="Filter by authorize status.",
    )
    charge_status = OperationObjectTypeWhereFilter(
        input_class=OrderChargeStatusEnumFilterInput,
        method=filter_where_charge_status,
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
        method=filter_where_is_click_and_collect,
        help_text="Filter by whether the order uses the click and collect delivery method.",
    )
    is_gift_card_used = BooleanWhereFilter(
        method="filter_is_gift_card_used",
        help_text="Filter based on whether a gift card was used in the order.",
    )
    is_gift_card_bought = BooleanWhereFilter(
        method="filter_is_gift_card_bought",
        help_text="Filter based on whether the order includes a gift card purchase.",
    )
    voucher_code = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method=filter_where_voucher_code,
        help_text="Filter by voucher code used in the order.",
    )
    has_invoices = BooleanWhereFilter(
        method="filter_has_invoices",
        help_text="Filter by whether the order has any invoices.",
    )
    invoices = ListObjectTypeWhereFilter(
        input_class=InvoiceFilterInput,
        method="filter_invoices",
        help_text=(
            "Filter by invoice data associated with the order."
            + LIST_INPUT_OBJECT_DESCRIPTION
        ),
    )
    has_fulfillments = BooleanWhereFilter(
        method="filter_has_fulfillments",
        help_text="Filter by whether the order has any fulfillments.",
    )
    fulfillments = ListObjectTypeWhereFilter(
        input_class=FulfillmentFilterInput,
        method="filter_fulfillments",
        help_text=(
            "Filter by fulfillment data associated with the order."
            + LIST_INPUT_OBJECT_DESCRIPTION
        ),
    )
    lines = ListObjectTypeWhereFilter(
        input_class=LinesFilterInput,
        method=filter_where_lines,
        help_text=(
            "Filter by line items associated with the order."
            + LIST_INPUT_OBJECT_DESCRIPTION
        ),
    )
    lines_count = OperationObjectTypeWhereFilter(
        input_class=IntFilterInput,
        method=filter_where_lines_count,
        help_text="Filter by number of lines in the order.",
    )
    transactions = ListObjectTypeWhereFilter(
        input_class=TransactionFilterInput,
        method=filter_where_transactions,
        help_text=(
            "Filter by transaction data associated with the order."
            + LIST_INPUT_OBJECT_DESCRIPTION
        ),
    )
    total_gross = ObjectTypeWhereFilter(
        input_class=PriceFilterInput,
        method=filter_where_total_gross,
        help_text="Filter by total gross amount of the order.",
    )
    total_net = ObjectTypeWhereFilter(
        input_class=PriceFilterInput,
        method=filter_where_total_net,
        help_text="Filter by total net amount of the order.",
    )
    product_type_id = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method=filter_where_product_type_id,
        help_text="Filter by the product type of related order lines.",
    )
    events = ListObjectTypeWhereFilter(
        input_class=OrderEventFilterInput,
        method=filter_where_events,
        help_text=("Filter by order events." + LIST_INPUT_OBJECT_DESCRIPTION),
    )
    billing_address = ObjectTypeWhereFilter(
        input_class=AddressFilterInput,
        method=filter_where_billing_address,
        help_text="Filter by billing address of the order.",
    )
    shipping_address = ObjectTypeWhereFilter(
        input_class=AddressFilterInput,
        method=filter_where_shipping_address,
        help_text="Filter by shipping address of the order.",
    )

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
    def filter_is_gift_card_used(qs, _, value):
        if value is None:
            return qs.none()
        return filter_by_gift_card(qs, value, GiftCardEvents.USED_IN_ORDER)

    @staticmethod
    def filter_is_gift_card_bought(qs, _, value):
        if value is None:
            return qs.none()
        return filter_by_gift_card(qs, value, GiftCardEvents.BOUGHT)

    @staticmethod
    def filter_has_invoices(qs, _, value):
        return filter_has_invoices(qs, value)

    @staticmethod
    def filter_invoices(qs, _, value):
        if not value:
            return qs.none()

        lookup = Q()
        for input_data in value:
            if filter_value := input_data.get("created_at"):
                invoices = filter_where_by_range_field(
                    Invoice.objects.using(qs.db), "created_at", filter_value
                )
                lookup &= Q(Exists(invoices.filter(order_id=OuterRef("id"))))
        if lookup:
            return qs.filter(lookup)
        return qs.none()

    @staticmethod
    def filter_has_fulfillments(qs, _, value):
        return filter_has_fulfillments(qs, value)

    @staticmethod
    def filter_fulfillments(qs, _, value):
        return filter_fulfillments(qs, value)


class OrderWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        filterset_class = OrderWhere


class DraftOrderWhere(MetadataWhereBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("Order"))
    number = OperationObjectTypeWhereFilter(
        input_class=IntFilterInput,
        method=filter_where_number,
        help_text="Filter by order number.",
    )
    channel_id = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method=filter_where_channel_id,
        help_text="Filter by channel.",
    )
    created_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method=filter_where_created_at_range,
        help_text="Filter order by created at date.",
    )
    updated_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method=filter_where_updated_at_range,
        help_text="Filter order by updated at date.",
    )
    user = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method=filter_where_user,
        help_text="Filter by user.",
    )
    user_email = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method=filter_where_user_email,
        help_text="Filter by user email.",
    )
    authorize_status = OperationObjectTypeWhereFilter(
        input_class=OrderAuthorizeStatusEnumFilterInput,
        method=filter_where_authorize_status,
        help_text="Filter by authorize status.",
    )
    charge_status = OperationObjectTypeWhereFilter(
        input_class=OrderChargeStatusEnumFilterInput,
        method=filter_where_charge_status,
        help_text="Filter by charge status.",
    )
    is_click_and_collect = BooleanWhereFilter(
        method=filter_where_is_click_and_collect,
        help_text="Filter by whether the order uses the click and collect delivery method.",
    )
    voucher_code = OperationObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method=filter_where_voucher_code,
        help_text="Filter by voucher code used in the order.",
    )
    lines = ListObjectTypeWhereFilter(
        input_class=LinesFilterInput,
        method=filter_where_lines,
        help_text=(
            "Filter by line items associated with the order."
            + LIST_INPUT_OBJECT_DESCRIPTION
        ),
    )
    lines_count = OperationObjectTypeWhereFilter(
        input_class=IntFilterInput,
        method=filter_where_lines_count,
        help_text="Filter by number of lines in the order.",
    )
    transactions = ListObjectTypeWhereFilter(
        input_class=TransactionFilterInput,
        method=filter_where_transactions,
        help_text=(
            "Filter by transaction data associated with the order."
            + LIST_INPUT_OBJECT_DESCRIPTION
        ),
    )
    total_gross = ObjectTypeWhereFilter(
        input_class=PriceFilterInput,
        method=filter_where_total_gross,
        help_text="Filter by total gross amount of the order.",
    )
    total_net = ObjectTypeWhereFilter(
        input_class=PriceFilterInput,
        method=filter_where_total_net,
        help_text="Filter by total net amount of the order.",
    )
    product_type_id = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method=filter_where_product_type_id,
        help_text="Filter by the product type of related order lines.",
    )
    events = ListObjectTypeWhereFilter(
        input_class=OrderEventFilterInput,
        method=filter_where_events,
        help_text=("Filter by order events." + LIST_INPUT_OBJECT_DESCRIPTION),
    )
    billing_address = ObjectTypeWhereFilter(
        input_class=AddressFilterInput,
        method=filter_where_billing_address,
        help_text="Filter by billing address of the order.",
    )
    shipping_address = ObjectTypeWhereFilter(
        input_class=AddressFilterInput,
        method=filter_where_shipping_address,
        help_text="Filter by shipping address of the order.",
    )


class DraftOrderWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ORDERS
        filterset_class = DraftOrderWhere


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
