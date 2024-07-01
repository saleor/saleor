import copy
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from dataclasses import fields as dataclass_fields
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

import graphene
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db.models import Q
from django.utils import timezone
from graphql import GraphQLError
from prices import Money

from ....account.models import Address, User
from ....app.models import App
from ....channel.models import Channel
from ....core import JobStatus
from ....core.prices import quantize_price
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....core.weight import zero_weight
from ....discount.models import OrderDiscount, VoucherCode
from ....giftcard.models import GiftCard
from ....invoice.models import Invoice
from ....order import (
    FulfillmentStatus,
    OrderEvents,
    OrderOrigin,
    OrderStatus,
    StockUpdatePolicy,
)
from ....order.error_codes import OrderBulkCreateErrorCode
from ....order.models import Fulfillment, FulfillmentLine, Order, OrderEvent, OrderLine
from ....order.search import update_order_search_vector
from ....order.utils import update_order_display_gross_prices, updates_amounts_for_order
from ....payment import TransactionEventType
from ....payment.models import TransactionEvent, TransactionItem
from ....permission.enums import OrderPermissions
from ....product.models import ProductVariant
from ....shipping.models import ShippingMethod, ShippingMethodChannelListing
from ....tax.models import TaxClass
from ....warehouse.models import Stock, Warehouse
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_314, ADDED_IN_318, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.enums import ErrorPolicy, ErrorPolicyEnum, LanguageCodeEnum
from ...core.mutations import BaseMutation
from ...core.scalars import DateTime, PositiveDecimal, WeightScalar
from ...core.types import BaseInputObjectType, BaseObjectType, NonNullList
from ...core.types.common import OrderBulkCreateError
from ...core.utils import from_global_id_or_error
from ...meta.inputs import MetadataInput
from ...payment.mutations.transaction.transaction_create import (
    TransactionCreate,
    TransactionCreateInput,
)
from ...payment.utils import metadata_contains_empty_key
from ...plugins.dataloaders import get_plugin_manager_promise
from ..enums import OrderStatusEnum, StockUpdatePolicyEnum
from ..mutations.order_discount_common import (
    OrderDiscountCommon,
    OrderDiscountCommonInput,
)
from ..types import Order as OrderType
from .utils import get_instance

MINUTES_DIFF = 5
MAX_ORDERS = 50
MAX_NOTE_LENGTH = 255


@dataclass
class OrderBulkError:
    message: str
    code: Optional[OrderBulkCreateErrorCode] = None
    path: Optional[str] = None


@dataclass
class OrderBulkFulfillmentLine:
    line: FulfillmentLine
    warehouse: Warehouse


@dataclass
class OrderBulkFulfillment:
    fulfillment: Fulfillment
    lines: list[OrderBulkFulfillmentLine]


@dataclass
class OrderBulkOrderLine:
    line: OrderLine
    warehouse: Warehouse


@dataclass
class OrderBulkTransaction:
    transaction: TransactionItem
    events: list[TransactionEvent]


@dataclass
class OrderBulkCreateData:
    order: Optional[Order] = None
    errors: list[OrderBulkError] = dataclass_field(default_factory=list)
    lines: list[OrderBulkOrderLine] = dataclass_field(default_factory=list)
    notes: list[OrderEvent] = dataclass_field(default_factory=list)
    fulfillments: list[OrderBulkFulfillment] = dataclass_field(default_factory=list)
    transactions: list[OrderBulkTransaction] = dataclass_field(default_factory=list)
    invoices: list[Invoice] = dataclass_field(default_factory=list)
    discounts: list[OrderDiscount] = dataclass_field(default_factory=list)
    gift_cards: list[GiftCard] = dataclass_field(default_factory=list)
    user: Optional[User] = None
    billing_address: Optional[Address] = None
    channel: Optional[Channel] = None
    shipping_address: Optional[Address] = None
    voucher_code: Optional[VoucherCode] = None
    # error which ignores error policy and disqualify order
    is_critical_error: bool = False

    def set_fulfillment_id(self):
        for fulfillment in self.fulfillments:
            for fulfillment_line in fulfillment.lines:
                fulfillment_line.line.fulfillment_id = fulfillment.fulfillment.id

    def set_quantity_fulfilled(self):
        map = self.orderline_quantityfulfilled_map
        for order_line in self.lines:
            order_line.line.quantity_fulfilled = map.get(order_line.line.id) or 0

    def set_fulfillment_order(self):
        order = 1
        for fulfillment in self.fulfillments:
            fulfillment.fulfillment.fulfillment_order = order
            order += 1

    def set_transaction_id(self):
        for transaction_data in self.transactions:
            for event in transaction_data.events:
                event.transaction = transaction_data.transaction

    def link_gift_cards(self):
        if self.order:
            self.order.gift_cards.add(*self.gift_cards)

    def post_create_order_update(self):
        if self.order:
            updates_amounts_for_order(self.order, save=False)
            update_order_search_vector(self.order, save=False)

    @property
    def all_order_lines(self) -> list[OrderLine]:
        return [order_line.line for order_line in self.lines]

    @property
    def all_fulfillment_lines(self) -> list[FulfillmentLine]:
        return [
            fulfillment_line.line
            for fulfillment in self.fulfillments
            for fulfillment_line in fulfillment.lines
        ]

    @property
    def all_transactions(self) -> list[TransactionItem]:
        return [transaction_data.transaction for transaction_data in self.transactions]

    @property
    def all_transaction_events(self) -> list[TransactionEvent]:
        return [
            event
            for transaction_data in self.transactions
            for event in transaction_data.events
        ]

    @property
    def all_invoices(self) -> list[Invoice]:
        return [invoice for invoice in self.invoices]

    @property
    def all_discounts(self) -> list[OrderDiscount]:
        return [discount for discount in self.discounts]

    @property
    def orderline_fulfillmentlines_map(
        self,
    ) -> dict[UUID, list[OrderBulkFulfillmentLine]]:
        map: dict[UUID, list] = defaultdict(list)
        for fulfillment in self.fulfillments:
            for fulfillment_line in fulfillment.lines:
                map[fulfillment_line.line.order_line.id].append(fulfillment_line)
        return map

    @property
    def orderline_quantityfulfilled_map(self) -> dict[UUID, int]:
        map: dict[UUID, int] = defaultdict(int)
        for (
            order_line,
            fulfillment_lines,
        ) in self.orderline_fulfillmentlines_map.items():
            map[order_line] = sum(
                [
                    fulfillment_line.line.quantity
                    for fulfillment_line in fulfillment_lines
                ]
            )
        return map

    @property
    def unique_variant_ids(self) -> list[int]:
        return list(
            set(
                [
                    order_line.line.variant.id
                    for order_line in self.lines
                    if order_line.line.variant
                ]
            )
        )

    @property
    def unique_warehouse_ids(self) -> list[UUID]:
        return list(set([order_line.warehouse.id for order_line in self.lines]))

    @property
    def total_order_quantity(self):
        return sum(order_line.line.quantity for order_line in self.lines)

    @property
    def total_fulfillment_quantity(self):
        return sum(
            fulfillment_line.line.quantity
            for fulfillment in self.fulfillments
            for fulfillment_line in fulfillment.lines
        )


@dataclass
class DeliveryMethod:
    is_shipping_required: bool
    warehouse: Optional[Warehouse] = None
    warehouse_name: Optional[str] = None
    shipping_method: Optional[ShippingMethod] = None
    shipping_method_name: Optional[str] = None
    shipping_tax_class: Optional[TaxClass] = None
    shipping_tax_class_name: Optional[str] = None
    shipping_tax_class_metadata: Optional[list[dict[str, str]]] = None
    shipping_tax_class_private_metadata: Optional[list[dict[str, str]]] = None


@dataclass
class OrderAmounts:
    shipping_price_gross: Decimal
    shipping_price_net: Decimal
    total_gross: Decimal
    total_net: Decimal
    undiscounted_total_gross: Decimal
    undiscounted_total_net: Decimal
    shipping_tax_rate: Decimal


@dataclass
class LineAmounts:
    total_gross: Decimal
    total_net: Decimal
    unit_gross: Decimal
    unit_net: Decimal
    undiscounted_total_gross: Decimal
    undiscounted_total_net: Decimal
    undiscounted_unit_gross: Decimal
    undiscounted_unit_net: Decimal
    unit_discount_amount: Decimal
    quantity: int
    tax_rate: Decimal


@dataclass
class ModelIdentifier:
    model: str
    keys: list[str] = dataclass_field(default_factory=list)


@dataclass
class ModelIdentifiers:
    user_ids: ModelIdentifier = ModelIdentifier(model="User")
    user_emails: ModelIdentifier = ModelIdentifier(model="User")
    user_external_references: ModelIdentifier = ModelIdentifier(model="User")
    channel_slugs: ModelIdentifier = ModelIdentifier(model="Channel")
    voucher_codes: ModelIdentifier = ModelIdentifier(model="VoucherCode")
    warehouse_ids: ModelIdentifier = ModelIdentifier(model="Warehouse")
    shipping_method_ids: ModelIdentifier = ModelIdentifier(model="ShippingMethod")
    tax_class_ids: ModelIdentifier = ModelIdentifier(model="TaxClass")
    order_external_references: ModelIdentifier = ModelIdentifier(model="Order")
    variant_ids: ModelIdentifier = ModelIdentifier(model="ProductVariant")
    variant_skus: ModelIdentifier = ModelIdentifier(model="ProductVariant")
    variant_external_references: ModelIdentifier = ModelIdentifier(
        model="ProductVariant"
    )
    gift_card_codes: ModelIdentifier = ModelIdentifier(model="GiftCard")
    app_ids: ModelIdentifier = ModelIdentifier(model="App")


class TaxedMoneyInput(BaseInputObjectType):
    gross = PositiveDecimal(required=True, description="Gross value of an item.")
    net = PositiveDecimal(required=True, description="Net value of an item.")

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateUserInput(BaseInputObjectType):
    id = graphene.ID(description="Customer ID associated with the order.")
    email = graphene.String(description="Customer email associated with the order.")
    external_reference = graphene.String(
        description="Customer external ID associated with the order."
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateInvoiceInput(BaseInputObjectType):
    created_at = DateTime(
        required=True, description="The date, when the invoice was created."
    )
    number = graphene.String(description="Invoice number.")
    url = graphene.String(description="URL of the invoice to download.")
    metadata = NonNullList(MetadataInput, description="Metadata of the invoice.")
    private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the invoice."
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateDeliveryMethodInput(BaseInputObjectType):
    warehouse_id = graphene.ID(description="The ID of the warehouse.")
    warehouse_name = graphene.String(description="The name of the warehouse.")
    shipping_method_id = graphene.ID(description="The ID of the shipping method.")
    shipping_method_name = graphene.String(
        description="The name of the shipping method."
    )
    shipping_price = graphene.Field(
        TaxedMoneyInput, description="The price of the shipping."
    )
    shipping_tax_rate = PositiveDecimal(description="Tax rate of the shipping.")
    shipping_tax_class_id = graphene.ID(description="The ID of the tax class.")
    shipping_tax_class_name = graphene.String(description="The name of the tax class.")
    shipping_tax_class_metadata = NonNullList(
        MetadataInput, description="Metadata of the tax class."
    )
    shipping_tax_class_private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the tax class."
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateNoteInput(BaseInputObjectType):
    message = graphene.String(
        required=True, description=f"Note message. Max characters: {MAX_NOTE_LENGTH}."
    )
    date = DateTime(description="The date associated with the message.")
    user_id = graphene.ID(description="The user ID associated with the message.")
    user_email = graphene.ID(description="The user email associated with the message.")
    user_external_reference = graphene.ID(
        description="The user external ID associated with the message."
    )
    app_id = graphene.ID(description="The app ID associated with the message.")

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateFulfillmentLineInput(BaseInputObjectType):
    variant_id = graphene.ID(description="The ID of the product variant.")
    variant_sku = graphene.String(description="The SKU of the product variant.")
    variant_external_reference = graphene.String(
        description="The external ID of the product variant."
    )
    quantity = graphene.Int(
        description="The number of line items to be fulfilled from given warehouse.",
        required=True,
    )
    warehouse = graphene.ID(
        description="ID of the warehouse from which the item will be fulfilled.",
        required=True,
    )
    order_line_index = graphene.Int(
        required=True,
        description=(
            "0-based index of order line, which the fulfillment line refers to."
        ),
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateFulfillmentInput(BaseInputObjectType):
    tracking_code = graphene.String(description="Fulfillment's tracking code.")
    lines = NonNullList(
        OrderBulkCreateFulfillmentLineInput,
        description="List of items informing how to fulfill the order.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateOrderLineInput(BaseInputObjectType):
    variant_id = graphene.ID(description="The ID of the product variant.")
    variant_sku = graphene.String(description="The SKU of the product variant.")
    variant_external_reference = graphene.String(
        description="The external ID of the product variant."
    )
    variant_name = graphene.String(description="The name of the product variant.")
    product_name = graphene.String(description="The name of the product.")
    translated_variant_name = graphene.String(
        description="Translation of the product variant name."
    )
    translated_product_name = graphene.String(
        description="Translation of the product name."
    )
    created_at = DateTime(
        required=True, description="The date, when the order line was created."
    )
    is_shipping_required = graphene.Boolean(
        required=True,
        description="Determines whether shipping of the order line items is required.",
    )
    is_gift_card = graphene.Boolean(required=True, description="Gift card flag.")
    quantity = graphene.Int(
        required=True, description="Number of items in the order line"
    )
    total_price = graphene.Field(
        TaxedMoneyInput, required=True, description="Price of the order line."
    )
    undiscounted_total_price = graphene.Field(
        TaxedMoneyInput,
        required=True,
        description="Price of the order line excluding applied discount.",
    )
    warehouse = graphene.ID(
        required=True,
        description="The ID of the warehouse, where the line will be allocated.",
    )
    metadata = NonNullList(MetadataInput, description="Metadata of the order line.")
    private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the order line."
    )
    tax_rate = PositiveDecimal(description="Tax rate of the order line.")
    tax_class_id = graphene.ID(description="The ID of the tax class.")
    tax_class_name = graphene.String(description="The name of the tax class.")
    tax_class_metadata = NonNullList(
        MetadataInput, description="Metadata of the tax class."
    )
    tax_class_private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the tax class."
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateInput(BaseInputObjectType):
    external_reference = graphene.String(description="External ID of the order.")
    channel = graphene.String(
        required=True, description="Slug of the channel associated with the order."
    )
    created_at = DateTime(
        required=True,
        description="The date, when the order was inserted to Saleor database.",
    )
    status = OrderStatusEnum(description="Status of the order.")
    user = graphene.Field(
        OrderBulkCreateUserInput,
        required=True,
        description="Customer associated with the order.",
    )
    billing_address = graphene.Field(
        AddressInput, required=True, description="Billing address of the customer."
    )
    shipping_address = graphene.Field(
        AddressInput, description="Shipping address of the customer."
    )
    currency = graphene.String(required=True, description="Currency code.")
    metadata = NonNullList(MetadataInput, description="Metadata of the order.")
    private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the order."
    )
    customer_note = graphene.String(description="Note about customer.")
    notes = NonNullList(
        OrderBulkCreateNoteInput,
        description="Notes related to the order.",
    )
    language_code = graphene.Argument(
        LanguageCodeEnum, required=True, description="Order language code."
    )
    display_gross_prices = graphene.Boolean(
        description=("Determines whether displayed prices should include taxes."),
    )
    weight = WeightScalar(description="Weight of the order in kg.")
    redirect_url = graphene.String(
        description="URL of a view, where users should be redirected "
        "to see the order details.",
    )
    lines = NonNullList(
        OrderBulkCreateOrderLineInput, required=True, description="List of order lines."
    )
    delivery_method = graphene.Field(
        OrderBulkCreateDeliveryMethodInput,
        description="The delivery method selected for this order.",
    )
    gift_cards = NonNullList(
        graphene.String,
        description="List of gift card codes associated with the order.",
    )
    voucher_code = graphene.String(
        description="Code of a voucher associated with the order." + ADDED_IN_318
    )
    discounts = NonNullList(OrderDiscountCommonInput, description="List of discounts.")
    fulfillments = NonNullList(
        OrderBulkCreateFulfillmentInput, description="Fulfillments of the order."
    )
    transactions = NonNullList(
        TransactionCreateInput, description="Transactions related to the order."
    )
    invoices = NonNullList(
        OrderBulkCreateInvoiceInput, description="Invoices related to the order."
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreateResult(BaseObjectType):
    order = graphene.Field(OrderType, description="Order data.")
    errors = NonNullList(
        OrderBulkCreateError,
        description="List of errors occurred on create attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderBulkCreate(BaseMutation, I18nMixin):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were created.",
    )
    results = NonNullList(
        OrderBulkCreateResult,
        required=True,
        default_value=[],
        description="List of the created orders.",
    )

    class Arguments:
        orders = NonNullList(
            OrderBulkCreateInput,
            required=True,
            description=f"Input list of orders to create. Orders limit: {MAX_ORDERS}.",
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
            ),
        )
        stock_update_policy = StockUpdatePolicyEnum(
            required=False,
            description=(
                "Determine how stock should be updated, while processing the order. "
                "DEFAULT: UPDATE - Only do update, if there is enough stocks."
            ),
        )

    class Meta:
        description = "Creates multiple orders." + ADDED_IN_314 + PREVIEW_FEATURE
        permissions = (OrderPermissions.MANAGE_ORDERS_IMPORT,)
        doc_category = DOC_CATEGORY_ORDERS
        error_type_class = OrderBulkCreateError
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def get_all_instances(cls, orders_input) -> dict[str, Any]:
        """Retrieve all required instances to process orders.

        Return:
            Dictionary with keys "{model_name}.{key_name}.{key_value}" and model
            instances as values.

        """
        # Collect all model keys from input
        identifiers = ModelIdentifiers()
        for order in orders_input:
            identifiers.user_ids.keys.append(order["user"].get("id"))
            identifiers.user_emails.keys.append(order["user"].get("email"))
            identifiers.user_external_references.keys.append(
                order["user"].get("external_reference")
            )
            identifiers.channel_slugs.keys.append(order.get("channel"))
            identifiers.voucher_codes.keys.append(order.get("voucher_code"))
            identifiers.order_external_references.keys.append(
                order.get("external_reference")
            )
            if delivery_method := order.get("delivery_method"):
                identifiers.warehouse_ids.keys.append(
                    delivery_method.get("warehouse_id")
                )
                identifiers.shipping_method_ids.keys.append(
                    delivery_method.get("shipping_method_id")
                )
                identifiers.tax_class_ids.keys.append(
                    delivery_method.get("shipping_tax_class_id")
                )
            notes = order.get("notes") or []
            for note in notes:
                identifiers.user_ids.keys.append(note.get("user_id"))
                identifiers.user_emails.keys.append(note.get("user_email"))
                identifiers.user_external_references.keys.append(
                    note.get("user_external_reference")
                )
                identifiers.app_ids.keys.append(note.get("app_id"))
            order_lines = order.get("lines") or []
            for order_line in order_lines:
                identifiers.variant_ids.keys.append(order_line.get("variant_id"))
                identifiers.variant_skus.keys.append(order_line.get("variant_sku"))
                identifiers.variant_external_references.keys.append(
                    order_line.get("variant_external_reference")
                )
                identifiers.warehouse_ids.keys.append(order_line.get("warehouse"))
                identifiers.tax_class_ids.keys.append(order_line.get("tax_class_id"))
            fulfillments = order.get("fulfillments") or []
            for fulfillment in fulfillments:
                for line in fulfillment.get("lines") or []:
                    identifiers.variant_ids.keys.append(line.get("variant_id"))
                    identifiers.variant_skus.keys.append(line.get("variant_sku"))
                    identifiers.variant_external_references.keys.append(
                        line.get("variant_external_reference")
                    )
                    identifiers.warehouse_ids.keys.append(line.get("warehouse"))
            gift_cards = order.get("gift_cards") or []
            for gift_card_code in gift_cards:
                identifiers.gift_card_codes.keys.append(gift_card_code)

        # Convert global ids to model ids and get rid of Nones
        for field in dataclass_fields(identifiers):
            identifier = getattr(identifiers, field.name)
            model, keys = identifier.model, identifier.keys
            keys = [key for key in keys if key is not None]
            setattr(identifier, "keys", keys)
            if "_ids" in field.name:
                model_ids = []
                for global_id in keys:
                    try:
                        _, id = from_global_id_or_error(
                            str(global_id), model, raise_error=True
                        )
                        model_ids.append(id)
                    except GraphQLError:
                        pass
                setattr(identifier, "keys", model_ids)

        # Make DB calls
        users = User.objects.filter(
            Q(pk__in=identifiers.user_ids.keys)
            | Q(email__in=identifiers.user_emails.keys)
            | Q(external_reference__in=identifiers.user_external_references.keys)
        )
        variants = ProductVariant.objects.filter(
            Q(pk__in=identifiers.variant_ids.keys)
            | Q(sku__in=identifiers.variant_skus.keys)
            | Q(external_reference__in=identifiers.variant_external_references.keys)
        )
        channels = Channel.objects.filter(slug__in=identifiers.channel_slugs.keys)
        voucher_codes = VoucherCode.objects.filter(
            code__in=identifiers.voucher_codes.keys
        ).select_related("voucher")
        warehouses = Warehouse.objects.filter(pk__in=identifiers.warehouse_ids.keys)
        shipping_methods = ShippingMethod.objects.filter(
            pk__in=identifiers.shipping_method_ids.keys
        )
        tax_classes = TaxClass.objects.filter(pk__in=identifiers.tax_class_ids.keys)
        apps = App.objects.filter(
            pk__in=identifiers.app_ids.keys, removed_at__isnull=True
        )
        gift_cards = GiftCard.objects.filter(code__in=identifiers.gift_card_codes.keys)
        orders = Order.objects.filter(
            external_reference__in=identifiers.order_external_references.keys
        )

        # Create dictionary
        object_storage: dict[str, Any] = {}
        for user in users:
            object_storage[f"User.id.{user.id}"] = user
            object_storage[f"User.email.{user.email}"] = user
            if user.external_reference:
                object_storage[f"User.external_reference.{user.external_reference}"] = (
                    user
                )

        for variant in variants:
            object_storage[f"ProductVariant.id.{variant.id}"] = variant
            if variant.sku:
                object_storage[f"ProductVariant.id.{variant.sku}"] = variant
            if variant.external_reference:
                object_storage[
                    f"ProductVariant.external_reference.{variant.external_reference}"
                ] = variant

        for channel in channels:
            object_storage[f"Channel.slug.{channel.slug}"] = channel

        for voucher_code in voucher_codes:
            object_storage[f"VoucherCode.code.{voucher_code.code}"] = voucher_code

        for gift_card in gift_cards:
            object_storage[f"GiftCard.code.{gift_card.code}"] = gift_card

        for order in orders:
            object_storage[f"Order.external_reference.{order.external_reference}"] = (
                order
            )

        for object in [*warehouses, *shipping_methods, *tax_classes, *apps]:
            object_storage[f"{object.__class__.__name__}.id.{object.pk}"] = object

        return object_storage

    @classmethod
    def is_datetime_valid(cls, date: datetime) -> bool:
        """We accept future time values with 5 minutes from current time.

        Some systems might have incorrect time that is in the future compared to Saleor.
        At the same time, we don't want to create orders that are too far in the future.
        """
        current_time = timezone.now()
        future_time = current_time + timedelta(minutes=MINUTES_DIFF)
        if not date.tzinfo:
            raise ValidationError(
                message="Input 'date' must be timezone-aware. "
                "Expected format: 'YYYY-MM-DD HH:MM:SS TZ'.",
                code=OrderBulkCreateErrorCode.INVALID.value,
            )
        return date < future_time

    @classmethod
    def is_shipping_required(cls, order_input: dict[str, Any]) -> bool:
        for order_line in order_input["lines"]:
            if order_line["is_shipping_required"]:
                return True
        return False

    @classmethod
    def validate_order_input(
        cls,
        order_input,
        order_data: OrderBulkCreateData,
        object_storage: dict[str, Any],
    ):
        date = order_input.get("created_at")
        if date and not cls.is_datetime_valid(date):
            order_data.errors.append(
                OrderBulkError(
                    message="Order input contains future date.",
                    path="created_at",
                    code=OrderBulkCreateErrorCode.FUTURE_DATE,
                )
            )

        if redirect_url := order_input.get("redirect_url"):
            try:
                validate_storefront_url(redirect_url)
            except ValidationError as err:
                order_data.errors.append(
                    OrderBulkError(
                        message=f"Invalid redirect url: {err.message}.",
                        path="redirect_url",
                        code=OrderBulkCreateErrorCode.INVALID,
                    )
                )

        weight = order_input.get("weight")
        if weight and weight.value < 0:
            order_data.errors.append(
                OrderBulkError(
                    message="Order can't have negative weight.",
                    path="weight",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )

        if external_reference := order_input.get("external_reference"):
            lookup_key = f"Order.external_reference.{external_reference}"
            if object_storage.get(lookup_key):
                order_data.errors.append(
                    OrderBulkError(
                        message=f"Order with external_reference: {external_reference} "
                        f"already exists.",
                        path="external_reference",
                        code=OrderBulkCreateErrorCode.UNIQUE,
                    )
                )
                order_data.is_critical_error = True

        channel = object_storage.get(f"Channel.slug.{order_input['channel']}")
        if channel:
            if channel.currency_code.lower() != order_input["currency"].lower():
                order_data.errors.append(
                    OrderBulkError(
                        message="Currency from input doesn't match channel's currency.",
                        path="currency",
                        code=OrderBulkCreateErrorCode.INCORRECT_CURRENCY,
                    )
                )
                order_data.is_critical_error = True

    @classmethod
    def validate_order_status(cls, status: str, order_data: OrderBulkCreateData):
        total_order_quantity = order_data.total_order_quantity
        total_fulfillment_quantity = order_data.total_fulfillment_quantity

        is_invalid = False
        if total_fulfillment_quantity == 0 and status in [
            OrderStatus.PARTIALLY_FULFILLED,
            OrderStatus.FULFILLED,
        ]:
            is_invalid = True
        if (
            total_fulfillment_quantity > 0
            and (total_order_quantity - total_fulfillment_quantity) > 0
            and status in [OrderStatus.FULFILLED, OrderStatus.UNFULFILLED]
        ):
            is_invalid = True
        if total_order_quantity == total_fulfillment_quantity and status in [
            OrderStatus.PARTIALLY_FULFILLED,
            OrderStatus.UNFULFILLED,
        ]:
            is_invalid = True

        if is_invalid:
            order_data.errors.append(
                OrderBulkError(
                    message="Invalid order status.",
                    path="status",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )

    @classmethod
    def process_metadata(
        cls,
        metadata: list[dict[str, str]],
        errors: list[OrderBulkError],
        path: str,
        field: Any,
    ):
        if metadata_contains_empty_key(metadata):
            errors.append(
                OrderBulkError(
                    message="Metadata key cannot be empty.",
                    path=path,
                    code=OrderBulkCreateErrorCode.METADATA_KEY_REQUIRED,
                )
            )
            metadata = [data for data in metadata if data["key"].strip() != ""]
        for data in metadata:
            field.update({data["key"]: data["value"]})

    @classmethod
    def get_instance_with_errors(
        cls,
        input: dict[str, Any],
        model,
        key_map: dict[str, str],
        errors: list[OrderBulkError],
        object_storage: dict[str, Any],
        path: str = "",
    ):
        """Resolve instance based on input data, model and `key_map` argument provided.

        Args:
            input: data from input
            model: database model associated with searched instance
            key_map: mapping between keys from input and keys from database
            errors: error list to be updated if an error occur
            object_storage: dict with key pattern: {model_name}_{key_name}_{key_value}
                              and instances as values; it is used to search for already
                              resolved instances
            path: path to input field, which caused an error

        Return:
            model instance

        """
        instance = None
        try:
            instance = get_instance(
                input, model, key_map, object_storage, OrderBulkCreateErrorCode, path
            )
        except ValidationError as err:
            errors.append(
                OrderBulkError(
                    message=str(err.message),
                    code=OrderBulkCreateErrorCode(err.code),
                    path=err.params["path"] if err.params else None,
                )
            )
        return instance

    @classmethod
    def get_instances_related_to_order(
        cls,
        order_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        object_storage: dict[str, Any],
        info: ResolveInfo,
    ):
        """Get all instances of objects needed to create an order."""
        user = cls.get_instance_with_errors(
            input=order_input["user"],
            errors=order_data.errors,
            model=User,
            key_map={
                "id": "id",
                "email": "email",
                "external_reference": "external_reference",
            },
            object_storage=object_storage,
            path="user",
        )

        # If user can't be found, but email is provided, consider it as valid.
        user_email = order_input["user"].get("email")
        if (
            not user
            and order_data.errors[-1].code == OrderBulkCreateErrorCode.NOT_FOUND
            and user_email
        ):
            order_data.errors.pop()

        channel = cls.get_instance_with_errors(
            input=order_input,
            errors=order_data.errors,
            model=Channel,
            key_map={"channel": "slug"},
            object_storage=object_storage,
        )

        billing_address: Optional[Address] = None
        billing_address_input = order_input["billing_address"]
        metadata_list = billing_address_input.pop("metadata", None)
        private_metadata_list = billing_address_input.pop("private_metadata", None)
        try:
            billing_address = cls.validate_address(billing_address_input, info=info)
            cls.validate_and_update_metadata(
                billing_address, metadata_list, private_metadata_list
            )
        except Exception:
            order_data.errors.append(
                OrderBulkError(
                    message="Invalid billing address.",
                    path="billing_address",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )

        shipping_address: Optional[Address] = None

        if shipping_address_input := order_input.get("shipping_address"):
            metadata_list = shipping_address_input.pop("metadata", None)
            private_metadata_list = shipping_address_input.pop("private_metadata", None)
            try:
                shipping_address = cls.validate_address(
                    shipping_address_input, info=info
                )
                cls.validate_and_update_metadata(
                    shipping_address, metadata_list, private_metadata_list
                )
            except Exception:
                order_data.errors.append(
                    OrderBulkError(
                        message="Invalid shipping address.",
                        path="shipping_address",
                        code=OrderBulkCreateErrorCode.INVALID,
                    )
                )

        voucher_code = None
        if order_input.get("voucher_code"):
            voucher_code = cls.get_instance_with_errors(
                input=order_input,
                errors=order_data.errors,
                model=VoucherCode,
                key_map={"voucher_code": "code"},
                object_storage=object_storage,
            )

        code_index = 0
        codes = order_input.get("gift_cards") or []
        for code in codes:
            key = f"GiftCard.code.{code}"
            if gift_card := object_storage.get(key):
                order_data.gift_cards.append(gift_card)
                code_index += 1
            else:
                order_data.errors.append(
                    OrderBulkError(
                        message=f"Gift card with code {code} doesn't exist.",
                        code=OrderBulkCreateErrorCode.NOT_FOUND,
                        path=f"gift_cards.{code_index}",
                    )
                )

        order_data.user = user
        order_data.channel = channel
        order_data.billing_address = billing_address
        order_data.shipping_address = shipping_address
        order_data.voucher_code = voucher_code

        if not channel or not billing_address:
            order_data.is_critical_error = True

        return

    @classmethod
    def make_order_line_calculations(
        cls,
        line_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        currency: str,
        index: int,
    ) -> Optional[LineAmounts]:
        gross_amount = line_input["total_price"]["gross"]
        net_amount = line_input["total_price"]["net"]
        undiscounted_gross_amount = line_input["undiscounted_total_price"]["gross"]
        undiscounted_net_amount = line_input["undiscounted_total_price"]["net"]
        quantity = line_input["quantity"]
        tax_rate = line_input.get("tax_rate", None)

        if quantity < 1 or int(quantity) != quantity:
            order_data.errors.append(
                OrderBulkError(
                    message="Invalid quantity. "
                    "Must be integer greater then or equal to 1.",
                    path=f"lines.{index}.quantity",
                    code=OrderBulkCreateErrorCode.INVALID_QUANTITY,
                )
            )
            order_data.is_critical_error = True
        if gross_amount < net_amount:
            order_data.errors.append(
                OrderBulkError(
                    message="Net price can't be greater then gross price.",
                    path=f"lines.{index}.total_price",
                    code=OrderBulkCreateErrorCode.PRICE_ERROR,
                )
            )
            order_data.is_critical_error = True
        if undiscounted_gross_amount < undiscounted_net_amount:
            order_data.errors.append(
                OrderBulkError(
                    message="Net price can't be greater then gross price.",
                    path=f"lines.{index}.undiscounted_total_price",
                    code=OrderBulkCreateErrorCode.PRICE_ERROR,
                )
            )
            order_data.is_critical_error = True
        if (
            undiscounted_gross_amount < gross_amount
            or undiscounted_net_amount < net_amount
        ):
            order_data.errors.append(
                OrderBulkError(
                    message=(
                        "Total price can't be greater then undiscounted total price."
                    ),
                    path=f"lines.{index}.undiscounted_total_price",
                    code=OrderBulkCreateErrorCode.PRICE_ERROR,
                )
            )
            order_data.is_critical_error = True

        if tax_rate is None and net_amount > 0:
            tax_rate = Decimal(gross_amount / net_amount - 1)

        if order_data.is_critical_error:
            return None

        unit_price_net_amount = quantize_price(Decimal(net_amount / quantity), currency)
        unit_price_gross_amount = quantize_price(
            Decimal(gross_amount / quantity), currency
        )
        undiscounted_unit_price_net_amount = quantize_price(
            Decimal(undiscounted_net_amount / quantity), currency
        )
        undiscounted_unit_price_gross_amount = quantize_price(
            Decimal(undiscounted_gross_amount / quantity), currency
        )
        unit_discount_amount = (
            undiscounted_unit_price_net_amount - unit_price_net_amount
        )

        return LineAmounts(
            total_gross=gross_amount,
            total_net=net_amount,
            unit_gross=unit_price_gross_amount,
            unit_net=unit_price_net_amount,
            undiscounted_total_gross=undiscounted_gross_amount,
            undiscounted_total_net=undiscounted_net_amount,
            undiscounted_unit_gross=undiscounted_unit_price_gross_amount,
            undiscounted_unit_net=undiscounted_unit_price_net_amount,
            unit_discount_amount=unit_discount_amount,
            quantity=quantity,
            tax_rate=tax_rate,
        )

    @classmethod
    def make_order_calculations(
        cls,
        delivery_method: DeliveryMethod,
        order_data: OrderBulkCreateData,
        delivery_input: dict[str, Any],
        object_storage: dict[str, Any],
    ) -> OrderAmounts:
        """Calculate all order amount fields."""

        # Calculate shipping amounts
        shipping_price_net_amount = Decimal(0)
        shipping_price_gross_amount = Decimal(0)
        shipping_tax_rate = Decimal(delivery_input.get("shipping_tax_rate") or 0)

        if delivery_method.shipping_method:
            if shipping_price := delivery_input.get("shipping_price"):
                shipping_price_net_amount = Decimal(shipping_price.net)
                shipping_price_gross_amount = Decimal(shipping_price.gross)
                if shipping_price_gross_amount < shipping_price_net_amount:
                    order_data.errors.append(
                        OrderBulkError(
                            message="Net price can't be greater then gross price.",
                            path="delivery_method.shipping_price",
                            code=OrderBulkCreateErrorCode.PRICE_ERROR,
                        )
                    )
                    order_data.is_critical_error = True
                shipping_tax_rate = (
                    shipping_price_gross_amount / shipping_price_net_amount - 1
                )
            else:
                assert order_data.channel
                lookup_key = f"shipping_price.{delivery_method.shipping_method.id}"
                db_price_amount = object_storage.get(lookup_key) or (
                    ShippingMethodChannelListing.objects.values_list(
                        "price_amount", flat=True
                    )
                    .filter(
                        shipping_method_id=delivery_method.shipping_method.id,
                        channel_id=order_data.channel.id,
                    )
                    .first()
                )
                if db_price_amount:
                    shipping_price_net_amount = Decimal(db_price_amount)
                    shipping_price_gross_amount = Decimal(
                        shipping_price_net_amount * (1 + shipping_tax_rate)
                    )
                    object_storage[lookup_key] = db_price_amount

        # Calculate lines
        order_lines = order_data.all_order_lines
        order_total_gross_amount = Decimal(
            sum(line.total_price_gross_amount for line in order_lines)
        )
        order_undiscounted_total_gross_amount = Decimal(
            sum(line.undiscounted_total_price_gross_amount for line in order_lines)
        )
        order_total_net_amount = Decimal(
            sum(line.total_price_net_amount for line in order_lines)
        )
        order_undiscounted_total_net_amount = Decimal(
            sum(line.undiscounted_total_price_net_amount for line in order_lines)
        )

        return OrderAmounts(
            shipping_price_gross=shipping_price_gross_amount,
            shipping_price_net=shipping_price_net_amount,
            shipping_tax_rate=shipping_tax_rate,
            total_gross=order_total_gross_amount,
            total_net=order_total_net_amount,
            undiscounted_total_gross=order_undiscounted_total_gross_amount,
            undiscounted_total_net=order_undiscounted_total_net_amount,
        )

    @classmethod
    def get_delivery_method(
        cls,
        delivery_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        object_storage: dict[str, Any],
        is_shipping_required: bool,
    ) -> DeliveryMethod:
        delivery_method = DeliveryMethod(is_shipping_required=is_shipping_required)
        if not is_shipping_required:
            return delivery_method

        warehouse, shipping_method, shipping_tax_class = None, None, None
        shipping_tax_class_metadata, shipping_tax_class_private_metadata = None, None
        is_warehouse_delivery = delivery_input.get("warehouse_id")
        is_shipping_delivery = delivery_input.get("shipping_method_id")

        if is_warehouse_delivery and is_shipping_delivery:
            order_data.errors.append(
                OrderBulkError(
                    message="Can't provide both warehouse and shipping method IDs.",
                    path="delivery_method",
                    code=OrderBulkCreateErrorCode.TOO_MANY_IDENTIFIERS,
                )
            )

        if is_warehouse_delivery:
            warehouse = cls.get_instance_with_errors(
                input=delivery_input,
                errors=order_data.errors,
                model=Warehouse,
                key_map={"warehouse_id": "id"},
                object_storage=object_storage,
                path="delivery_method.warehouse_id",
            )

        if is_shipping_delivery:
            shipping_method = cls.get_instance_with_errors(
                input=delivery_input,
                errors=order_data.errors,
                model=ShippingMethod,
                key_map={"shipping_method_id": "id"},
                object_storage=object_storage,
                path="delivery_method.shipping_method_id",
            )
            shipping_tax_class = cls.get_instance_with_errors(
                input=delivery_input,
                errors=order_data.errors,
                model=TaxClass,
                key_map={"shipping_tax_class_id": "id"},
                object_storage=object_storage,
                path="delivery_method.shipping_tax_class_id",
            )
            shipping_tax_class_metadata = delivery_input.get(
                "shipping_tax_class_metadata"
            )
            shipping_tax_class_private_metadata = delivery_input.get(
                "shipping_tax_class_private_metadata"
            )

        if not warehouse and not shipping_method:
            order_data.errors.append(
                OrderBulkError(
                    message="No delivery method provided.",
                    path="delivery_method",
                    code=OrderBulkCreateErrorCode.REQUIRED,
                )
            )
            order_data.is_critical_error = True
        else:
            delivery_method = DeliveryMethod(
                is_shipping_required=True,
                warehouse=warehouse,
                warehouse_name=delivery_input.get("warehouse_name"),
                shipping_method=shipping_method,
                shipping_method_name=delivery_input.get("shipping_method_name"),
                shipping_tax_class=shipping_tax_class,
                shipping_tax_class_name=delivery_input.get("shipping_tax_class_name"),
                shipping_tax_class_metadata=shipping_tax_class_metadata,
                shipping_tax_class_private_metadata=shipping_tax_class_private_metadata,
            )

        return delivery_method

    @classmethod
    def create_single_note(
        cls,
        note_input,
        order_data: OrderBulkCreateData,
        object_storage: dict[str, Any],
        index: int,
    ) -> Optional[OrderEvent]:
        if len(note_input["message"]) > MAX_NOTE_LENGTH:
            order_data.errors.append(
                OrderBulkError(
                    message=f"Note message exceeds character limit: {MAX_NOTE_LENGTH}.",
                    path=f"notes.{index}.message",
                    code=OrderBulkCreateErrorCode.NOTE_LENGTH,
                )
            )
            return None

        date = note_input.get("date")
        if date and not cls.is_datetime_valid(date):
            order_data.errors.append(
                OrderBulkError(
                    message="Note input contains future date.",
                    path=f"notes.{index}.date",
                    code=OrderBulkCreateErrorCode.FUTURE_DATE,
                )
            )
            date = timezone.now()

        user, app = None, None
        user_key_map = {
            "user_id": "id",
            "user_email": "email",
            "user_external_reference": "external_reference",
        }
        if any([note_input.get(key) for key in user_key_map.keys()]):
            user = cls.get_instance_with_errors(
                input=note_input,
                errors=order_data.errors,
                model=User,
                key_map=user_key_map,
                object_storage=object_storage,
                path=f"notes.{index}",
            )

        if note_input.get("app_id"):
            app = cls.get_instance_with_errors(
                input=note_input,
                errors=order_data.errors,
                model=App,
                key_map={"app_id": "id"},
                object_storage=object_storage,
                path=f"notes.{index}",
            )

        if user and app:
            user, app = None, None
            order_data.errors.append(
                OrderBulkError(
                    message="Note input contains both user and app identifier.",
                    code=OrderBulkCreateErrorCode.TOO_MANY_IDENTIFIERS,
                    path=f"notes.{index}",
                )
            )

        event = OrderEvent(
            date=date or timezone.now(),
            type=OrderEvents.NOTE_ADDED,
            order=order_data.order,
            parameters={"message": note_input["message"]},
            user=user,
            app=app,
        )

        return event

    @classmethod
    def create_single_discount(
        cls,
        discount_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        order_amounts: OrderAmounts,
        currency: str,
        index: int,
    ) -> OrderDiscount:
        max_total = Money(order_amounts.undiscounted_total_gross, currency)
        try:
            OrderDiscountCommon.validate_order_discount_input(max_total, discount_input)
        except ValidationError as err:
            order_data.errors.append(
                OrderBulkError(
                    message=err.messages[0],
                    path=f"discounts.{index}",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )

        return OrderDiscount(
            order=order_data.order,
            value_type=discount_input["value_type"],
            value=discount_input["value"],
            reason=discount_input.get("reason"),
        )

    @classmethod
    def create_single_invoice(
        cls,
        invoice_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        index: int,
    ) -> Invoice:
        created_at = invoice_input["created_at"]
        if not cls.is_datetime_valid(created_at):
            order_data.errors.append(
                OrderBulkError(
                    message="Invoice input contains future date.",
                    path=f"invoices.{index}.created_at",
                    code=OrderBulkCreateErrorCode.FUTURE_DATE,
                )
            )
            created_at = None

        if url := invoice_input.get("url"):
            try:
                URLValidator()(url)
            except ValidationError:
                order_data.errors.append(
                    OrderBulkError(
                        message="Invalid URL format.",
                        path=f"invoices.{index}.url",
                        code=OrderBulkCreateErrorCode.INVALID,
                    )
                )
                url = None

        invoice = Invoice(
            order=order_data.order,
            number=invoice_input.get("number"),
            status=JobStatus.SUCCESS,
            external_url=url,
            created_at=created_at,
        )

        if metadata := invoice_input.get("metadata"):
            cls.process_metadata(
                metadata=metadata,
                errors=order_data.errors,
                path=f"invoices.{index}.metadata",
                field=invoice.metadata,
            )
        if private_metadata := invoice_input.get("private_metadata"):
            cls.process_metadata(
                metadata=private_metadata,
                errors=order_data.errors,
                path=f"invoices.{index}.private_metadata",
                field=invoice.private_metadata,
            )

        return invoice

    @classmethod
    def create_single_transaction(
        cls,
        transaction_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        index: int,
    ):
        try:
            assert order_data.order
            order = TransactionCreate.validate_input(
                order_data.order, transaction_input
            )
            transaction_data = {
                **transaction_input,
                "currency": order.currency,
                "order_id": order.pk,
            }
            new_transaction = TransactionCreate.create_transaction(
                transaction_data, None, None, save=False
            )
            money_data = TransactionCreate.get_money_data_from_input(transaction_data)
            events: list[TransactionEvent] = []
            if money_data:
                amountfield_eventtype_map = {
                    "authorized_value": TransactionEventType.AUTHORIZATION_SUCCESS,
                    "charged_value": TransactionEventType.CHARGE_SUCCESS,
                    "refunded_value": TransactionEventType.REFUND_SUCCESS,
                    "canceled_value": TransactionEventType.CANCEL_SUCCESS,
                }
                for amount_field, amount in money_data.items():
                    if amount is None:
                        continue
                    transaction_data[amount_field] = amount
                    events.append(
                        TransactionEvent(
                            type=amountfield_eventtype_map[amount_field],
                            amount_value=amount,
                            currency=order.currency,
                            include_in_calculations=True,
                            created_at=timezone.now(),
                            message="Manual adjustment of the transaction.",
                        )
                    )

            order_data.transactions.append(
                OrderBulkTransaction(transaction=new_transaction, events=events)
            )
        except ValidationError as error:
            for field, err in error.error_dict.items():
                message = str(err[0].message)
                code = err[0].code
                order_data.errors.append(
                    OrderBulkError(
                        message=message,
                        path=f"transactions.{index}",
                        code=OrderBulkCreateErrorCode(code),
                    )
                )

    @classmethod
    def create_single_order_line(
        cls,
        order_line_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        object_storage,
        order_input: dict[str, Any],
        index: int,
    ) -> Optional[OrderBulkOrderLine]:
        variant = cls.get_instance_with_errors(
            input=order_line_input,
            errors=order_data.errors,
            model=ProductVariant,
            key_map={
                "variant_id": "id",
                "variant_external_reference": "external_reference",
                "variant_sku": "sku",
            },
            object_storage=object_storage,
            path=f"lines.{index}",
        )
        if variant is None and not order_line_input.get("product_name"):
            order_data.errors.append(
                OrderBulkError(
                    message=(
                        "Order line input must contain product name when"
                        " no variant provided."
                    ),
                    path=f"lines.{index}",
                    code=OrderBulkCreateErrorCode.REQUIRED,
                )
            )
            return None

        warehouse = cls.get_instance_with_errors(
            input=order_line_input,
            errors=order_data.errors,
            model=Warehouse,
            key_map={"warehouse": "id"},
            object_storage=object_storage,
            path=f"lines.{index}",
        )
        if not warehouse:
            return None

        line_tax_class = cls.get_instance_with_errors(
            input=order_line_input,
            errors=order_data.errors,
            model=TaxClass,
            key_map={"tax_class_id": "id"},
            object_storage=object_storage,
            path=f"lines.{index}",
        )
        line_amounts = cls.make_order_line_calculations(
            order_line_input, order_data, order_input["currency"], index
        )
        if not line_amounts:
            return None

        if not cls.is_datetime_valid(order_line_input["created_at"]):
            order_data.errors.append(
                OrderBulkError(
                    message="Order line input contains future date.",
                    path=f"lines.{index}.created_at",
                    code=OrderBulkCreateErrorCode.FUTURE_DATE,
                )
            )

        order_line = OrderLine(
            order=order_data.order,
            variant=variant,
            product_name=order_line_input.get("product_name") or variant.product.name,
            variant_name=order_line_input.get("variant_name")
            or (variant.name if variant else ""),
            translated_product_name=order_line_input.get("translated_product_name")
            or "",
            translated_variant_name=order_line_input.get("translated_variant_name")
            or "",
            product_variant_id=(variant.get_global_id() if variant else None),
            created_at=order_line_input["created_at"],
            is_shipping_required=order_line_input["is_shipping_required"],
            is_gift_card=order_line_input["is_gift_card"],
            currency=order_input["currency"],
            quantity=line_amounts.quantity,
            unit_price_net_amount=line_amounts.unit_net,
            unit_price_gross_amount=line_amounts.unit_gross,
            total_price_net_amount=line_amounts.total_net,
            total_price_gross_amount=line_amounts.total_gross,
            undiscounted_unit_price_net_amount=line_amounts.undiscounted_unit_net,
            undiscounted_unit_price_gross_amount=line_amounts.undiscounted_unit_gross,
            undiscounted_total_price_net_amount=line_amounts.undiscounted_total_net,
            undiscounted_total_price_gross_amount=line_amounts.undiscounted_total_gross,
            unit_discount_amount=line_amounts.unit_discount_amount,
            tax_rate=line_amounts.tax_rate,
            tax_class=line_tax_class,
            tax_class_name=order_line_input.get("tax_class_name"),
        )

        if metadata := order_line_input.get("metadata"):
            cls.process_metadata(
                metadata=metadata,
                errors=order_data.errors,
                path=f"lines.{index}.metadata",
                field=order_line.metadata,
            )
        if private_metadata := order_line_input.get("private_metadata"):
            cls.process_metadata(
                metadata=private_metadata,
                errors=order_data.errors,
                path=f"lines.{index}.private_metadata",
                field=order_line.private_metadata,
            )
        if tax_class_metadata := order_line_input.get("tax_class_metadata"):
            cls.process_metadata(
                metadata=tax_class_metadata,
                errors=order_data.errors,
                path=f"lines.{index}.tax_class_metadata",
                field=order_line.tax_class_metadata,
            )
        if tax_class_private_metadata := order_line_input.get(
            "tax_class_private_metadata"
        ):
            cls.process_metadata(
                metadata=tax_class_private_metadata,
                errors=order_data.errors,
                path=f"lines.{index}.tax_class_private_metadata",
                field=order_line.tax_class_private_metadata,
            )

        return OrderBulkOrderLine(line=order_line, warehouse=warehouse)

    @classmethod
    def create_single_fulfillment(
        cls,
        fulfillment_input: dict[str, Any],
        order_lines: list[OrderBulkOrderLine],
        order_data: OrderBulkCreateData,
        object_storage: dict[str, Any],
        index: int,
    ) -> Optional[OrderBulkFulfillment]:
        fulfillment = Fulfillment(
            order=order_data.order,
            status=FulfillmentStatus.FULFILLED,
            tracking_number=fulfillment_input.get("tracking_code") or "",
            fulfillment_order=1,
        )

        lines_input = fulfillment_input.get("lines") or []
        lines: list[OrderBulkFulfillmentLine] = []
        line_index = 0
        for line_input in lines_input:
            path = f"fulfillments.{index}.lines.{line_index}"
            variant = cls.get_instance_with_errors(
                input=line_input,
                errors=order_data.errors,
                model=ProductVariant,
                key_map={
                    "variant_id": "id",
                    "variant_external_reference": "external_reference",
                    "variant_sku": "sku",
                },
                object_storage=object_storage,
                path=path,
            )

            warehouse = cls.get_instance_with_errors(
                input=line_input,
                errors=order_data.errors,
                model=Warehouse,
                key_map={"warehouse": "id"},
                object_storage=object_storage,
                path=path,
            )
            if not warehouse:
                return None

            order_line_index = line_input["order_line_index"]
            if order_line_index < 0:
                order_data.errors.append(
                    OrderBulkError(
                        message="Order line index can't be negative.",
                        path=f"{path}.order_line_index",
                        code=OrderBulkCreateErrorCode.NEGATIVE_INDEX,
                    )
                )
                return None

            try:
                order_line = order_lines[order_line_index]
            except IndexError:
                order_data.errors.append(
                    OrderBulkError(
                        message=f"There is no order line with index:"
                        f" {order_line_index}.",
                        path=f"{path}.order_line_index",
                        code=OrderBulkCreateErrorCode.NO_RELATED_ORDER_LINE,
                    )
                )
                return None

            if order_line.warehouse.id != warehouse.id:
                code = OrderBulkCreateErrorCode.ORDER_LINE_FULFILLMENT_LINE_MISMATCH
                order_data.errors.append(
                    OrderBulkError(
                        message="Fulfillment line's warehouse is different"
                        " then order line's warehouse.",
                        path=f"{path}.warehouse",
                        code=code,
                    )
                )
                return None

            line_variant_missmatch = (
                variant
                and order_line.line.variant
                and order_line.line.variant.id != variant.id
            )
            missing_only_variant = not variant and order_line.line.variant
            missing_only_line_variant = variant and not order_line.line.variant
            if (
                line_variant_missmatch
                or missing_only_variant
                or missing_only_line_variant
            ):
                code = OrderBulkCreateErrorCode.ORDER_LINE_FULFILLMENT_LINE_MISMATCH
                order_data.errors.append(
                    OrderBulkError(
                        message="Fulfillment line's product variant is different"
                        " then order line's product variant.",
                        path=f"{path}.variant_id",
                        code=code,
                    )
                )
                return None

            fulfillment_line = FulfillmentLine(
                fulfillment=fulfillment,
                order_line=order_line.line,
                quantity=line_input["quantity"],
            )
            lines.append(OrderBulkFulfillmentLine(fulfillment_line, warehouse))
            line_index += 1

        return OrderBulkFulfillment(fulfillment=fulfillment, lines=lines)

    @classmethod
    def create_notes(
        cls,
        order_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        object_storage: dict[str, Any],
    ):
        if notes_input := order_input.get("notes"):
            note_index = 0
            for note_input in notes_input:
                if note := cls.create_single_note(
                    note_input, order_data, object_storage, note_index
                ):
                    order_data.notes.append(note)
                note_index += 1

    @classmethod
    def create_invoices(
        cls,
        order_input: dict[str, Any],
        order_data: OrderBulkCreateData,
    ):
        if invoices_input := order_input.get("invoices"):
            invoice_index = 0
            for invoice_input in invoices_input:
                order_data.invoices.append(
                    cls.create_single_invoice(invoice_input, order_data, invoice_index)
                )
                invoice_index += 1

    @classmethod
    def create_transactions(
        cls,
        order_input: dict[str, Any],
        order_data: OrderBulkCreateData,
    ):
        transactions_input = order_input.get("transactions")
        if transactions_input and order_data.order:
            index = 0
            for transaction_input in transactions_input:
                cls.create_single_transaction(transaction_input, order_data, index)
                index += 1

    @classmethod
    def create_discounts(
        cls,
        order_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        order_amounts: OrderAmounts,
    ):
        if discounts_input := order_input.get("discounts"):
            discount_index = 0
            for discount_input in discounts_input:
                order_data.discounts.append(
                    cls.create_single_discount(
                        discount_input,
                        order_data,
                        order_amounts,
                        order_input["currency"],
                        discount_index,
                    )
                )
                discount_index += 1

    @classmethod
    def create_order_lines(
        cls,
        order_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        object_storage: dict[str, Any],
    ):
        order_lines_input = order_input["lines"]
        order_line_index = 0
        for order_line_input in order_lines_input:
            if order_line := cls.create_single_order_line(
                order_line_input,
                order_data,
                object_storage,
                order_input,
                order_line_index,
            ):
                order_data.lines.append(order_line)
            else:
                order_data.is_critical_error = True
            order_line_index += 1

    @classmethod
    def create_fulfillments(
        cls,
        order_input: dict[str, Any],
        order_data: OrderBulkCreateData,
        object_storage: dict[str, Any],
    ):
        if fulfillments_input := order_input.get("fulfillments"):
            fulfillment_index = 0
            for fulfillment_input in fulfillments_input:
                if fulfillment := cls.create_single_fulfillment(
                    fulfillment_input,
                    order_data.lines,
                    order_data,
                    object_storage,
                    fulfillment_index,
                ):
                    order_data.fulfillments.append(fulfillment)
                else:
                    order_data.is_critical_error = True
                fulfillment_index += 1

    @classmethod
    def create_single_order(
        cls,
        order_input,
        object_storage: dict[str, Any],
        info: ResolveInfo,
    ) -> OrderBulkCreateData:
        order_data = OrderBulkCreateData()
        cls.validate_order_input(order_input, order_data, object_storage)
        if order_data.is_critical_error:
            return order_data

        order_data.order = Order(currency=order_input["currency"])
        cls.get_instances_related_to_order(
            order_input=order_input,
            order_data=order_data,
            object_storage=object_storage,
            info=info,
        )

        is_shipping_required = cls.is_shipping_required(order_input)
        delivery_input = order_input.get("delivery_method") or {}
        delivery_method = cls.get_delivery_method(
            delivery_input=delivery_input,
            order_data=order_data,
            object_storage=object_storage,
            is_shipping_required=is_shipping_required,
        )
        if order_data.is_critical_error or not order_data.channel:
            order_data.order = None
            return order_data

        cls.create_order_lines(order_input, order_data, object_storage)
        if order_data.is_critical_error:
            order_data.order = None
            return order_data

        cls.create_fulfillments(order_input, order_data, object_storage)
        if order_data.is_critical_error:
            order_data.order = None
            return order_data

        order_amounts = cls.make_order_calculations(
            delivery_method,
            order_data,
            delivery_input,
            object_storage,
        )
        if order_data.is_critical_error:
            order_data.order = None
            return order_data

        cls.create_notes(order_input, order_data, object_storage)
        cls.create_transactions(order_input, order_data)
        cls.create_invoices(order_input, order_data)
        cls.create_discounts(order_input, order_data, order_amounts)
        cls.validate_order_status(order_input["status"], order_data)

        order_data.order.external_reference = order_input.get("external_reference")
        order_data.order.channel = order_data.channel
        order_data.order.created_at = order_input["created_at"]
        order_data.order.status = order_input["status"]
        order_data.order.user = order_data.user
        order_data.order.billing_address = order_data.billing_address
        order_data.order.shipping_address = order_data.shipping_address
        order_data.order.language_code = order_input["language_code"]
        order_data.order.user_email = (
            order_data.user.email
            if order_data.user
            else order_input["user"].get("email")
        ) or ""
        order_data.order.collection_point = delivery_method.warehouse
        order_data.order.collection_point_name = delivery_method.warehouse_name
        order_data.order.shipping_method = delivery_method.shipping_method
        order_data.order.shipping_method_name = delivery_method.shipping_method_name
        order_data.order.shipping_tax_class = delivery_method.shipping_tax_class
        order_data.order.shipping_tax_class_name = (
            delivery_method.shipping_tax_class_name
        )
        order_data.order.shipping_tax_rate = order_amounts.shipping_tax_rate
        order_data.order.shipping_price_gross_amount = (
            order_amounts.shipping_price_gross
        )
        order_data.order.shipping_price_net_amount = order_amounts.shipping_price_net
        order_data.order.base_shipping_price_amount = order_amounts.shipping_price_net
        order_data.order.total_gross_amount = order_amounts.total_gross
        order_data.order.undiscounted_total_gross_amount = (
            order_amounts.undiscounted_total_gross
        )
        order_data.order.total_net_amount = order_amounts.total_net
        order_data.order.undiscounted_total_net_amount = (
            order_amounts.undiscounted_total_net
        )
        order_data.order.customer_note = order_input.get("customer_note") or ""
        order_data.order.redirect_url = order_input.get("redirect_url")
        order_data.order.origin = OrderOrigin.BULK_CREATE
        order_data.order.weight = order_input.get("weight") or zero_weight()
        order_data.order.currency = order_input["currency"]
        order_data.order.should_refresh_prices = False
        if order_data.voucher_code:
            order_data.order.voucher_code = order_data.voucher_code.code
            order_data.order.voucher = order_data.voucher_code.voucher
        update_order_display_gross_prices(order_data.order)

        if metadata := order_input.get("metadata"):
            cls.process_metadata(
                metadata=metadata,
                errors=order_data.errors,
                path="metadata",
                field=order_data.order.metadata,
            )
        if private_metadata := order_input.get("private_metadata"):
            cls.process_metadata(
                metadata=private_metadata,
                errors=order_data.errors,
                path="private_metadata",
                field=order_data.order.private_metadata,
            )
        if shipping_metadata := delivery_method.shipping_tax_class_metadata:
            cls.process_metadata(
                metadata=shipping_metadata,
                errors=order_data.errors,
                path="delivery_method.shipping_tax_class_metadata",
                field=order_data.order.shipping_tax_class_metadata,
            )
        shipping_private_metadata = delivery_method.shipping_tax_class_private_metadata
        if shipping_private_metadata:
            cls.process_metadata(
                metadata=shipping_private_metadata,
                errors=order_data.errors,
                path="delivery_method.shipping_tax_class_private_metadata",
                field=order_data.order.shipping_tax_class_private_metadata,
            )

        return order_data

    @classmethod
    def handle_stocks(
        cls, orders_data: list[OrderBulkCreateData], stock_update_policy: str
    ) -> list[Stock]:
        variant_ids: list[int] = sum(
            [
                order_data.unique_variant_ids
                for order_data in orders_data
                if order_data.order
            ],
            [],
        )
        warehouse_ids: list[UUID] = sum(
            [
                order_data.unique_warehouse_ids
                for order_data in orders_data
                if order_data.order
            ],
            [],
        )
        stocks = Stock.objects.filter(
            warehouse__id__in=warehouse_ids, product_variant__id__in=variant_ids
        ).all()
        stocks_map: dict[str, Stock] = {
            f"{stock.product_variant_id}_{stock.warehouse_id}": stock
            for stock in stocks
        }

        for order_data in orders_data:
            # Create a copy of stocks. If full iteration over order lines
            # and fulfillments will not produce error, which disqualify whole order,
            # than replace the copy with original stocks.
            stocks_map_copy = copy.deepcopy(stocks_map)
            line_index = 0
            for line in order_data.lines:
                order_line = line.line
                variant_id = order_line.variant_id
                warehouse_id = line.warehouse.id
                quantity_to_fulfill = order_line.quantity
                quantity_fulfilled = (
                    order_data.orderline_quantityfulfilled_map.get(order_line.id) or 0
                )
                quantity_to_allocate = quantity_to_fulfill - quantity_fulfilled

                if quantity_to_allocate < 0:
                    order_data.errors.append(
                        OrderBulkError(
                            message=f"There is more fulfillments, than ordered quantity"
                            f" for order line with variant: {variant_id} and warehouse:"
                            f" {warehouse_id}",
                            path=f"lines.{line_index}",
                            code=OrderBulkCreateErrorCode.INVALID_QUANTITY,
                        )
                    )
                    order_data.is_critical_error = True
                    break

                stock = stocks_map_copy.get(f"{variant_id}_{warehouse_id}")
                if not stock:
                    order_data.errors.append(
                        OrderBulkError(
                            message=f"There is no stock for given product variant:"
                            f" {variant_id} and warehouse: "
                            f"{warehouse_id}.",
                            path=f"lines.{line_index}",
                            code=OrderBulkCreateErrorCode.NON_EXISTING_STOCK,
                        )
                    )
                    order_data.is_critical_error = True
                    break

                available_quantity = stock.quantity - stock.quantity_allocated
                if (
                    quantity_to_fulfill > available_quantity
                    and stock_update_policy != StockUpdatePolicy.FORCE
                ):
                    order_data.errors.append(
                        OrderBulkError(
                            message=f"Insufficient stock for product variant: "
                            f"{variant_id} and warehouse: "
                            f"{warehouse_id}.",
                            path=f"lines.{line_index}",
                            code=OrderBulkCreateErrorCode.INSUFFICIENT_STOCK,
                        )
                    )
                    order_data.is_critical_error = True

                stock.quantity_allocated += quantity_to_allocate

                fulfillment_lines: list[OrderBulkFulfillmentLine] = (
                    order_data.orderline_fulfillmentlines_map.get(order_line.id) or []
                )
                for fulfillment_line in fulfillment_lines:
                    stock.quantity -= fulfillment_line.line.quantity
                line_index += 1

            if not order_data.is_critical_error:
                stocks_map = stocks_map_copy

        return [stock for stock in stocks_map.values()]

    @classmethod
    def handle_error_policy(
        cls, orders_data: list[OrderBulkCreateData], error_policy: str
    ):
        errors = [error for order in orders_data for error in order.errors]
        if errors:
            for order_data in orders_data:
                if error_policy == ErrorPolicy.REJECT_EVERYTHING:
                    order_data.order = None
                elif error_policy == ErrorPolicy.REJECT_FAILED_ROWS:
                    if order_data.errors:
                        order_data.order = None
        return orders_data

    @classmethod
    def save_data(cls, orders_data: list[OrderBulkCreateData], stocks: list[Stock]):
        for order_data in orders_data:
            order_data.set_quantity_fulfilled()
            order_data.set_fulfillment_order()
            if order_data.is_critical_error:
                order_data.order = None

        addresses = []
        for order_data in orders_data:
            if order_data.order:
                if billing_address := order_data.order.billing_address:
                    addresses.append(billing_address)
                if shipping_address := order_data.order.shipping_address:
                    addresses.append(shipping_address)
        Address.objects.bulk_create(addresses)

        orders = [order_data.order for order_data in orders_data if order_data.order]
        Order.objects.bulk_create(orders)

        order_lines: list[OrderLine] = sum(
            [
                order_data.all_order_lines
                for order_data in orders_data
                if order_data.order
            ],
            [],
        )
        OrderLine.objects.bulk_create(order_lines)

        notes = [
            note
            for order_data in orders_data
            for note in order_data.notes
            if order_data.order
        ]
        OrderEvent.objects.bulk_create(notes)

        fulfillments = [
            fulfillment.fulfillment
            for order_data in orders_data
            for fulfillment in order_data.fulfillments
            if order_data.order
        ]
        Fulfillment.objects.bulk_create(fulfillments)
        for order_data in orders_data:
            order_data.set_fulfillment_id()
        fulfillment_lines: list[FulfillmentLine] = sum(
            [
                order_data.all_fulfillment_lines
                for order_data in orders_data
                if order_data.order
            ],
            [],
        )
        FulfillmentLine.objects.bulk_create(fulfillment_lines)

        Stock.objects.bulk_update(stocks, ["quantity"])

        transactions: list[TransactionItem] = sum(
            [
                order_data.all_transactions
                for order_data in orders_data
                if order_data.order
            ],
            [],
        )
        TransactionItem.objects.bulk_create(transactions)
        for order_data in orders_data:
            order_data.set_transaction_id()
        transaction_events: list[TransactionEvent] = sum(
            [
                order_data.all_transaction_events
                for order_data in orders_data
                if order_data.order
            ],
            [],
        )
        TransactionEvent.objects.bulk_create(transaction_events)

        invoices: list[Invoice] = sum(
            [order_data.all_invoices for order_data in orders_data if order_data.order],
            [],
        )
        Invoice.objects.bulk_create(invoices)

        discounts: list[OrderDiscount] = sum(
            [
                order_data.all_discounts
                for order_data in orders_data
                if order_data.order
            ],
            [],
        )
        OrderDiscount.objects.bulk_create(discounts)

        for order_data in orders_data:
            order_data.link_gift_cards()
            order_data.post_create_order_update()

        Order.objects.bulk_update(
            orders,
            [
                "total_charged_amount",
                "charge_status",
                "updated_at",
                "total_authorized_amount",
                "authorize_status",
                "search_vector",
            ],
        )

        return orders_data

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        orders_input = data["orders"]
        if len(orders_input) > MAX_ORDERS:
            error = OrderBulkError(
                message=f"Number of orders exceeds limit: {MAX_ORDERS}.",
                code=OrderBulkCreateErrorCode.BULK_LIMIT,
            )
            result = OrderBulkCreateResult(order=None, error=error)
            return OrderBulkCreate(count=0, results=result)

        orders_data: list[OrderBulkCreateData] = []
        with traced_atomic_transaction():
            # Create dictionary, which stores already resolved objects:
            #   - key for instances: "{model_name}.{key_name}.{key_value}"
            #   - key for shipping prices: "shipping_price.{shipping_method_id}"
            object_storage: dict[str, Any] = cls.get_all_instances(orders_input)
            for order_input in orders_input:
                orders_data.append(
                    cls.create_single_order(order_input, object_storage, info)
                )

            error_policy = data.get("error_policy") or ErrorPolicy.REJECT_EVERYTHING
            stock_update_policy = (
                data.get("stock_update_policy") or StockUpdatePolicy.UPDATE
            )
            stocks: list[Stock] = []

            cls.handle_error_policy(orders_data, error_policy)
            if stock_update_policy != StockUpdatePolicy.SKIP:
                stocks = cls.handle_stocks(orders_data, stock_update_policy)
            cls.save_data(orders_data, stocks)

            manager = get_plugin_manager_promise(info.context).get()
            if created_orders := [
                order_data.order for order_data in orders_data if order_data.order
            ]:
                cls.call_event(manager.order_bulk_created, created_orders)

            results = [
                OrderBulkCreateResult(order=order_data.order, errors=order_data.errors)
                for order_data in orders_data
            ]
            count = sum([order_data.order is not None for order_data in orders_data])
            return OrderBulkCreate(count=count, results=results)
