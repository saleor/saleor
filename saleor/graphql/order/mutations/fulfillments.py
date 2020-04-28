from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.template.defaultfilters import pluralize

from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....order import models
from ....order.actions import (
    cancel_fulfillment,
    create_fulfillments,
    fulfillment_tracking_updated,
)
from ....order.emails import send_fulfillment_update
from ....order.error_codes import OrderErrorCode
from ...core.mutations import BaseMutation
from ...core.types.common import OrderError
from ...core.utils import from_global_id_strict_type, get_duplicated_values
from ...meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
from ...order.types import Fulfillment, Order
from ...utils import get_user_or_app_from_context
from ...warehouse.types import Warehouse
from ..types import OrderLine


class OrderFulfillStockInput(graphene.InputObjectType):
    quantity = graphene.Int(
        description="The number of line items to be fulfilled from given warehouse."
    )
    warehouse = graphene.ID(
        description="ID of the warehouse from which the item will be fulfilled."
    )


class OrderFulfillLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(
        description="The ID of the order line.", name="orderLineId"
    )
    stocks = graphene.List(
        graphene.NonNull(OrderFulfillStockInput),
        required=True,
        description="List of stock items to create.",
    )


class OrderFulfillInput(graphene.InputObjectType):
    lines = graphene.List(
        graphene.NonNull(OrderFulfillLineInput),
        required=True,
        description="List of items informing how to fulfill the order.",
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
    warehouse_id = graphene.ID(
        description="ID of warehouse where items will be restock.", required=True
    )


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
    fulfillments = graphene.List(
        Fulfillment, description="List of created fulfillments."
    )
    order = graphene.Field(Order, description="Fulfilled order.")

    class Arguments:
        order = graphene.ID(
            description="ID of the order to be fulfilled.", name="order"
        )
        input = OrderFulfillInput(
            required=True, description="Fields required to create an fulfillment."
        )

    class Meta:
        description = "Creates new fulfillments for an order."
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
                order_line_global_id = graphene.Node.to_global_id(
                    "OrderLine", order_line.pk
                )
                raise ValidationError(
                    {
                        "order_line_id": ValidationError(
                            msg,
                            code=OrderErrorCode.FULFILL_ORDER_LINE,
                            params={"order_line": order_line_global_id},
                        )
                    }
                )

    @classmethod
    def check_warehouses_for_duplicates(cls, warehouse_ids):
        for warehouse_ids_for_line in warehouse_ids:
            duplicates = get_duplicated_values(warehouse_ids_for_line)
            if duplicates:
                raise ValidationError(
                    {
                        "warehouse": ValidationError(
                            "Duplicated warehouse ID.",
                            code=OrderErrorCode.DUPLICATED_INPUT_ITEM,
                            params={"warehouse": duplicates.pop()},
                        )
                    }
                )

    @classmethod
    def check_lines_for_duplicates(cls, lines_ids):
        duplicates = get_duplicated_values(lines_ids)
        if duplicates:
            raise ValidationError(
                {
                    "orderLineId": ValidationError(
                        "Duplicated order line ID.",
                        code=OrderErrorCode.DUPLICATED_INPUT_ITEM,
                        params={"order_line": duplicates.pop()},
                    )
                }
            )

    @classmethod
    def check_total_quantity_of_items(cls, quantities_for_lines):
        flat_quantities = sum(quantities_for_lines, [])
        if sum(flat_quantities) <= 0:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Total quantity must be larger than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY,
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
            lines_ids, field="lines", only_type=OrderLine
        )

        cls.clean_lines(order_lines, quantities_for_lines)

        cls.check_total_quantity_of_items(quantities_for_lines)

        lines_for_warehouses = defaultdict(list)
        for line, order_line in zip(lines, order_lines):
            for stock in line["stocks"]:
                if stock["quantity"] > 0:
                    warehouse_pk = from_global_id_strict_type(
                        stock["warehouse"], only_type=Warehouse, field="warehouse"
                    )
                    lines_for_warehouses[warehouse_pk].append(
                        {"order_line": order_line, "quantity": stock["quantity"]}
                    )

        data["order_lines"] = order_lines
        data["quantities"] = quantities_for_lines
        data["lines_for_warehouses"] = lines_for_warehouses
        return data

    @classmethod
    def perform_mutation(cls, _root, info, order, **data):
        order = cls.get_node_or_error(info, order, field="order", only_type=Order)
        data = data.get("input")

        cleaned_input = cls.clean_input(data)

        requester = get_user_or_app_from_context(info.context)
        lines_for_warehouses = cleaned_input["lines_for_warehouses"]
        notify_customer = cleaned_input.get("notify_customer", True)

        try:
            fulfillments = create_fulfillments(
                requester, order, dict(lines_for_warehouses), notify_customer
            )
        except InsufficientStock as exc:
            order_line_global_id = graphene.Node.to_global_id(
                "OrderLine", exc.context["order_line"].pk
            )
            warehouse_global_id = graphene.Node.to_global_id(
                "Warehouse", exc.context["warehouse_pk"]
            )
            raise ValidationError(
                {
                    "stocks": ValidationError(
                        f"Insufficient product stock: {exc.item}",
                        code=OrderErrorCode.INSUFFICIENT_STOCK,
                        params={
                            "order_line": order_line_global_id,
                            "warehouse": warehouse_global_id,
                        },
                    )
                }
            )

        return OrderFulfill(fulfillments=fulfillments, order=order)


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
        warehouse_id = data.get("input").get("warehouse_id")
        warehouse = cls.get_node_or_error(
            info, warehouse_id, only_type="Warehouse", field="warehouse_id"
        )
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
        cancel_fulfillment(fulfillment, info.context.user, warehouse)
        fulfillment.refresh_from_db(fields=["status"])
        order.refresh_from_db(fields=["status"])
        return FulfillmentCancel(fulfillment=fulfillment, order=order)
