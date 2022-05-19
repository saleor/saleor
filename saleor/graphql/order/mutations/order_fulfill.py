from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.template.defaultfilters import pluralize

from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import models as order_models
from ....order.actions import create_fulfillments
from ....order.error_codes import OrderErrorCode
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, OrderError
from ...core.utils import get_duplicated_values
from ...warehouse.types import Warehouse
from ..types import Fulfillment, Order, OrderLine
from ..utils import prepare_insufficient_stock_order_validation_errors


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
    stocks = NonNullList(
        OrderFulfillStockInput,
        required=True,
        description="List of stock items to create.",
    )


class OrderFulfillInput(graphene.InputObjectType):
    lines = NonNullList(
        OrderFulfillLineInput,
        required=True,
        description="List of items informing how to fulfill the order.",
    )
    notify_customer = graphene.Boolean(
        description="If true, send an email notification to the customer."
    )

    allow_stock_to_be_exceeded = graphene.Boolean(
        description="If true, then allow proceed fulfillment when stock is exceeded.",
        default_value=False,
    )


class FulfillmentUpdateTrackingInput(graphene.InputObjectType):
    tracking_number = graphene.String(description="Fulfillment tracking number.")
    notify_customer = graphene.Boolean(
        default_value=False,
        description="If true, send an email notification to the customer.",
    )


class OrderFulfill(BaseMutation):
    fulfillments = NonNullList(Fulfillment, description="List of created fulfillments.")
    order = graphene.Field(Order, description="Fulfilled order.")

    class Arguments:
        order = graphene.ID(
            description="ID of the order to be fulfilled.", name="order"
        )
        input = OrderFulfillInput(
            required=True, description="Fields required to create a fulfillment."
        )

    class Meta:
        description = "Creates new fulfillments for an order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_lines(cls, order_lines, quantities_for_lines):
        for order_line, line_quantities in zip(order_lines, quantities_for_lines):
            line_total_quantity = sum(line_quantities)
            line_quantity_unfulfilled = order_line.quantity_unfulfilled

            if line_total_quantity > line_quantity_unfulfilled:
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
                            params={"order_lines": [order_line_global_id]},
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
                        params={"order_lines": [duplicates.pop()]},
                    )
                }
            )

    @classmethod
    def check_lines_for_preorder(cls, order_lines):
        for order_line in order_lines:
            if order_line.variant_id and order_line.variant.is_preorder_active():
                order_line_global_id = graphene.Node.to_global_id(
                    "OrderLine", order_line.pk
                )
                raise ValidationError(
                    {
                        "order_line_id": ValidationError(
                            "Can not fulfill preorder variant.",
                            code=OrderErrorCode.FULFILL_ORDER_LINE,
                            params={"order_lines": [order_line_global_id]},
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
    def clean_input(cls, info, order, data):
        site_settings = info.context.site.settings
        if not order.is_fully_paid() and (
            site_settings.fulfillment_auto_approve
            and not site_settings.fulfillment_allow_unpaid
        ):
            raise ValidationError(
                {
                    "order": ValidationError(
                        "Cannot fulfill unpaid order.",
                        code=OrderErrorCode.CANNOT_FULFILL_UNPAID_ORDER.value,
                    )
                }
            )

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

        if site_settings.fulfillment_auto_approve:
            cls.check_lines_for_preorder(order_lines)

        cls.check_total_quantity_of_items(quantities_for_lines)

        lines_for_warehouses = defaultdict(list)
        for line, order_line in zip(lines, order_lines):
            for stock in line["stocks"]:
                if stock["quantity"] > 0:
                    warehouse_pk = cls.get_global_id_or_error(
                        stock["warehouse"], only_type=Warehouse, field="warehouse"
                    )
                    lines_for_warehouses[warehouse_pk].append(
                        {"order_line": order_line, "quantity": stock["quantity"]}
                    )

        data["order_lines"] = order_lines
        data["lines_for_warehouses"] = lines_for_warehouses
        return data

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, order, **data):
        order = cls.get_node_or_error(
            info,
            order,
            field="order",
            only_type=Order,
            qs=order_models.Order.objects.prefetch_related("lines__variant"),
        )
        data = data.get("input")

        cleaned_input = cls.clean_input(info, order, data)

        context = info.context
        user = context.user if not context.user.is_anonymous else None
        app = context.app
        manager = context.plugins
        lines_for_warehouses = cleaned_input["lines_for_warehouses"]
        notify_customer = cleaned_input.get("notify_customer", True)
        allow_stock_to_be_exceeded = cleaned_input.get(
            "allow_stock_to_be_exceeded", False
        )

        approved = info.context.site.settings.fulfillment_auto_approve

        try:
            fulfillments = create_fulfillments(
                user,
                app,
                order,
                dict(lines_for_warehouses),
                manager,
                context.site.settings,
                notify_customer,
                allow_stock_to_be_exceeded=allow_stock_to_be_exceeded,
                approved=approved,
            )
        except InsufficientStock as exc:
            errors = prepare_insufficient_stock_order_validation_errors(exc)
            raise ValidationError({"stocks": errors})

        return OrderFulfill(fulfillments=fulfillments, order=order)
