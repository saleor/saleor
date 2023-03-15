from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....account.models import Address, User
from ....app.models import App
from ....channel.models import Channel
from ....core.tracing import traced_atomic_transaction
from ....core.utils.url import validate_storefront_url
from ....core.weight import zero_weight
from ....order import OrderEvents, OrderOrigin
from ....order.error_codes import OrderBulkCreateErrorCode
from ....order.models import Order, OrderEvent, OrderLine
from ....order.utils import update_order_display_gross_prices
from ....permission.enums import OrderPermissions
from ....product.models import ProductVariant
from ....shipping.models import ShippingMethod, ShippingMethodChannelListing
from ....tax.models import TaxClass
from ....warehouse.models import Warehouse
from ...account.i18n import I18nMixin
from ...account.types import AddressInput
from ...core import ResolveInfo
from ...core.enums import ErrorPolicy, ErrorPolicyEnum, LanguageCodeEnum
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal, WeightScalar
from ...core.types import NonNullList
from ...core.types.common import OrderBulkCreateError
from ...meta.mutations import MetadataInput
from ..mutations.order_discount_common import OrderDiscountCommonInput
from ..types import Order as OrderType
from .utils import get_instance

MINUTES_DIFF = 5
MAX_ORDERS = 50


@dataclass
class OrderBulkError:
    message: str
    code: Optional[OrderBulkCreateErrorCode] = None
    field: Optional[str] = None


@dataclass
class OrderLineWithErrors:
    line: Optional[OrderLine]
    errors: List[OrderBulkError]


@dataclass
class NoteWithErrors:
    note: Optional[OrderEvent]
    errors: List[OrderBulkError]


@dataclass
class OrderWithErrors:
    order: Optional[Order]
    errors: List[OrderBulkError]
    lines: List[OrderLineWithErrors]
    notes: List[NoteWithErrors]

    def get_all_errors(self) -> List[OrderBulkError]:
        return (
            self.errors
            + [error for line in self.lines for error in line.errors]
            + [error for note in self.notes for error in note.errors]
        )

    def get_all_lines(self) -> List[OrderLine]:
        return [line.line for line in self.lines if line.line and self.order]

    def get_all_notes(self) -> List[OrderEvent]:
        return [note.note for note in self.notes if note.note and self.order]


@dataclass
class OrderBulkStock:
    quantity: int
    warehouse: Warehouse


@dataclass
class DeliveryMethod:
    warehouse: Optional[Warehouse]
    shipping_method: Optional[ShippingMethod]
    shipping_tax_class: Optional[TaxClass]


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


class OrderBulkCreateNoteInput(graphene.InputObjectType):
    message = graphene.String(required=True, description="Note message.")
    date = graphene.DateTime(description="The date associated with the message.")
    user_id = graphene.ID(description="The user ID associated with the message.")
    user_email = graphene.ID(description="The user email associated with the message.")
    user_external_reference = graphene.ID(
        description="The user external ID associated with the message."
    )
    app_id = graphene.ID(description="The app ID associated with the message.")


class OrderBulkCreateFulfillStockInput(graphene.InputObjectType):
    quantity = graphene.Int(
        description="The number of line items to be fulfilled from given warehouse.",
        required=True,
    )
    warehouse_id = graphene.ID(
        description="ID of the warehouse from which the item will be fulfilled.",
    )
    warehouse_name = graphene.String(
        description="Name of the warehouse from which the item will be fulfilled.",
    )


class OrderBulkCreateFulfillmentLineInput(graphene.InputObjectType):
    variant_id = graphene.ID(description="The ID of the product variant.")
    variant_sku = graphene.String(description="The sku of the product variant.")
    variant_external_reference = graphene.String(
        description="The external ID of the product variant."
    )
    stocks = NonNullList(
        OrderBulkCreateFulfillStockInput, description="List of stock items."
    )


class OrderBulkCreateFulfillmentInput(graphene.InputObjectType):
    trackingCode = graphene.String(description="Fulfillments tracking code.")
    lines = NonNullList(
        OrderBulkCreateFulfillmentLineInput,
        description="List of items informing how to fulfill the order.",
    )


class OrderBulkCreateOrderLineInput(graphene.InputObjectType):
    variant_id = graphene.ID(description="The ID of the product variant.")
    variant_sku = graphene.String(description="The sku of the product variant.")
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
    quantity_fulfilled = graphene.Int(
        required=True,
        description="Number of items in the order line, "
        "which have been already fulfilled.",
    )
    total_price = graphene.Field(
        TaxedMoneyInput, required=True, description="Price of the order line."
    )
    undiscounted_total_price = graphene.Field(
        TaxedMoneyInput,
        required=True,
        description="Price of the order line excluding applied discount.",
    )
    # TODO is line tax rate needed if we have total gross and net required ?
    tax_rate = graphene.Float(required=True, description="Tax rate of the order line.")
    tax_class_id = graphene.ID(description="The ID of the tax class.")
    tax_class_name = graphene.String(description="The name of the tax class.")


class OrderBulkCreateInput(graphene.InputObjectType):
    number = graphene.Int(description="Unique number of the order.")
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
    # TODO fulfillments
    # TODO invoices = [OrderBulkCreateInvoiceInput!]
    # TODO transactions: [TransactionCreateInput!]!
    # TODO discounts (? need to be added/calculated if any ?)


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
            description="Input list of orders to create.",
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.value,
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
            ),
        )

    class Meta:
        description = "Creates multiple orders."
        permissions = (OrderPermissions.MANAGE_ORDERS_IMPORT,)
        error_type_class = OrderBulkCreateError
        error_type_field = "bulk_order_errors"

    @classmethod
    def is_datetime_valid(cls, date: datetime) -> bool:
        return date < timezone.now() + timedelta(minutes=MINUTES_DIFF)

    @classmethod
    def validate_order_input(cls, order_input, errors: List[OrderBulkError]):
        weight = order_input.get("weight")
        if weight and weight.value < 0:
            errors.append(
                OrderBulkError(
                    message="Product can't have negative weight.",
                    field="weight",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )

        date = order_input.get("created_at")
        if date and not cls.is_datetime_valid(date):
            errors.append(
                OrderBulkError(
                    message="Order input contains future date.",
                    field="createdAt",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )

        if redirect_url := order_input.get("redirect_url"):
            try:
                validate_storefront_url(redirect_url)
            except ValidationError as err:
                errors.append(
                    OrderBulkError(
                        message=f"Invalid redirect url: {err.message}.",
                        field="redirectUrl",
                        code=OrderBulkCreateErrorCode.INVALID,
                    )
                )

        # TODO validate status (wait for fulfillments)
        # TODO validate number (?)
        # TODO validate zones for warehouse
        # TODO tracking code
        return errors

    @classmethod
    def get_instance_and_errors(
        cls,
        input: Dict[str, Any],
        model,
        key_map: Dict[str, str],
        errors: List[OrderBulkError],
        instance_storage: Dict[str, Any],
    ):
        """Resolve instance based on input data, model and `key_map` argument provided.

        Args:
            input: data from input
            model: database model associated with searched instance
            key_map: mapping between keys from input and keys from database
            errors: error list to be updated if an error occur
            instance_storage: dict with key pattern: {model_name}_{key_name}_{key_value}
                              and instances as values; it is used to search for already
                              resolved instances

        Return:
            model instance and error list.

        """
        instance = None
        try:
            instance = get_instance(input, model, key_map, instance_storage)
        except ValidationError as err:
            errors.append(OrderBulkError(message=str(err.message)))
        return instance, errors

    @classmethod
    def get_instances_related_to_order(
        cls,
        order_input: Dict[str, Any],
        errors: List[OrderBulkError],
        instance_storage: Dict[str, Any],
    ) -> Tuple[Optional[InstancesRelatedToOrder], List[OrderBulkError]]:
        """Get all instances of objects needed to create an order."""

        user, errors = cls.get_instance_and_errors(
            input=order_input["user"],
            errors=errors,
            model=User,
            key_map={
                "id": "id",
                "email": "email",
                "external_reference": "external_reference",
            },
            instance_storage=instance_storage,
        )

        channel, errors = cls.get_instance_and_errors(
            input=order_input,
            errors=errors,
            model=Channel,
            key_map={"channel": "slug"},
            instance_storage=instance_storage,
        )

        billing_address: Optional[Address] = None
        billing_address_input = order_input["billing_address"]
        try:
            billing_address = cls.validate_address(billing_address_input)
        except Exception:
            errors.append(
                OrderBulkError(
                    message="Invalid billing address.",
                    field="billingAddress",
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
                        field="shippingAddress",
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

        return instances, errors

    @classmethod
    def make_order_calculations(
        cls,
        delivery_method: DeliveryMethod,
        order_lines: List[OrderLine],
        channel: Channel,
        delivery_input: Dict[str, Any],
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
                # TODO discuss if it make sense to get it from database
                db_price_amount = (
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

        # calculate lines
        order_total_gross_amount = Decimal(
            sum((line.total_price_gross_amount for line in order_lines))
        )
        order_undiscounted_total_gross_amount = Decimal(order_total_gross_amount)
        order_total_net_amount = Decimal(
            sum((line.total_price_net_amount for line in order_lines))
        )
        order_undiscounted_total_net_amount = Decimal(order_total_net_amount)

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
        cls, input: Dict[str, Any], errors: List[OrderBulkError], instance_storage
    ) -> Tuple[Optional[DeliveryMethod], List[OrderBulkError]]:
        warehouse, shipping_method, shipping_tax_class = None, None, None

        is_warehouse_delivery = input.get("warehouse_id")
        is_shipping_delivery = input.get("shipping_method_id")

        if is_warehouse_delivery and is_shipping_delivery:
            errors.append(
                OrderBulkError(
                    message="Can't provide both warehouse and shipping method IDs "
                    "in deliveryMethod field.",
                    field="deliveryMethod",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )

        if is_warehouse_delivery:
            warehouse, errors = cls.get_instance_and_errors(
                input=input,
                errors=errors,
                model=Warehouse,
                key_map={"warehouse_id": "id"},
                instance_storage=instance_storage,
            )

        if is_shipping_delivery:
            shipping_method, errors = cls.get_instance_and_errors(
                input=input,
                errors=errors,
                model=ShippingMethod,
                key_map={"shipping_method_id": "id"},
                instance_storage=instance_storage,
            )
            shipping_tax_class, errors = cls.get_instance_and_errors(
                input=input,
                errors=errors,
                model=TaxClass,
                key_map={"shipping_tax_class_id": "id"},
                instance_storage=instance_storage,
            )

        delivery_method = None
        if not warehouse and not shipping_method:
            errors.append(
                OrderBulkError(
                    message="No delivery method provided.",
                    field="deliveryMethod",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )
        else:
            delivery_method = DeliveryMethod(
                warehouse=warehouse,
                shipping_method=shipping_method,
                shipping_tax_class=shipping_tax_class,
            )

        return delivery_method, errors

    @classmethod
    def create_single_note(
        cls, note_input, order: Order, instance_storage: Dict[str, Any]
    ) -> NoteWithErrors:
        errors: List[OrderBulkError] = []
        date = note_input.get("date")
        if date and not cls.is_datetime_valid(date):
            errors.append(
                OrderBulkError(
                    message="Note input contains future date.",
                    field="date",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )
            date = None

        user, app = None, None
        user_key_map = {
            "user_id": "id",
            "user_email": "email",
            "user_external_reference": "external_reference",
        }
        if any([note_input.get(key) for key in user_key_map.keys()]):
            user, errors = cls.get_instance_and_errors(
                input=note_input,
                errors=errors,
                model=User,
                key_map=user_key_map,
                instance_storage=instance_storage,
            )

        if note_input.get("app_id"):
            app, errors = cls.get_instance_and_errors(
                input=note_input,
                errors=errors,
                model=App,
                key_map={"app_id": "id"},
                instance_storage=instance_storage,
            )

        if user and app:
            user, app = None, None
            errors.append(
                OrderBulkError(message="Note input contains both userId and appId.")
            )

        event = OrderEvent(
            date=date,
            type=OrderEvents.NOTE_ADDED,
            order=order,
            parameters={"message": note_input["message"]},
            user=user,
            app=app,
        )

        return NoteWithErrors(note=event, errors=errors)

    @classmethod
    def create_single_order_line(
        cls,
        order_line_input: Dict[str, Any],
        order: Order,
        instance_storage,
        order_input: Dict[str, Any],
    ) -> OrderLineWithErrors:
        errors: List[OrderBulkError] = []

        variant, errors = cls.get_instance_and_errors(
            input=order_line_input,
            errors=errors,
            model=ProductVariant,
            key_map={
                "variant_id": "id",
                "variant_external_reference": "external_reference",
                "variant_sku": "sku",
            },
            instance_storage=instance_storage,
        )

        line_tax_class, errors = cls.get_instance_and_errors(
            input=order_line_input,
            errors=errors,
            model=TaxClass,
            key_map={"tax_class_id": "id"},
            instance_storage=instance_storage,
        )

        if not all([variant, line_tax_class]):
            return OrderLineWithErrors(line=None, errors=errors)

        order_line_gross_amount = order_line_input["total_price"]["gross"]
        order_line_net_amount = order_line_input["total_price"]["net"]
        order_line_quantity = order_line_input["quantity"]

        order_line_unit_price_net_amount = Decimal(
            order_line_net_amount / order_line_quantity
        )
        order_line_unit_price_gross_amount = Decimal(
            order_line_gross_amount / order_line_quantity
        )

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
            quantity=order_line_quantity,
            quantity_fulfilled=order_line_input["quantity_fulfilled"],
            currency=order_input["currency"],
            unit_price_net_amount=order_line_unit_price_net_amount,
            unit_price_gross_amount=order_line_unit_price_gross_amount,
            total_price_net_amount=order_line_net_amount,
            total_price_gross_amount=order_line_gross_amount,
            tax_rate=Decimal(order_line_input["tax_rate"]),
            tax_class=line_tax_class,
            tax_class_name=order_line_input.get("tax_class_name", line_tax_class.name),
        )

        return OrderLineWithErrors(line=order_line, errors=errors)

    @classmethod
    def create_single_order(
        cls, order_input, instance_storage: Dict[str, Any]
    ) -> OrderWithErrors:
        errors: List[OrderBulkError] = []
        cls.validate_order_input(order_input, errors)
        order = Order()

        # get order related instances
        instances, errors = cls.get_instances_related_to_order(
            order_input=order_input,
            errors=errors,
            instance_storage=instance_storage,
        )
        delivery_input = order_input["delivery_method"]
        delivery_method, errors = cls.get_delivery_method(
            input=delivery_input,
            errors=errors,
            instance_storage=instance_storage,
        )
        if not instances or not delivery_method:
            return OrderWithErrors(order=None, errors=errors, lines=[], notes=[])

        # create lines
        order_lines_input = order_input["lines"]
        order_lines_with_errors: List[OrderLineWithErrors] = []
        for order_line_input in order_lines_input:
            order_lines_with_errors.append(
                cls.create_single_order_line(
                    order_line_input, order, instance_storage, order_input
                )
            )

        if not all([line.line for line in order_lines_with_errors]):
            errors.append(
                OrderBulkError(
                    message="At least one order line can't be created.",
                    field="lines",
                    code=OrderBulkCreateErrorCode.INVALID,
                )
            )
            return OrderWithErrors(
                order=None, errors=errors, lines=order_lines_with_errors, notes=[]
            )
        # TODO check if multiple order lines contains the same variant

        # calculate order amounts
        order_lines: List[OrderLine] = [
            line.line for line in order_lines_with_errors if line.line is not None
        ]
        order_amounts = cls.make_order_calculations(
            delivery_method, order_lines, instances.channel, delivery_input
        )

        # create notes
        notes_with_errors: List[NoteWithErrors] = []
        if notes_input := order_input.get("notes"):
            for note_input in notes_input:
                notes_with_errors.append(
                    cls.create_single_note(note_input, order, instance_storage)
                )

        # order.number = order_input.get("number")
        order.external_reference = order_input.get("external_reference")
        order.channel = instances.channel
        order.created_at = order_input["created_at"]
        order.status = order_input["status"]
        order.user = instances.user
        order.billing_address = instances.billing_address
        order.shipping_address = instances.shipping_address
        order.language_code = order_input["language_code"]
        order.user_email = instances.user.email
        order.collection_point = delivery_method.warehouse
        order.collection_point_name = delivery_input.get("warehouse_name") or getattr(
            delivery_method.warehouse, "name", None
        )
        order.shipping_method = delivery_method.shipping_method
        order.shipping_method_name = delivery_input.get(
            "shipping_method_name"
        ) or getattr(delivery_method.shipping_method, "name", None)
        order.shipping_tax_class = delivery_method.shipping_tax_class
        order.shipping_tax_class_name = delivery_input.get(
            "shipping_tax_class_name"
        ) or getattr(delivery_method.shipping_tax_class, "name", None)
        order.shipping_tax_rate = order_amounts.shipping_tax_rate
        order.shipping_price_gross_amount = order_amounts.shipping_price_gross
        order.shipping_price_net_amount = order_amounts.shipping_price_net
        order.total_gross_amount = order_amounts.total_gross
        order.undiscounted_total_gross_amount = order_amounts.undiscounted_total_gross
        order.total_net_amount = order_amounts.total_net
        order.undiscounted_total_net_amount = order_amounts.undiscounted_total_net
        order.customer_note = order_input.get("customer_note", "")
        order.redirect_url = order_input.get("redirect_url")
        order.origin = OrderOrigin.BULK_CREATE
        order.weight = order_input.get("weight", zero_weight())
        order.tracking_client_id = order_input.get("tracking_client_id")
        order.currency = order_input["currency"]
        order.should_refresh_prices = False
        update_order_display_gross_prices(order)
        # TODO charged
        # TODO authourized
        # TODO voucher
        # TODO gift cards

        return OrderWithErrors(
            order=order,
            errors=errors,
            lines=order_lines_with_errors,
            notes=notes_with_errors,
        )

    @classmethod
    def handle_error_policy(
        cls,
        orders_with_errors: List[OrderWithErrors],
        policy: ErrorPolicy,
    ):
        errors = [
            error for order in orders_with_errors for error in order.get_all_errors()
        ]
        if errors:
            for order in orders_with_errors:
                if policy == ErrorPolicy.REJECT_EVERYTHING:
                    order.order = None
                elif policy == ErrorPolicy.REJECT_FAILED_ROWS:
                    if order.get_all_errors():
                        order.order = None
        return orders_with_errors

    @classmethod
    @traced_atomic_transaction()
    def save_data(cls, orders_with_errors: List[OrderWithErrors]):
        addresses = []
        for order in orders_with_errors:
            if order.order:
                if billing_address := order.order.billing_address:
                    addresses.append(billing_address)
                if shipping_address := order.order.shipping_address:
                    addresses.append(shipping_address)
        Address.objects.bulk_create(addresses)

        Order.objects.bulk_create(
            [order.order for order in orders_with_errors if order.order]
        )

        order_lines = [
            line for order in orders_with_errors for line in order.get_all_lines()
        ]
        OrderLine.objects.bulk_create(order_lines)

        notes = [note for order in orders_with_errors for note in order.get_all_notes()]
        OrderEvent.objects.bulk_create(notes)

        return orders_with_errors

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /, **data):
        # TODO post save actions
        # TODO add webhook ORDER_BULK_CREATED
        # TODO handle tax class matedata, is needed ?
        # TODO error codes

        orders_input = data["orders"]
        if len(orders_input) > MAX_ORDERS:
            error = OrderBulkError(f"Number of orders exeeds limit: {MAX_ORDERS}.")
            result = OrderBulkCreateResult(order=None, error=error)
            return OrderBulkCreate(count=0, results=result)

        orders_with_errors: List[OrderWithErrors] = []
        instance_storage: Dict[str, Any] = {}
        for order_input in orders_input:
            orders_with_errors.append(
                cls.create_single_order(order_input, instance_storage)
            )

        cls.handle_error_policy(orders_with_errors, data["error_policy"])
        cls.save_data(orders_with_errors)

        results = [
            OrderBulkCreateResult(order=order.order, errors=order.get_all_errors())
            for order in orders_with_errors
        ]
        count = sum([order.order is not None for order in orders_with_errors])
        return OrderBulkCreate(count=count, results=results)
