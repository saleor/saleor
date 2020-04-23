from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.template.defaultfilters import pluralize

from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....order import models
from ....order.actions import (
    cancel_fulfillment,
    fulfill_order_line,
    fulfillment_tracking_updated,
    order_fulfilled,
)
from ....order.emails import send_fulfillment_update
from ....order.error_codes import OrderErrorCode
from ...core.mutations import BaseMutation
from ...core.types.common import OrderError
from ...core.utils import from_global_id_strict_type
from ...meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
from ...order.types import Fulfillment, Order
from ...utils import get_user_or_service_account_from_context
from ...warehouse.types import Warehouse
from ..types import OrderLine


class FulfillmentLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(
        description="The ID of the order line.", name="orderLineId"
    )
    quantity = graphene.Int(description="The number of line item(s) to be fulfilled.")


class FulfillmentCreateInput(graphene.InputObjectType):
    tracking_number = graphene.String(description="Fulfillment tracking number.")
    notify_customer = graphene.Boolean(
        description="If true, send an email notification to the customer."
    )
    lines = graphene.List(
        FulfillmentLineInput, required=True, description="Item line to be fulfilled."
    )


class OrderFulfillStockInput(graphene.InputObjectType):
    quantity = graphene.Int(
        description="The number of line item to be fulfilled from given warehouse."
    )
    warehouse = graphene.ID(
        description="ID of the warehouse from which item be fulfilled."
    )


class OrderFulfillLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(
        description="The ID of the order line.", name="orderLineId"
    )
    stocks = graphene.List(
        graphene.NonNull(OrderFulfillStockInput),
        required=True,
        description="Stocks from item line be fulfilled.",
    )


class OrderFulfillInput(graphene.InputObjectType):
    lines = graphene.List(
        graphene.NonNull(OrderFulfillLineInput),
        required=True,
        description="Item line to be fulfilled.",
    )
    notify_customer = graphene.Boolean(
        description="If true, send an email notification to the customer."
    )


class FulfillmentUpdateTrackingInput(graphene.InputObjectType):
    tracking_number = graphene.String(description="Fulfillment tracking number.")
    notify_customer = graphene.Boolean(
        default_value=False,
        description="If true, send an email notification to the customer.",
    )


class FulfillmentCancelInput(graphene.InputObjectType):
    restock = graphene.Boolean(description="Whether item lines are restocked.")


class FulfillmentClearMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears metadata for fulfillment."
        model = models.Fulfillment
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        public = True


class FulfillmentUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates metadata for fulfillment."
        model = models.Fulfillment
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        public = True


class FulfillmentClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears private metadata for fulfillment."
        model = models.Fulfillment
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        public = False


class FulfillmentUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Updates metadata for fulfillment."
        model = models.Fulfillment
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        public = False


class OrderFulfill(BaseMutation):
    fulfillments = graphene.List(Fulfillment, description="A created fulfillments.")
    order = graphene.Field(Order, description="Fulfilled order.")

    class Arguments:
        order = graphene.ID(
            description="ID of the order to be fulfilled.", name="order"
        )
        input = OrderFulfillInput(
            required=True, description="Fields required to create an fulfillment."
        )

    class Meta:
        description = "Creates a new fulfillments for an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_lines(cls, order_lines, quantities):
        for order_line, line_quantities in zip(order_lines, quantities):
            line_quantity_unfulfilled = order_line.quantity_unfulfilled

            if sum(line_quantities) > line_quantity_unfulfilled:
                msg = (
                    "Only %(quantity)d item%(item_pluralize)s remaining "
                    "to fulfill: %(order_line)s."
                ) % {
                    "quantity": line_quantity_unfulfilled,
                    "item_pluralize": pluralize(line_quantity_unfulfilled),
                    "order_line": order_line,
                }
                raise ValidationError(
                    {
                        "order_line_id": ValidationError(
                            msg, code=OrderErrorCode.FULFILL_ORDER_LINE
                        )
                    }
                )

    @classmethod
    def check_warehouses_for_duplicates(cls, warehouse_ids):
        for warehouse_ids_for_line in warehouse_ids:
            duplicates = {
                id
                for id in warehouse_ids_for_line
                if warehouse_ids_for_line.count(id) > 1
            }
            if duplicates:
                raise ValidationError(
                    {
                        "warehouse": ValidationError(
                            "Duplicated warehouse ID.", code=OrderErrorCode.UNIQUE
                        )
                    }
                )

    @classmethod
    def check_lines_for_duplicates(cls, lines_ids):
        duplicates = {id for id in lines_ids if lines_ids.count(id) > 1}
        if duplicates:
            raise ValidationError(
                {
                    "orderLineId": ValidationError(
                        "Duplicated warehouse ID.", code=OrderErrorCode.UNIQUE
                    )
                }
            )

    @classmethod
    def clean_input(cls, data):
        lines = data["lines"]

        warehouse_ids_for_lines = [
            [stock["warehouse"] for stock in line["stocks"]] for line in lines
        ]
        cls.check_warehouses_for_duplicates(warehouse_ids_for_lines)

        quantities_for_lines = [
            [stock["quantity"] for stock in line["stocks"]] for line in lines
        ]

        lines_ids = [line["order_line_id"] for line in lines]
        cls.check_lines_for_duplicates(lines_ids)
        order_lines = cls.get_nodes_or_error(
            lines_ids, field="liens", only_type=OrderLine
        )

        cls.clean_lines(order_lines, quantities_for_lines)

        if sum(sum(quantities_for_lines, [])) <= 0:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Total quantity must be larger than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                    )
                }
            )

        lines_for_warehouses = defaultdict(list)
        for line, order_line in zip(lines, order_lines):
            for stock in line["stocks"]:
                lines_for_warehouses[stock["warehouse"]].append(
                    {"order_line": order_line, "quantity": stock["quantity"]}
                )

        data["order_lines"] = order_lines
        data["quantities"] = quantities_for_lines
        data["lines_for_warehouses"] = lines_for_warehouses
        return data

    @classmethod
    def create_fulfillment(cls, fulfillment, warehouse_pk, lines):
        fulfillment_lines = []
        for line in lines:
            quantity = line["quantity"]
            order_line = line["order_line"]
            if quantity > 0:
                try:
                    fulfill_order_line(order_line, quantity, warehouse_pk)
                except InsufficientStock as exc:
                    raise ValidationError(
                        {
                            "stocks": ValidationError(
                                f"Insufficient product stock: {exc.item}",
                                code=OrderErrorCode.INSUFFICIENT_STOCK,
                            )
                        }
                    )
                if order_line.is_digital:
                    order_line.variant.digital_content.urls.create(line=order_line)
                fulfillment_lines.append(
                    models.FulfillmentLine(
                        order_line=order_line,
                        fulfillment=fulfillment,
                        quantity=quantity,
                        stock=order_line.variant.stocks.get(warehouse=warehouse_pk),
                    )
                )
        return fulfillment_lines

    @classmethod
    @transaction.atomic()
    def create_fulfillments(cls, requester, order, cleaned_input):
        lines_for_warehouses = cleaned_input["lines_for_warehouses"]
        fulfillments = []
        fulfillment_lines = []
        for warehouse_global_id in lines_for_warehouses:
            warehouse_pk = from_global_id_strict_type(
                warehouse_global_id, only_type=Warehouse, field="warehouse",
            )
            fulfillment = models.Fulfillment.objects.create(order=order)
            fulfillments.append(fulfillment)
            fulfillment_lines.extend(
                cls.create_fulfillment(
                    fulfillment,
                    warehouse_pk,
                    lines_for_warehouses[warehouse_global_id],
                )
            )

        models.FulfillmentLine.objects.bulk_create(fulfillment_lines)
        order_fulfilled(
            fulfillments,
            requester,
            fulfillment_lines,
            cleaned_input.get("notify_customer", True),
        )
        return fulfillments

    @classmethod
    def perform_mutation(cls, _root, info, order, **data):
        order = cls.get_node_or_error(info, order, field="order", only_type=Order)
        data = data.get("input")

        cleaned_input = cls.clean_input(data)

        requester = get_user_or_service_account_from_context(info.context)
        fulfillments = cls.create_fulfillments(requester, order, cleaned_input)

        return OrderFulfill(fulfillments=fulfillments, order=order)


class FulfillmentCreate(BaseMutation):
    fulfillment = graphene.Field(Fulfillment, description="A created fulfillment.")
    order = graphene.Field(Order, description="Fulfilled order.")

    class Arguments:
        order = graphene.ID(
            description="ID of the order to be fulfilled.", name="order"
        )
        input = FulfillmentCreateInput(
            required=True, description="Fields required to create an fulfillment."
        )

    class Meta:
        description = "Creates a new fulfillment for an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_lines(cls, order_lines, quantities):
        for order_line, quantity in zip(order_lines, quantities):
            line_quantity_unfulfilled = order_line.quantity_unfulfilled
            if quantity > line_quantity_unfulfilled:
                msg = (
                    "Only %(quantity)d item%(item_pluralize)s remaining "
                    "to fulfill: %(order_line)s."
                ) % {
                    "quantity": line_quantity_unfulfilled,
                    "item_pluralize": pluralize(line_quantity_unfulfilled),
                    "order_line": order_line,
                }
                raise ValidationError(
                    {
                        "order_line_id": ValidationError(
                            msg, code=OrderErrorCode.FULFILL_ORDER_LINE
                        )
                    }
                )

    @classmethod
    def clean_input(cls, data):
        lines = data["lines"]
        quantities = [line["quantity"] for line in lines]
        lines_ids = [line["order_line_id"] for line in lines]
        order_lines = cls.get_nodes_or_error(
            lines_ids, field="lines", only_type=OrderLine
        )

        cls.clean_lines(order_lines, quantities)

        if sum(quantities) <= 0:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Total quantity must be larger than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                    )
                }
            )

        data["order_lines"] = order_lines
        data["quantities"] = quantities
        return data

    @classmethod
    def save(cls, user, fulfillment, order, cleaned_input):
        fulfillment.save()
        order_lines = cleaned_input.get("order_lines")
        quantities = cleaned_input.get("quantities")
        fulfillment_lines = []
        for order_line, quantity in zip(order_lines, quantities):
            if quantity > 0:
                fulfill_order_line(order_line, quantity)
                if order_line.is_digital:
                    order_line.variant.digital_content.urls.create(line=order_line)
                fulfillment_lines.append(
                    models.FulfillmentLine(
                        order_line=order_line,
                        fulfillment=fulfillment,
                        quantity=quantity,
                    )
                )

        fulfillment.lines.bulk_create(fulfillment_lines)
        order_fulfilled(
            fulfillment,
            user,
            fulfillment_lines,
            cleaned_input.get("notify_customer", True),
        )
        return fulfillment

    @classmethod
    def perform_mutation(cls, _root, info, order, **data):
        order = cls.get_node_or_error(info, order, field="order", only_type=Order)
        data = data.get("input")
        fulfillment = models.Fulfillment(
            tracking_number=data.pop("tracking_number", None) or "", order=order
        )
        cleaned_input = cls.clean_input(data)
        fulfillment = cls.save(info.context.user, fulfillment, order, cleaned_input)
        return FulfillmentCreate(fulfillment=fulfillment, order=fulfillment.order)


class FulfillmentUpdateTracking(BaseMutation):
    fulfillment = graphene.Field(
        Fulfillment, description="A fulfillment with updated tracking."
    )
    order = graphene.Field(
        Order, description="Order for which fulfillment was updated."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of an fulfillment to update.")
        input = FulfillmentUpdateTrackingInput(
            required=True, description="Fields required to update an fulfillment."
        )

    class Meta:
        description = "Updates a fulfillment for an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        fulfillment = cls.get_node_or_error(info, data.get("id"), only_type=Fulfillment)
        tracking_number = data.get("input").get("tracking_number") or ""
        fulfillment.tracking_number = tracking_number
        fulfillment.save()
        order = fulfillment.order
        fulfillment_tracking_updated(fulfillment, info.context.user, tracking_number)
        input_data = data.get("input", {})
        notify_customer = input_data.get("notify_customer")
        if notify_customer:
            send_fulfillment_update.delay(order.pk, fulfillment.pk)
        return FulfillmentUpdateTracking(fulfillment=fulfillment, order=order)


class FulfillmentCancel(BaseMutation):
    fulfillment = graphene.Field(Fulfillment, description="A canceled fulfillment.")
    order = graphene.Field(Order, description="Order which fulfillment was cancelled.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of an fulfillment to cancel.")
        input = FulfillmentCancelInput(
            required=True, description="Fields required to cancel an fulfillment."
        )

    class Meta:
        description = "Cancels existing fulfillment and optionally restocks items."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        restock = data.get("input").get("restock")
        fulfillment = cls.get_node_or_error(info, data.get("id"), only_type=Fulfillment)

        if not fulfillment.can_edit():
            err_msg = "This fulfillment can't be canceled"
            raise ValidationError(
                {
                    "fulfillment": ValidationError(
                        err_msg, code=OrderErrorCode.CANNOT_CANCEL_FULFILLMENT
                    )
                }
            )

        order = fulfillment.order
        cancel_fulfillment(fulfillment, info.context.user, restock)
        return FulfillmentCancel(fulfillment=fulfillment, order=order)
