from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.template.defaultfilters import pluralize

from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....giftcard.utils import order_has_gift_card_lines
from ....order import FulfillmentLineData, FulfillmentStatus
from ....order import models as order_models
from ....order.actions import (
    approve_fulfillment,
    cancel_fulfillment,
    cancel_waiting_fulfillment,
    create_fulfillments,
    create_fulfillments_for_returned_products,
    create_refund_fulfillment,
    fulfillment_tracking_updated,
)
from ....order.error_codes import OrderErrorCode
from ....order.fetch import OrderLineInfo
from ....order.notifications import send_fulfillment_update
from ...core.descriptions import ADDED_IN_31
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types.common import OrderError
from ...core.utils import get_duplicated_values
from ...warehouse.types import Warehouse
from ..types import Fulfillment, FulfillmentLine, Order, OrderLine
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
    fulfillments = graphene.List(
        Fulfillment, description="List of created fulfillments."
    )
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


class FulfillmentUpdateTracking(BaseMutation):
    fulfillment = graphene.Field(
        Fulfillment, description="A fulfillment with updated tracking."
    )
    order = graphene.Field(
        Order, description="Order for which fulfillment was updated."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a fulfillment to update.")
        input = FulfillmentUpdateTrackingInput(
            required=True, description="Fields required to update a fulfillment."
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
        fulfillment_tracking_updated(
            fulfillment,
            info.context.user,
            info.context.app,
            tracking_number,
            info.context.plugins,
        )
        input_data = data.get("input", {})
        notify_customer = input_data.get("notify_customer")
        if notify_customer:
            send_fulfillment_update(order, fulfillment, info.context.plugins)
        return FulfillmentUpdateTracking(fulfillment=fulfillment, order=order)


class FulfillmentCancelInput(graphene.InputObjectType):
    warehouse_id = graphene.ID(
        description="ID of a warehouse where items will be restocked. Optional "
        "when fulfillment is in WAITING_FOR_APPROVAL state.",
        required=False,
    )


class FulfillmentCancel(BaseMutation):
    fulfillment = graphene.Field(Fulfillment, description="A canceled fulfillment.")
    order = graphene.Field(Order, description="Order which fulfillment was cancelled.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a fulfillment to cancel.")
        input = FulfillmentCancelInput(
            required=False, description="Fields required to cancel a fulfillment."
        )

    class Meta:
        description = "Cancels existing fulfillment and optionally restocks items."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def validate_fulfillment(cls, fulfillment, warehouse):
        if not fulfillment.can_edit():
            raise ValidationError(
                {
                    "fulfillment": ValidationError(
                        "This fulfillment can't be canceled",
                        code=OrderErrorCode.CANNOT_CANCEL_FULFILLMENT,
                    )
                }
            )
        if (
            fulfillment.status != FulfillmentStatus.WAITING_FOR_APPROVAL
            and not warehouse
        ):
            raise ValidationError(
                {
                    "warehouseId": ValidationError(
                        "This parameter is required for fulfillments which are not in "
                        "WAITING_FOR_APPROVAL state.",
                        code=OrderErrorCode.REQUIRED,
                    )
                }
            )

    @classmethod
    def validate_order(cls, order):
        if order_has_gift_card_lines(order):
            raise ValidationError(
                {
                    "fulfillment": ValidationError(
                        "Cannot cancel fulfillment with gift card lines.",
                        code=OrderErrorCode.CANNOT_CANCEL_FULFILLMENT.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        fulfillment = cls.get_node_or_error(info, data.get("id"), only_type=Fulfillment)
        order = fulfillment.order

        cls.validate_order(order)

        warehouse = None
        if fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL:
            warehouse = None
        elif warehouse_id := data.get("input", {}).get("warehouse_id"):
            warehouse = cls.get_node_or_error(
                info, warehouse_id, only_type="Warehouse", field="warehouse_id"
            )

        cls.validate_fulfillment(fulfillment, warehouse)

        if fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL:
            fulfillment = cancel_waiting_fulfillment(
                fulfillment,
                info.context.user,
                info.context.app,
                info.context.plugins,
            )
        else:
            fulfillment = cancel_fulfillment(
                fulfillment,
                info.context.user,
                info.context.app,
                warehouse,
                info.context.plugins,
            )
        order.refresh_from_db(fields=["status"])
        return FulfillmentCancel(fulfillment=fulfillment, order=order)


class FulfillmentApprove(BaseMutation):
    fulfillment = graphene.Field(Fulfillment, description="An approved fulfillment.")
    order = graphene.Field(Order, description="Order which fulfillment was approved.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a fulfillment to approve.")
        notify_customer = graphene.Boolean(
            required=True, description="True if confirmation email should be send."
        )
        allow_stock_to_be_exceeded = graphene.Boolean(
            default_value=False, description="True if stock could be exceeded."
        )

    class Meta:
        description = f"{ADDED_IN_31} Approve existing fulfillment."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, info, fulfillment):
        if fulfillment.status != FulfillmentStatus.WAITING_FOR_APPROVAL:
            raise ValidationError(
                "Invalid fulfillment status, only WAITING_FOR_APPROVAL "
                "fulfillments can be accepted.",
                code=OrderErrorCode.INVALID.value,
            )

        OrderFulfill.check_lines_for_preorder([line.order_line for line in fulfillment])

        if (
            not info.context.site.settings.fulfillment_allow_unpaid
            and not fulfillment.order.is_fully_paid()
        ):
            raise ValidationError(
                "Cannot fulfill unpaid order.",
                code=OrderErrorCode.CANNOT_FULFILL_UNPAID_ORDER,
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        fulfillment = cls.get_node_or_error(info, data["id"], only_type="Fulfillment")
        cls.clean_input(info, fulfillment)

        order = fulfillment.order
        fulfillment = approve_fulfillment(
            fulfillment,
            info.context.user,
            info.context.app,
            info.context.plugins,
            info.context.site.settings,
            notify_customer=data["notify_customer"],
            allow_stock_to_be_exceeded=data.get("allow_stock_to_be_exceeded"),
        )
        order.refresh_from_db(fields=["status"])
        return FulfillmentApprove(fulfillment=fulfillment, order=order)


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
        description="The total amount of refund when the value is provided manually.",
    )
    include_shipping_costs = graphene.Boolean(
        description=(
            "If true, Saleor will refund shipping costs. If amountToRefund is provided"
            "includeShippingCosts will be ignored."
        ),
        default_value=False,
    )


class FulfillmentRefundAndReturnProductBase(BaseMutation):
    class Meta:
        abstract = True

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
    def clean_amount_to_refund(cls, order, amount_to_refund, payment, cleaned_input):
        if amount_to_refund is not None:
            if order_has_gift_card_lines(order):
                raise ValidationError(
                    {
                        "amount_to_refund": ValidationError(
                            (
                                "Cannot specified amount to refund when order has "
                                "gift card lines."
                            ),
                            code=OrderErrorCode.CANNOT_REFUND.value,
                        )
                    }
                )
            if amount_to_refund > payment.captured_amount:
                raise ValidationError(
                    {
                        "amount_to_refund": ValidationError(
                            (
                                "The amountToRefund is greater than the maximal "
                                "possible amount to refund."
                            ),
                            code=OrderErrorCode.CANNOT_REFUND.value,
                        ),
                    }
                )
        cleaned_input["amount_to_refund"] = amount_to_refund

    @classmethod
    def _raise_error_for_line(cls, msg, type, line_id, field_name, code=None):
        line_global_id = graphene.Node.to_global_id(type, line_id)
        if not code:
            code = OrderErrorCode.INVALID_QUANTITY.value
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
    def clean_fulfillment_lines(
        cls, fulfillment_lines_data, cleaned_input, whitelisted_statuses
    ):
        fulfillment_lines = cls.get_nodes_or_error(
            [line["fulfillment_line_id"] for line in fulfillment_lines_data],
            field="fulfillment_lines",
            only_type=FulfillmentLine,
            qs=order_models.FulfillmentLine.objects.prefetch_related(
                "fulfillment", "order_line"
            ),
        )
        fulfillment_lines = list(fulfillment_lines)
        cleaned_fulfillment_lines = []
        for line, line_data in zip(fulfillment_lines, fulfillment_lines_data):
            quantity = line_data["quantity"]
            if line.order_line.is_gift_card:
                cls._raise_error_for_line(
                    "Cannot refund or return gift card line.",
                    "FulfillmentLine",
                    line.pk,
                    "fulfillment_line_id",
                    OrderErrorCode.GIFT_CARD_LINE.value,
                )
            if line.quantity < quantity:
                cls._raise_error_for_line(
                    "Provided quantity is bigger than quantity from "
                    "fulfillment line",
                    "FulfillmentLine",
                    line.pk,
                    "fulfillment_line_id",
                )
            if line.fulfillment.status not in whitelisted_statuses:
                allowed_statuses_str = ", ".join(whitelisted_statuses)
                cls._raise_error_for_line(
                    f"Unable to process action for fulfillmentLine with different "
                    f"status than {allowed_statuses_str}.",
                    "FulfillmentLine",
                    line.pk,
                    "fulfillment_line_id",
                    code=OrderErrorCode.INVALID.value,
                )
            replace = line_data.get("replace", False)
            if replace and not line.order_line.variant_id:
                cls._raise_error_for_line(
                    "Unable to replace line as the assigned product doesn't exist.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )
            cleaned_fulfillment_lines.append(
                FulfillmentLineData(
                    line=line,
                    quantity=quantity,
                    replace=replace,
                )
            )
        cleaned_input["fulfillment_lines"] = cleaned_fulfillment_lines

    @classmethod
    def clean_lines(cls, lines_data, cleaned_input):
        order_lines = cls.get_nodes_or_error(
            [line["order_line_id"] for line in lines_data],
            field="order_lines",
            only_type=OrderLine,
            qs=order_models.OrderLine.objects.prefetch_related(
                "fulfillment_lines__fulfillment", "variant", "allocations"
            ),
        )
        order_lines = list(order_lines)
        cleaned_order_lines = []
        for line, line_data in zip(order_lines, lines_data):
            quantity = line_data["quantity"]
            if line.is_gift_card:
                cls._raise_error_for_line(
                    "Cannot refund or return gift card line.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                    OrderErrorCode.GIFT_CARD_LINE.value,
                )
            if line.quantity < quantity:
                cls._raise_error_for_line(
                    "Provided quantity is bigger than quantity from order line.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )
            quantity_ready_to_move = line.quantity_unfulfilled
            if quantity_ready_to_move < quantity:
                cls._raise_error_for_line(
                    "Provided quantity is bigger than unfulfilled quantity.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )
            replace = line_data.get("replace", False)
            if replace and not line.variant_id:
                cls._raise_error_for_line(
                    "Unable to replace line as the assigned product doesn't exist.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )

            cleaned_order_lines.append(
                OrderLineInfo(line=line, quantity=quantity, replace=replace)
            )
        cleaned_input["order_lines"] = cleaned_order_lines


class FulfillmentRefundProducts(FulfillmentRefundAndReturnProductBase):
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
        cls.clean_amount_to_refund(order, amount_to_refund, payment, cleaned_input)

        cleaned_input.update(
            {"include_shipping_costs": include_shipping_costs, "order": order}
        )

        order_lines_data = input.get("order_lines", [])
        fulfillment_lines_data = input.get("fulfillment_lines", [])

        if order_lines_data:
            cls.clean_lines(order_lines_data, cleaned_input)
        if fulfillment_lines_data:
            cls.clean_fulfillment_lines(
                fulfillment_lines_data,
                cleaned_input,
                whitelisted_statuses=[
                    FulfillmentStatus.FULFILLED,
                    FulfillmentStatus.RETURNED,
                    FulfillmentStatus.WAITING_FOR_APPROVAL,
                ],
            )
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        cleaned_input = cls.clean_input(info, data.get("order"), data.get("input"))
        order = cleaned_input["order"]

        refund_fulfillment = create_refund_fulfillment(
            info.context.user,
            info.context.app,
            order,
            cleaned_input["payment"],
            cleaned_input.get("order_lines", []),
            cleaned_input.get("fulfillment_lines", []),
            info.context.plugins,
            cleaned_input["amount_to_refund"],
            cleaned_input["include_shipping_costs"],
        )
        return cls(order=order, fulfillment=refund_fulfillment)


class OrderReturnLineInput(graphene.InputObjectType):
    order_line_id = graphene.ID(
        description="The ID of the order line to return.",
        name="orderLineId",
        required=True,
    )
    quantity = graphene.Int(
        description="The number of items to be returned.",
        required=True,
    )
    replace = graphene.Boolean(
        description="Determines, if the line should be added to replace order.",
        default_value=False,
    )


class OrderReturnFulfillmentLineInput(graphene.InputObjectType):
    fulfillment_line_id = graphene.ID(
        description="The ID of the fulfillment line to return.",
        name="fulfillmentLineId",
        required=True,
    )
    quantity = graphene.Int(
        description="The number of items to be returned.",
        required=True,
    )
    replace = graphene.Boolean(
        description="Determines, if the line should be added to replace order.",
        default_value=False,
    )


class OrderReturnProductsInput(graphene.InputObjectType):
    order_lines = graphene.List(
        graphene.NonNull(OrderReturnLineInput),
        description="List of unfulfilled lines to return.",
    )
    fulfillment_lines = graphene.List(
        graphene.NonNull(OrderReturnFulfillmentLineInput),
        description="List of fulfilled lines to return.",
    )
    amount_to_refund = PositiveDecimal(
        required=False,
        description="The total amount of refund when the value is provided manually.",
    )
    include_shipping_costs = graphene.Boolean(
        description=(
            "If true, Saleor will refund shipping costs. If amountToRefund is provided"
            "includeShippingCosts will be ignored."
        ),
        default_value=False,
    )
    refund = graphene.Boolean(
        description="If true, Saleor will call refund action for all lines.",
        default_value=False,
    )


class FulfillmentReturnProducts(FulfillmentRefundAndReturnProductBase):
    return_fulfillment = graphene.Field(
        Fulfillment, description="A return fulfillment."
    )
    replace_fulfillment = graphene.Field(
        Fulfillment, description="A replace fulfillment."
    )
    order = graphene.Field(Order, description="Order which fulfillment was returned.")
    replace_order = graphene.Field(
        Order,
        description="A draft order which was created for products with replace flag.",
    )

    class Meta:
        description = "Return products."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    class Arguments:
        order = graphene.ID(
            description="ID of the order to be returned.", required=True
        )
        input = OrderReturnProductsInput(
            required=True,
            description="Fields required to return products.",
        )

    @classmethod
    def clean_input(cls, info, order_id, input):
        cleaned_input = {}
        amount_to_refund = input.get("amount_to_refund")
        include_shipping_costs = input["include_shipping_costs"]
        refund = input["refund"]

        qs = order_models.Order.objects.prefetch_related("payments")
        order = cls.get_node_or_error(
            info, order_id, field="order", only_type=Order, qs=qs
        )
        payment = order.get_last_payment()
        if refund:
            cls.clean_order_payment(payment, cleaned_input)
            cls.clean_amount_to_refund(order, amount_to_refund, payment, cleaned_input)

        cleaned_input.update(
            {
                "include_shipping_costs": include_shipping_costs,
                "order": order,
                "refund": refund,
            }
        )

        order_lines_data = input.get("order_lines")
        fulfillment_lines_data = input.get("fulfillment_lines")

        if order_lines_data:
            cls.clean_lines(order_lines_data, cleaned_input)
        if fulfillment_lines_data:
            cls.clean_fulfillment_lines(
                fulfillment_lines_data,
                cleaned_input,
                whitelisted_statuses=[
                    FulfillmentStatus.FULFILLED,
                    FulfillmentStatus.REFUNDED,
                    FulfillmentStatus.WAITING_FOR_APPROVAL,
                ],
            )
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        cleaned_input = cls.clean_input(info, data.get("order"), data.get("input"))
        order = cleaned_input["order"]
        response = create_fulfillments_for_returned_products(
            info.context.user,
            info.context.app,
            order,
            cleaned_input.get("payment"),
            cleaned_input.get("order_lines", []),
            cleaned_input.get("fulfillment_lines", []),
            info.context.plugins,
            cleaned_input["refund"],
            cleaned_input.get("amount_to_refund"),
            cleaned_input["include_shipping_costs"],
        )
        return_fulfillment, replace_fulfillment, replace_order = response
        return cls(
            order=order,
            return_fulfillment=return_fulfillment,
            replace_fulfillment=replace_fulfillment,
            replace_order=replace_order,
        )
