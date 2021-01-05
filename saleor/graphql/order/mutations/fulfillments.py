from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.template.defaultfilters import pluralize

from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....order import FulfillmentStatus
from ....order import models as order_models
from ....order.actions import (
    cancel_fulfillment,
    create_fulfillments,
    create_refund_fulfillment,
    fulfillment_tracking_updated,
)
from ....order.emails import send_fulfillment_update
from ....order.error_codes import OrderErrorCode
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types.common import OrderError
from ...core.utils import from_global_id_strict_type, get_duplicated_values
from ...order.types import Fulfillment, FulfillmentLine, Order
from ...utils import get_user_or_app_from_context
from ...warehouse.types import Warehouse
from ..types import OrderLine


class OrderFulfillStockInput(graphene.InputObjectType):
    quantity = graphene.Int(
        description="The number of line items to be fulfilled from given warehouse.",
        required=True,
    )
    warehouse = graphene.ID(
        description="ID of the warehouse from which the item will be fulfilled.",
        required=True,
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

        user = info.context.user
        lines_for_warehouses = cleaned_input["lines_for_warehouses"]
        notify_customer = cleaned_input.get("notify_customer", True)

        try:
            fulfillments = create_fulfillments(
                user, order, dict(lines_for_warehouses), notify_customer
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


class OrderRefundLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(
        description="The ID of the order line to refund.",
        name="orderLineId",
        required=True,
    )
    quantity = graphene.Int(
        description="The number of items to be refunded.",
        required=True,
    )


class OrderRefundFulfillmentLineInput(graphene.InputObjectType):
    fulfillment_line_id = graphene.ID(
        description="The ID of the fulfillment line to refund.",
        name="fulfillmentLineId",
        required=True,
    )
    quantity = graphene.Int(
        description="The number of items to be refunded.",
        required=True,
    )


class OrderRefundProductsInput(graphene.InputObjectType):
    order_lines = graphene.List(
        graphene.NonNull(OrderRefundLineInput),
        description="List of unfulfilled lines to refund.",
    )
    fulfillment_lines = graphene.List(
        graphene.NonNull(OrderRefundFulfillmentLineInput),
        description="List of fulfilled lines to refund.",
    )
    amount_to_refund = PositiveDecimal(
        required=False,
        description=("The total amount of refund when the value is provided manually."),
    )
    include_shipping_costs = graphene.Boolean(
        description=(
            "If true, Saleor will refund shipping costs. If amountToRefund is provided"
            "includeShippingCosts will be ignored."
        ),
        default_value=False,
    )


class FulfillmentRefundProducts(BaseMutation):
    fulfillment = graphene.Field(Fulfillment, description="A refunded fulfillment.")
    order = graphene.Field(Order, description="Order which fulfillment was refunded.")

    class Arguments:
        order = graphene.ID(
            description="ID of the order to be refunded.", required=True
        )
        input = OrderRefundProductsInput(
            required=True,
            description="Fields required to create an refund fulfillment.",
        )

    class Meta:
        description = "Refund products."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_order_payment(cls, payment, cleaned_input):
        if not payment or not payment.can_refund():
            raise ValidationError(
                {
                    "order": ValidationError(
                        "Order cannot be refunded.",
                        code=OrderErrorCode.CANNOT_REFUND.value,
                    )
                }
            )
        cleaned_input["payment"] = payment

    @classmethod
    def clean_amount_to_refund(cls, amount_to_refund, payment, cleaned_input):
        if amount_to_refund is not None and amount_to_refund > payment.captured_amount:
            raise ValidationError(
                {
                    "amount_to_refund": ValidationError(
                        (
                            "The amountToRefund is greater than the maximal possible "
                            "amount to refund."
                        ),
                        code=OrderErrorCode.CANNOT_REFUND.value,
                    ),
                }
            )
        cleaned_input["amount_to_refund"] = amount_to_refund

    @classmethod
    def clean_input(cls, info, order_id, input):
        cleaned_input = {}
        amount_to_refund = input.get("amount_to_refund")
        include_shipping_costs = input["include_shipping_costs"]

        qs = order_models.Order.objects.prefetch_related("payments")
        order = cls.get_node_or_error(
            info, order_id, field="order", only_type=Order, qs=qs
        )
        payment = order.get_last_payment()
        cls.clean_order_payment(payment, cleaned_input)
        cls.clean_amount_to_refund(amount_to_refund, payment, cleaned_input)

        cleaned_input.update(
            {"include_shipping_costs": include_shipping_costs, "order": order}
        )

        order_lines_data = input.get("order_lines")
        fulfillment_lines_data = input.get("fulfillment_lines")

        if order_lines_data:
            cls.clean_lines(order_lines_data, cleaned_input)
        if fulfillment_lines_data:
            cls.clean_fulfillment_lines(fulfillment_lines_data, cleaned_input)
        return cleaned_input

    @classmethod
    def _raise_error_for_line(cls, msg, type, line_id, field_name, code=None):
        line_global_id = graphene.Node.to_global_id(type, line_id)
        if not code:
            code = OrderErrorCode.INVALID_REFUND_QUANTITY.value
        raise ValidationError(
            {
                field_name: ValidationError(
                    msg,
                    code=code,
                    params={field_name: line_global_id},
                )
            }
        )

    @classmethod
    def clean_fulfillment_lines(cls, fulfillment_lines_data, cleaned_input):
        lines_ids = [line["fulfillment_line_id"] for line in fulfillment_lines_data]
        quantities_to_refund = [line["quantity"] for line in fulfillment_lines_data]
        lines_to_refund = cls.get_nodes_or_error(
            lines_ids,
            field="fulfillment_lines",
            only_type=FulfillmentLine,
            qs=order_models.FulfillmentLine.objects.prefetch_related("fulfillment"),
        )
        lines_to_refund = list(lines_to_refund)
        for line, quantity in zip(lines_to_refund, quantities_to_refund):
            if line.quantity < quantity:
                cls._raise_error_for_line(
                    "Quantity provided to refund is bigger than quantity from "
                    "fulfillment line",
                    "FulfillmentLine",
                    line.pk,
                    "fulfillment_line_id",
                )
            if line.fulfillment.status != FulfillmentStatus.FULFILLED:
                cls._raise_error_for_line(
                    "Unable to refund fulfillmentLine with different type than "
                    "FULFILLED.",
                    "FulfillmentLine",
                    line.pk,
                    "fulfillment_line_id",
                    code=OrderErrorCode.CANNOT_REFUND_FULFILLMENT_LINE.value,
                )
        cleaned_input["fulfillment_lines_quantities_to_refund"] = quantities_to_refund
        cleaned_input["fulfillment_lines_to_refund"] = lines_to_refund

    @classmethod
    def clean_lines(cls, lines_data, cleaned_input):
        lines_ids = [line["order_line_id"] for line in lines_data]
        quantities_to_refund = [line["quantity"] for line in lines_data]
        lines_to_refund = cls.get_nodes_or_error(
            lines_ids,
            field="order_lines",
            only_type=OrderLine,
            qs=order_models.OrderLine.objects.prefetch_related(
                "fulfillment_lines__fulfillment", "variant", "allocations"
            ),
        )
        lines_to_refund = list(lines_to_refund)
        for line, quantity in zip(lines_to_refund, quantities_to_refund):
            if line.quantity < quantity:
                cls._raise_error_for_line(
                    "Quantity provided to refund is bigger than quantity from order "
                    "line.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )
            quantity_ready_to_refund = line.quantity_unfulfilled
            if quantity_ready_to_refund < quantity:
                cls._raise_error_for_line(
                    "Quantity provided to refund is bigger than unfulfilled quantity.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )

        cleaned_input["order_lines_quantities_to_refund"] = quantities_to_refund
        cleaned_input["order_lines_to_refund"] = lines_to_refund

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        cleaned_input = cls.clean_input(info, data.get("order"), data.get("input"))
        order = cleaned_input["order"]
        refund_fulfillment = create_refund_fulfillment(
            get_user_or_app_from_context(info.context),
            order,
            cleaned_input["payment"],
            cleaned_input.get("order_lines_to_refund", []),
            cleaned_input.get("order_lines_quantities_to_refund", []),
            cleaned_input.get("fulfillment_lines_to_refund", []),
            cleaned_input.get("fulfillment_lines_quantities_to_refund", []),
            cleaned_input["amount_to_refund"],
            cleaned_input["include_shipping_costs"],
        )
        return cls(order=order, fulfillment=refund_fulfillment)
