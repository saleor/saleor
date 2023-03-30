import copy
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....account.models import Address, User
from ....app.models import App
from ....channel.models import Channel
from ....core.prices import quantize_price
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....core.weight import zero_weight
from ....order import FulfillmentStatus, OrderEvents, OrderOrigin, StockUpdatePolicy
from ....order.error_codes import OrderBulkCreateErrorCode
from ....order.models import Fulfillment, FulfillmentLine, Order, OrderEvent, OrderLine
from ....order.utils import update_order_display_gross_prices
from ....permission.enums import OrderPermissions
from ....product.models import ProductVariant
from ....shipping.models import ShippingMethod, ShippingMethodChannelListing
from ....tax.models import TaxClass
from ....warehouse.models import Stock, Warehouse
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_313, PREVIEW_FEATURE
from ...core.enums import ErrorPolicy, ErrorPolicyEnum, LanguageCodeEnum
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal, WeightScalar
from ...core.types import NonNullList
from ...core.types.common import OrderBulkCreateError
from ...meta.mutations import MetadataInput
from ..enums import StockUpdatePolicyEnum
from ..mutations.order_discount_common import OrderDiscountCommonInput
from ..mutations.order_fulfill import OrderFulfillStockInput
from ..types import Order as OrderType
from .utils import get_instance

MINUTES_DIFF = 5
MAX_ORDERS = 50
MAX_NOTE_LENGTH = 200


@dataclass
class OrderBulkError:
    message: str
    code: Optional[OrderBulkCreateErrorCode] = None
    field: Optional[str] = None


@dataclass
class OrderBulkStock:
    quantity: int
    warehouse: Warehouse


@dataclass
class OrderBulkFulfillmentLine:
    line: FulfillmentLine
    stock: OrderBulkStock


@dataclass
class OrderBulkFulfillment:
    fulfillment: Fulfillment
    lines: List[OrderBulkFulfillmentLine]


@dataclass
class OrderBulkOrderLine:
    line: OrderLine
    warehouse: Warehouse


@dataclass
class OrderWithErrors:
    order: Optional[Order]
    order_errors: List[OrderBulkError]
    lines: List[OrderBulkOrderLine]
    lines_errors: List[OrderBulkError]
    notes: List[OrderEvent]
    notes_errors: List[OrderBulkError]
    fulfillments: List[OrderBulkFulfillment]
    fulfillments_errors: List[OrderBulkError]
    # error which ignores error policy and disqualify order
    is_critical_error: bool = False

    def __init__(self):
        super().__init__()
        self.order = None
        self.order_errors = []
        self.lines = []
        self.lines_errors = []
        self.notes = []
        self.notes_errors = []
        self.fulfillments = []
        self.fulfillments_errors = []

    def set_fulfillment_id(self):
        for fulfillment in self.fulfillments:
            for line in fulfillment.lines:
                line.line.fulfillment_id = fulfillment.fulfillment.id

    def set_quantity_fulfilled(self):
        map = self.orderline_quantityfulfilled_map
        for order_line in self.lines:
            order_line.line.quantity_fulfilled = map.get(order_line.line.id, 0)

    def set_fulfillment_order(self):
        order = 1
        for fulfillment in self.fulfillments:
            fulfillment.fulfillment.fulfillment_order = order
            order += 1

    @property
    def order_lines_duplicates(self) -> bool:
        keys = [
            f"{line.line.variant.id}_{line.warehouse.id}"
            for line in self.lines
            if line.line.variant
        ]
        return len(keys) != len(list(set(keys)))

    @property
    def all_errors(self) -> List[OrderBulkError]:
        return (
            self.order_errors
            + self.lines_errors
            + self.notes_errors
            + self.fulfillments_errors
        )

    @property
    def all_order_lines(self) -> List[OrderLine]:
        return [line.line for line in self.lines]

    @property
    def all_fulfillment_lines(self) -> List[FulfillmentLine]:
        return [
            line.line for fulfillment in self.fulfillments for line in fulfillment.lines
        ]

    @property
    def variantwarehouse_orderline_map(self) -> Dict[str, OrderLine]:
        return {
            f"{line.line.variant.id}_{line.warehouse.id}": line.line
            for line in self.lines
            if line.line.variant
        }

    @property
    def orderline_fulfillmentlines_map(
        self,
    ) -> Dict[UUID, List[OrderBulkFulfillmentLine]]:
        map: Dict[UUID, list] = defaultdict(list)
        for fulfillment in self.fulfillments:
            for line in fulfillment.lines:
                map[line.line.order_line.id].append(line)
        return map

    @property
    def orderline_quantityfulfilled_map(self) -> Dict[UUID, int]:
        map: Dict[UUID, int] = defaultdict(int)
        for (
            order_line,
            fulfillment_lines,
        ) in self.orderline_fulfillmentlines_map.items():
            map[order_line] = sum([line.stock.quantity for line in fulfillment_lines])
        return map

    @property
    def unique_variant_ids(self) -> List[int]:
        return list(
            set([line.line.variant.id for line in self.lines if line.line.variant])
        )

    @property
    def unique_warehouse_ids(self) -> List[UUID]:
        return list(set([line.warehouse.id for line in self.lines]))


@dataclass
class DeliveryMethod:
    warehouse: Optional[Warehouse]
    shipping_method: Optional[ShippingMethod]
    shipping_tax_class: Optional[TaxClass]
    shipping_tax_class_metadata: Optional[List[Dict[str, str]]]
    shipping_tax_class_private_metadata: Optional[List[Dict[str, str]]]


@dataclass
class InstancesRelatedToOrder:
    user: User
    billing_address: Address
    channel: Channel
    shipping_address: Optional[Address] = None


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
    quantity: int
    tax_rate: Decimal


class TaxedMoneyInput(graphene.InputObjectType):
    gross = PositiveDecimal(required=True, description="Gross value of an item.")
    net = PositiveDecimal(required=True, description="Net value of an item.")


class OrderBulkCreateUserInput(graphene.InputObjectType):
    id = graphene.ID(description="Customer ID associated with the order.")
    email = graphene.String(description="Customer email associated with the order.")
    external_reference = graphene.String(
        description="Customer external ID associated with the order."
    )


class OrderBulkCreateDeliveryMethodInput(graphene.InputObjectType):
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


class OrderBulkCreateNoteInput(graphene.InputObjectType):
    message = graphene.String(
        required=True, description=f"Note message. Max characters: {MAX_NOTE_LENGTH}."
    )
    date = graphene.DateTime(description="The date associated with the message.")
    user_id = graphene.ID(description="The user ID associated with the message.")
    user_email = graphene.ID(description="The user email associated with the message.")
    user_external_reference = graphene.ID(
        description="The user external ID associated with the message."
    )
    app_id = graphene.ID(description="The app ID associated with the message.")


class OrderBulkCreateFulfillmentLineInput(graphene.InputObjectType):
    variant_id = graphene.ID(description="The ID of the product variant.")
    variant_sku = graphene.String(description="The SKU of the product variant.")
    variant_external_reference = graphene.String(
        description="The external ID of the product variant."
    )
    stocks = NonNullList(OrderFulfillStockInput, description="List of stock items.")


class OrderBulkCreateFulfillmentInput(graphene.InputObjectType):
    tracking_code = graphene.String(description="Fulfillments tracking code.")
    lines = NonNullList(
        OrderBulkCreateFulfillmentLineInput,
        description="List of items informing how to fulfill the order.",
    )


class OrderBulkCreateOrderLineInput(graphene.InputObjectType):
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
    created_at = graphene.DateTime(
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
    tax_rate = PositiveDecimal(description="Tax rate of the order line.")
    tax_class_id = graphene.ID(description="The ID of the tax class.")
    tax_class_name = graphene.String(description="The name of the tax class.")
    tax_class_metadata = NonNullList(
        MetadataInput, description="Metadata of the tax class."
    )
    tax_class_private_metadata = NonNullList(
        MetadataInput, description="Private metadata of the tax class."
    )


class OrderBulkCreateInput(graphene.InputObjectType):
    number = graphene.String(description="Unique string identifier of the order.")
    external_reference = graphene.String(description="External ID of the order.")
    channel = graphene.String(
        required=True, description="Slug of the channel associated with the order."
    )
    created_at = graphene.DateTime(
        required=True,
        description="The date, when the order was inserted to Saleor database.",
    )
    status = graphene.String(description="Status of the order.")
    user = graphene.Field(
        OrderBulkCreateUserInput,
        required=True,
        description="Customer associated with the order.",
    )
    tracking_client_id = graphene.String(description="Tracking ID of the customer.")
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
        description="Determines whether checkout prices should include taxes, "
        "when displayed in a storefront.",
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
        required=True,
        description="The delivery method selected for this order.",
    )
    promo_codes = NonNullList(graphene.String, description="List of promo codes.")
    discounts = NonNullList(OrderDiscountCommonInput, description="List of discounts.")
    fulfillments = NonNullList(
        OrderBulkCreateFulfillmentInput, description="Fulfillments of the order."
    )


class OrderBulkCreateResult(graphene.ObjectType):
    order = graphene.Field(OrderType, description="Order data.")
    errors = NonNullList(
        OrderBulkCreateError,
        description="List of errors occurred on create attempt.",
    )


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
        description = "Creates multiple orders." + ADDED_IN_313 + PREVIEW_FEATURE
        permissions = (OrderPermissions.MANAGE_ORDERS_IMPORT,)
        error_type_class = OrderBulkCreateError

    @classmethod
    def is_datetime_valid(cls, date: datetime) -> bool:
        """We accept future time values with 5 minutes from current time.

        Some systems might have incorrect time that is in the future compared to Saleor.
        At the same time, we don't want to create orders that are too far in the future.
        """
        return date < timezone.now() + timedelta(minutes=MINUTES_DIFF)

    @classmethod
    def validate_order_input(cls, order_input, errors: List[OrderBulkError]):
        date = order_input.get("created_at")
        if date and not cls.is_datetime_valid(date):
            errors.append(
                OrderBulkError(
                    message="Order input contains future date.",
                    field="created_at",
                    code=OrderBulkCreateErrorCode.FUTURE_DATE,
                )
            )

        if redirect_url := order_input.get("redirect_url"):
            try:
                validate_storefront_url(redirect_url)
            except ValidationError as err:
                errors.append(
                    OrderBulkError(
                        message=f"Invalid redirect url: {err.message}.",
                        field="redirect_url",
                        code=OrderBulkCreateErrorCode.INVALID,
                    )
                )

        # TODO validate status (wait for fulfillments)
        # TODO validate number (?)
        # TODO validate zones for warehouse (?)
        # TODO validate shipping method if available (?)
        return errors

    @classmethod
    def get_instance_with_errors(
        cls,
        input: Dict[str, Any],
        model,
        key_map: Dict[str, str],
        errors: List[OrderBulkError],
        object_storage: Dict[str, Any],
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

        Return:
            model instance and error list.

        """
        instance = None
        try:
            instance = get_instance(
                input, model, key_map, object_storage, OrderBulkCreateErrorCode
            )
        except ValidationError as err:
            errors.append(
                OrderBulkError(
                    message=str(err.message),
                    code=OrderBulkCreateErrorCode(err.code),
                )
            )
        return instance

    @classmethod
    def get_instances_related_to_order(
        cls,
        order_input: Dict[str, Any],
        errors: List[OrderBulkError],
        object_storage: Dict[str, Any],
    ) -> Optional[InstancesRelatedToOrder]:
        """Get all instances of objects needed to create an order."""

        user = cls.get_instance_with_errors(
            input=order_input["user"],
            errors=errors,
            model=User,
            key_map={
                "id": "id",
                "email": "email",
                "external_reference": "external_reference",
            },
            object_storage=object_storage,
        )

        channel = cls.get_instance_with_errors(
            input=order_input,
            errors=errors,
            model=Channel,
            key_map={"channel": "slug"},
            object_storage=object_storage,
        )

        billing_address: Optional[Address] = None
        billing_address_input = order_input["billing_address"]
        try:
            billing_address = cls.validate_address(billing_address_input)
        except Exception:
            errors.append(
                OrderBulkError(
                    message="Invalid billing address.",
                    field="billing_address",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )

        shipping_address: Optional[Address] = None
        if shipping_address_input := order_input.get("shipping_address"):
            try:
                shipping_address = cls.validate_address(shipping_address_input)
            except Exception:
                errors.append(
                    OrderBulkError(
                        message="Invalid shipping address.",
                        field="shipping_address",
                        code=OrderBulkCreateErrorCode.INVALID,
                    )
                )

        instances = None
        if user and billing_address and channel:
            instances = InstancesRelatedToOrder(
                user=user,
                billing_address=billing_address,
                shipping_address=shipping_address,
                channel=channel,
            )

        return instances

    @classmethod
    def make_order_line_calculations(
        cls, line_input: Dict[str, Any], errors: List[OrderBulkError], currency: str
    ) -> Optional[LineAmounts]:
        gross_amount = line_input["total_price"]["gross"]
        net_amount = line_input["total_price"]["net"]
        undiscounted_gross_amount = line_input["undiscounted_total_price"]["gross"]
        undiscounted_net_amount = line_input["undiscounted_total_price"]["net"]
        quantity = line_input["quantity"]
        tax_rate = line_input.get("tax_rate", None)

        is_exit_error = False
        if quantity < 1 or int(quantity) != quantity:
            errors.append(
                OrderBulkError(
                    message="Invalid quantity. "
                    "Must be integer greater then or equal to 1.",
                    field="quantity",
                    code=OrderBulkCreateErrorCode.INVALID_QUANTITY,
                )
            )
            is_exit_error = True
        if gross_amount < net_amount:
            errors.append(
                OrderBulkError(
                    message="Net price can't be greater then gross price.",
                    field="total_price",
                    code=OrderBulkCreateErrorCode.PRICE_ERROR,
                )
            )
            is_exit_error = True
        if undiscounted_gross_amount < undiscounted_net_amount:
            errors.append(
                OrderBulkError(
                    message="Net price can't be greater then gross price.",
                    field="undiscounted_total_price",
                    code=OrderBulkCreateErrorCode.PRICE_ERROR,
                )
            )
            is_exit_error = True

        if is_exit_error:
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

        if tax_rate is None and net_amount > 0:
            tax_rate = Decimal(gross_amount / net_amount - 1)

        return LineAmounts(
            total_gross=gross_amount,
            total_net=net_amount,
            unit_gross=unit_price_gross_amount,
            unit_net=unit_price_net_amount,
            undiscounted_total_gross=undiscounted_gross_amount,
            undiscounted_total_net=undiscounted_net_amount,
            undiscounted_unit_gross=undiscounted_unit_price_gross_amount,
            undiscounted_unit_net=undiscounted_unit_price_net_amount,
            quantity=quantity,
            tax_rate=tax_rate,
        )

    @classmethod
    def make_order_calculations(
        cls,
        delivery_method: DeliveryMethod,
        order_lines: List[OrderLine],
        channel: Channel,
        delivery_input: Dict[str, Any],
        object_storage: Dict[str, Any],
    ) -> OrderAmounts:
        """Calculate all order amount fields."""

        # calculate shipping amounts
        shipping_price_net_amount = Decimal(0)
        shipping_price_gross_amount = Decimal(0)
        shipping_price_tax_rate = Decimal(delivery_input.get("shipping_tax_rate", 0))

        if delivery_method.shipping_method:
            if shipping_price := delivery_input.get("shipping_price"):
                shipping_price_net_amount = Decimal(shipping_price.net)
                shipping_price_gross_amount = Decimal(shipping_price.gross)
                shipping_price_tax_rate = (
                    shipping_price_gross_amount / shipping_price_net_amount - 1
                )
            else:
                lookup_key = f"shipping_price_{delivery_method.shipping_method.id}"
                db_price_amount = object_storage.get(lookup_key) or (
                    ShippingMethodChannelListing.objects.values_list(
                        "price_amount", flat=True
                    )
                    .filter(
                        shipping_method_id=delivery_method.shipping_method.id,
                        channel_id=channel.id,
                    )
                    .first()
                )
                if db_price_amount:
                    shipping_price_net_amount = Decimal(db_price_amount)
                    shipping_price_gross_amount = Decimal(
                        shipping_price_net_amount * (1 + shipping_price_tax_rate)
                    )
                    object_storage[lookup_key] = db_price_amount

        # calculate lines
        order_total_gross_amount = Decimal(
            sum((line.total_price_gross_amount for line in order_lines))
        )
        order_undiscounted_total_gross_amount = Decimal(
            sum((line.undiscounted_total_price_gross_amount for line in order_lines))
        )
        order_total_net_amount = Decimal(
            sum((line.total_price_net_amount for line in order_lines))
        )
        order_undiscounted_total_net_amount = Decimal(
            sum((line.undiscounted_total_price_net_amount for line in order_lines))
        )

        return OrderAmounts(
            shipping_price_gross=shipping_price_gross_amount,
            shipping_price_net=shipping_price_net_amount,
            shipping_tax_rate=shipping_price_tax_rate,
            total_gross=order_total_gross_amount,
            total_net=order_total_net_amount,
            undiscounted_total_gross=order_undiscounted_total_gross_amount,
            undiscounted_total_net=order_undiscounted_total_net_amount,
        )

    @classmethod
    def get_delivery_method(
        cls, input: Dict[str, Any], errors: List[OrderBulkError], object_storage
    ) -> Optional[DeliveryMethod]:
        warehouse, shipping_method, shipping_tax_class = None, None, None
        shipping_tax_class_metadata, shipping_tax_class_private_metadata = None, None

        is_warehouse_delivery = input.get("warehouse_id")
        is_shipping_delivery = input.get("shipping_method_id")

        if is_warehouse_delivery and is_shipping_delivery:
            errors.append(
                OrderBulkError(
                    message="Can't provide both warehouse and shipping method IDs.",
                    field="delivery_method",
                    code=OrderBulkCreateErrorCode.TOO_MANY_IDENTIFIERS,
                )
            )

        if is_warehouse_delivery:
            warehouse = cls.get_instance_with_errors(
                input=input,
                errors=errors,
                model=Warehouse,
                key_map={"warehouse_id": "id"},
                object_storage=object_storage,
            )

        if is_shipping_delivery:
            shipping_method = cls.get_instance_with_errors(
                input=input,
                errors=errors,
                model=ShippingMethod,
                key_map={"shipping_method_id": "id"},
                object_storage=object_storage,
            )
            shipping_tax_class = cls.get_instance_with_errors(
                input=input,
                errors=errors,
                model=TaxClass,
                key_map={"shipping_tax_class_id": "id"},
                object_storage=object_storage,
            )
            shipping_tax_class_metadata = input.get("shipping_tax_class_metadata")
            shipping_tax_class_private_metadata = input.get(
                "shipping_tax_class_private_metadata"
            )

        delivery_method = None
        if not warehouse and not shipping_method:
            errors.append(
                OrderBulkError(
                    message="No delivery method provided.",
                    field="delivery_method",
                    code=OrderBulkCreateErrorCode.REQUIRED,
                )
            )
        else:
            delivery_method = DeliveryMethod(
                warehouse=warehouse,
                shipping_method=shipping_method,
                shipping_tax_class=shipping_tax_class,
                shipping_tax_class_metadata=shipping_tax_class_metadata,
                shipping_tax_class_private_metadata=shipping_tax_class_private_metadata,
            )

        return delivery_method

    @classmethod
    def create_single_note(
        cls,
        note_input,
        order: Order,
        object_storage: Dict[str, Any],
        errors: List[OrderBulkError],
    ) -> Optional[OrderEvent]:
        if len(note_input["message"]) > MAX_NOTE_LENGTH:
            errors.append(
                OrderBulkError(
                    message=f"Note message exceeds character limit: {MAX_NOTE_LENGTH}.",
                    field="message",
                    code=OrderBulkCreateErrorCode.NOTE_LENGTH,
                )
            )
            return None

        date = note_input.get("date")
        if date and not cls.is_datetime_valid(date):
            errors.append(
                OrderBulkError(
                    message="Note input contains future date.",
                    field="date",
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
                errors=errors,
                model=User,
                key_map=user_key_map,
                object_storage=object_storage,
            )

        if note_input.get("app_id"):
            app = cls.get_instance_with_errors(
                input=note_input,
                errors=errors,
                model=App,
                key_map={"app_id": "id"},
                object_storage=object_storage,
            )

        if user and app:
            user, app = None, None
            errors.append(
                OrderBulkError(
                    message="Note input contains both user and app identifier.",
                    code=OrderBulkCreateErrorCode.TOO_MANY_IDENTIFIERS,
                    field="notes",
                )
            )

        event = OrderEvent(
            date=date,
            type=OrderEvents.NOTE_ADDED,
            order=order,
            parameters={"message": note_input["message"]},
            user=user,
            app=app,
        )

        return event

    @classmethod
    def create_single_order_line(
        cls,
        order_line_input: Dict[str, Any],
        order: Order,
        object_storage,
        order_input: Dict[str, Any],
        errors: List[OrderBulkError],
    ) -> Optional[OrderBulkOrderLine]:
        variant = cls.get_instance_with_errors(
            input=order_line_input,
            errors=errors,
            model=ProductVariant,
            key_map={
                "variant_id": "id",
                "variant_external_reference": "external_reference",
                "variant_sku": "sku",
            },
            object_storage=object_storage,
        )
        if not variant:
            return None

        warehouse = cls.get_instance_with_errors(
            input=order_line_input,
            errors=errors,
            model=Warehouse,
            key_map={"warehouse": "id"},
            object_storage=object_storage,
        )
        if not warehouse:
            return None

        line_tax_class = cls.get_instance_with_errors(
            input=order_line_input,
            errors=errors,
            model=TaxClass,
            key_map={"tax_class_id": "id"},
            object_storage=object_storage,
        )
        tax_class_name = order_line_input.get(
            "tax_class_name", line_tax_class.name if line_tax_class else None
        )

        line_amounts = cls.make_order_line_calculations(
            order_line_input, errors, order_input["currency"]
        )
        if not line_amounts:
            return None

        order_line = OrderLine(
            order=order,
            variant=variant,
            product_name=order_line_input.get("product_name", ""),
            variant_name=order_line_input.get("variant_name", variant.name),
            translated_product_name=order_line_input.get("translated_product_name", ""),
            translated_variant_name=order_line_input.get("translated_variant_name", ""),
            product_variant_id=variant.get_global_id(),
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
            tax_rate=line_amounts.tax_rate,
            tax_class=line_tax_class,
            tax_class_name=tax_class_name,
        )

        if metadata := order_line_input.get("tax_class_metadata"):
            for data in metadata:
                order_line.tax_class_metadata.update({data["key"]: data["value"]})
        if private_metadata := order_line_input.get("tax_class_private_metadata"):
            for data in private_metadata:
                order_line.tax_class_private_metadata.update(
                    {data["key"]: data["value"]}
                )
        return OrderBulkOrderLine(line=order_line, warehouse=warehouse)

    @classmethod
    def create_single_fulfillment(
        cls,
        fulfillment_input: Dict[str, Any],
        order_lines_with_keys: Dict[str, OrderLine],
        order: Order,
        object_storage: Dict[str, Any],
        errors: List[OrderBulkError],
    ) -> Optional[OrderBulkFulfillment]:
        fulfillment = Fulfillment(
            order=order,
            status=FulfillmentStatus.FULFILLED,
            tracking_number=fulfillment_input.get("tracking_code", ""),
            fulfillment_order=1,
        )

        lines_input = fulfillment_input["lines"]
        lines: List[OrderBulkFulfillmentLine] = []
        for line_input in lines_input:
            variant = cls.get_instance_with_errors(
                input=line_input,
                errors=errors,
                model=ProductVariant,
                key_map={
                    "variant_id": "id",
                    "variant_external_reference": "external_reference",
                    "variant_sku": "sku",
                },
                object_storage=object_storage,
            )
            if not variant:
                return None

            for stock_input in line_input["stocks"]:
                warehouse = cls.get_instance_with_errors(
                    input=stock_input,
                    errors=errors,
                    model=Warehouse,
                    key_map={"warehouse": "id"},
                    object_storage=object_storage,
                )
                if not warehouse:
                    return None

                key = f"{variant.id}_{warehouse.id}"
                order_line = order_lines_with_keys.get(key)
                if not order_line:
                    errors.append(
                        OrderBulkError(
                            message=f"There is no related order line for given "
                            f"variant: {variant.id} and warehouse: "
                            f"{warehouse.id} in fulfillment line.",
                            field="fulfillment_line",
                            code=OrderBulkCreateErrorCode.NO_RELATED_ORDER_LINE,
                        )
                    )
                    return None

                stock = OrderBulkStock(
                    quantity=stock_input["quantity"], warehouse=warehouse
                )
                fulfillment_line = FulfillmentLine(
                    fulfillment=fulfillment,
                    order_line=order_line,
                    quantity=stock_input["quantity"],
                )
                lines.append(OrderBulkFulfillmentLine(fulfillment_line, stock))

        return OrderBulkFulfillment(fulfillment=fulfillment, lines=lines)

    @classmethod
    def create_single_order(
        cls, order_input, object_storage: Dict[str, Any]
    ) -> OrderWithErrors:
        order = OrderWithErrors()
        cls.validate_order_input(order_input, order.order_errors)
        order_instance = Order()

        # get order related instances
        instances = cls.get_instances_related_to_order(
            order_input=order_input,
            errors=order.order_errors,
            object_storage=object_storage,
        )
        delivery_input = order_input["delivery_method"]
        delivery_method = cls.get_delivery_method(
            input=delivery_input,
            errors=order.order_errors,
            object_storage=object_storage,
        )
        if not instances or not delivery_method:
            return order

        # create lines
        order_lines_input = order_input["lines"]
        for order_line_input in order_lines_input:
            if order_line := cls.create_single_order_line(
                order_line_input,
                order_instance,
                object_storage,
                order_input,
                order.lines_errors,
            ):
                order.lines.append(order_line)
            else:
                order.is_critical_error = True

        if order.is_critical_error:
            return order

        if order.order_lines_duplicates:
            order.order_errors.append(
                OrderBulkError(
                    message="Multiple order lines contain the same product variant "
                    "and warehouse.",
                    field="lines",
                    code=OrderBulkCreateErrorCode.DUPLICATED_INPUT_ITEM,
                )
            )
            return order

        # calculate order amounts
        order_amounts = cls.make_order_calculations(
            delivery_method,
            order.all_order_lines,
            instances.channel,
            delivery_input,
            object_storage,
        )

        # create notes
        if notes_input := order_input.get("notes"):
            for note_input in notes_input:
                if note := cls.create_single_note(
                    note_input, order_instance, object_storage, order.notes_errors
                ):
                    order.notes.append(note)

        # create fulfillments
        if fulfillments_input := order_input.get("fulfillments"):
            for fulfillment_input in fulfillments_input:
                if fulfillment := cls.create_single_fulfillment(
                    fulfillment_input,
                    order.variantwarehouse_orderline_map,
                    order_instance,
                    object_storage,
                    order.fulfillments_errors,
                ):
                    order.fulfillments.append(fulfillment)
                else:
                    order.is_critical_error = True
            if order.is_critical_error:
                return order

        order_instance.external_reference = order_input.get("external_reference")
        order_instance.channel = instances.channel
        order_instance.created_at = order_input["created_at"]
        order_instance.status = order_input["status"]
        order_instance.user = instances.user
        order_instance.billing_address = instances.billing_address
        order_instance.shipping_address = instances.shipping_address
        order_instance.language_code = order_input["language_code"]
        order_instance.user_email = instances.user.email
        order_instance.collection_point = delivery_method.warehouse
        order_instance.collection_point_name = delivery_input.get(
            "warehouse_name"
        ) or getattr(delivery_method.warehouse, "name", None)
        order_instance.shipping_method = delivery_method.shipping_method
        order_instance.shipping_method_name = delivery_input.get(
            "shipping_method_name"
        ) or getattr(delivery_method.shipping_method, "name", None)
        order_instance.shipping_tax_class = delivery_method.shipping_tax_class
        order_instance.shipping_tax_class_name = delivery_input.get(
            "shipping_tax_class_name"
        ) or getattr(delivery_method.shipping_tax_class, "name", None)
        order_instance.shipping_tax_rate = order_amounts.shipping_tax_rate
        order_instance.shipping_price_gross_amount = order_amounts.shipping_price_gross
        order_instance.shipping_price_net_amount = order_amounts.shipping_price_net
        order_instance.total_gross_amount = order_amounts.total_gross
        order_instance.undiscounted_total_gross_amount = (
            order_amounts.undiscounted_total_gross
        )
        order_instance.total_net_amount = order_amounts.total_net
        order_instance.undiscounted_total_net_amount = (
            order_amounts.undiscounted_total_net
        )
        order_instance.customer_note = order_input.get("customer_note", "")
        order_instance.redirect_url = order_input.get("redirect_url")
        order_instance.origin = OrderOrigin.BULK_CREATE
        order_instance.weight = order_input.get("weight", zero_weight())
        order_instance.tracking_client_id = order_input.get("tracking_client_id")
        order_instance.currency = order_input["currency"]
        order_instance.should_refresh_prices = False
        update_order_display_gross_prices(order_instance)

        if metadata := delivery_method.shipping_tax_class_metadata:
            for data in metadata:
                order_instance.shipping_tax_class_metadata.update(
                    {data["key"]: data["value"]}
                )
        if private_metadata := delivery_method.shipping_tax_class_private_metadata:
            for data in private_metadata:
                order_instance.shipping_tax_class_private_metadata.update(
                    {data["key"]: data["value"]}
                )

        order.order = order_instance
        return order

    @classmethod
    def handle_stocks(
        cls, orders: List[OrderWithErrors], stock_update_policy: str
    ) -> List[Stock]:
        variant_ids: List[int] = sum(
            [order.unique_variant_ids for order in orders if order.order], []
        )
        warehouse_ids: List[UUID] = sum(
            [order.unique_warehouse_ids for order in orders if order.order], []
        )
        stocks = Stock.objects.filter(
            warehouse__id__in=warehouse_ids, product_variant__id__in=variant_ids
        ).all()
        stocks_map: Dict[str, Stock] = {
            f"{stock.product_variant_id}_{stock.warehouse_id}": stock
            for stock in stocks
        }

        for order in orders:
            # Create a copy of stocks. If full iteration over order lines
            # and fulfillments will not produce error, which disqualify whole order,
            # than replace the copy with original stocks.
            stocks_map_copy = copy.deepcopy(stocks_map)
            for line in order.lines:
                order_line = line.line
                variant_id = order_line.variant_id
                warehouse_id_for_allocation = line.warehouse.id
                quantity_to_fulfill = order_line.quantity
                quantity_fulfilled = order.orderline_quantityfulfilled_map.get(
                    order_line.id, 0
                )
                quantity_to_allocate = quantity_to_fulfill - quantity_fulfilled

                # increase allocations
                if quantity_to_allocate < 0:
                    order.lines_errors.append(
                        OrderBulkError(
                            message=f"There is more fulfillments, than ordered quantity"
                            f" for order line with variant: {variant_id} and warehouse:"
                            f" {warehouse_id_for_allocation}",
                            field="order_line",
                            code=OrderBulkCreateErrorCode.INVALID_QUANTITY,
                        )
                    )
                    order.is_critical_error = True
                    break

                stock = stocks_map_copy.get(
                    f"{variant_id}_{warehouse_id_for_allocation}"
                )
                if not stock:
                    order.lines_errors.append(
                        OrderBulkError(
                            message=f"There is no stock for given product variant:"
                            f" {variant_id} and warehouse: "
                            f"{warehouse_id_for_allocation}.",
                            field="order_line",
                            code=OrderBulkCreateErrorCode.NON_EXISTING_STOCK,
                        )
                    )
                    order.is_critical_error = True
                    break

                available_quantity = stock.quantity - stock.quantity_allocated
                if (
                    quantity_to_allocate > available_quantity
                    and stock_update_policy != StockUpdatePolicy.FORCE
                ):
                    order.lines_errors.append(
                        OrderBulkError(
                            message=f"Insufficient stock for product variant: "
                            f"{variant_id} and warehouse: "
                            f"{warehouse_id_for_allocation}.",
                            field="order_line",
                            code=OrderBulkCreateErrorCode.INSUFFICIENT_STOCK,
                        )
                    )
                    order.is_critical_error = True

                stock.quantity_allocated += quantity_to_allocate

                # decrease quantity
                fulfillment_lines: List[
                    OrderBulkFulfillmentLine
                ] = order.orderline_fulfillmentlines_map.get(order_line.id, [])
                for fulfillment_line in fulfillment_lines:
                    warehouse_id_for_fulfillment = fulfillment_line.stock.warehouse.id
                    stock = stocks_map_copy.get(
                        f"{variant_id}_{warehouse_id_for_fulfillment}"
                    )
                    if not stock:
                        order.fulfillments_errors.append(
                            OrderBulkError(
                                message=f"There is no stock for given product variant:"
                                f" {variant_id} and warehouse: "
                                f"{warehouse_id_for_fulfillment}.",
                                field="fulfillment_line",
                                code=OrderBulkCreateErrorCode.NON_EXISTING_STOCK,
                            )
                        )
                        order.is_critical_error = True
                        break

                    fulfillment_line_quantity = fulfillment_line.line.quantity
                    stock.quantity -= fulfillment_line_quantity

            if not order.is_critical_error:
                stocks_map = stocks_map_copy

        return [stock for stock in stocks_map.values()]

    @classmethod
    def handle_error_policy(cls, orders: List[OrderWithErrors], error_policy: str):
        errors = [error for order in orders for error in order.all_errors]
        if errors:
            for order in orders:
                if error_policy == ErrorPolicy.REJECT_EVERYTHING:
                    order.order = None
                elif error_policy == ErrorPolicy.REJECT_FAILED_ROWS:
                    if order.all_errors:
                        order.order = None
        return orders

    @classmethod
    @traced_atomic_transaction()
    def save_data(cls, orders: List[OrderWithErrors], stocks: List[Stock]):
        for order in orders:
            order.set_quantity_fulfilled()
            order.set_fulfillment_order()
            if order.is_critical_error:
                order.order = None

        addresses = []
        for order in orders:
            if order.order:
                if billing_address := order.order.billing_address:
                    addresses.append(billing_address)
                if shipping_address := order.order.shipping_address:
                    addresses.append(shipping_address)
        Address.objects.bulk_create(addresses)

        Order.objects.bulk_create([order.order for order in orders if order.order])

        order_lines: List[OrderLine] = sum(
            [order.all_order_lines for order in orders if order.order], []
        )
        OrderLine.objects.bulk_create(order_lines)

        notes = [note for order in orders for note in order.notes if order.order]
        OrderEvent.objects.bulk_create(notes)

        fulfillments = [
            fulfillment.fulfillment
            for order in orders
            for fulfillment in order.fulfillments
            if order.order
        ]
        Fulfillment.objects.bulk_create(fulfillments)
        for order in orders:
            order.set_fulfillment_id()
        fulfillment_lines: List[FulfillmentLine] = sum(
            [order.all_fulfillment_lines for order in orders if order.order], []
        )
        FulfillmentLine.objects.bulk_create(fulfillment_lines)

        Stock.objects.bulk_update(stocks, ["quantity"])

        return orders

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /, **data):
        orders_input = data["orders"]
        if len(orders_input) > MAX_ORDERS:
            error = OrderBulkError(
                message=f"Number of orders exceeds limit: {MAX_ORDERS}.",
                code=OrderBulkCreateErrorCode.BULK_LIMIT,
            )
            result = OrderBulkCreateResult(order=None, error=error)
            return OrderBulkCreate(count=0, results=result)

        orders: List[OrderWithErrors] = []
        # Create dictionary, which stores already resolved objects:
        #   - key for instances: "{model_name}_{key_name}_{key_value}"
        #   - key for shipping prices: "shipping_price_{shipping_method_id}"
        object_storage: Dict[str, Any] = {}
        for order_input in orders_input:
            orders.append(cls.create_single_order(order_input, object_storage))

        error_policy = data.get("error_policy", ErrorPolicy.REJECT_EVERYTHING)
        stock_update_policy = data.get("stock_update_policy", StockUpdatePolicy.UPDATE)
        stocks: List[Stock] = []

        cls.handle_error_policy(orders, error_policy)
        if stock_update_policy != StockUpdatePolicy.SKIP:
            stocks = cls.handle_stocks(orders, stock_update_policy)
        cls.save_data(orders, stocks)

        results = [
            OrderBulkCreateResult(order=order.order, errors=order.all_errors)
            for order in orders
        ]
        count = sum([order.order is not None for order in orders])
        return OrderBulkCreate(count=count, results=results)
