from collections import defaultdict
from typing import Optional
from uuid import UUID

import graphene
from django.core.exceptions import ValidationError
from django.template.defaultfilters import pluralize

from ....core.exceptions import InsufficientStock
from ....order import models as order_models
from ....order.actions import OrderFulfillmentLineInfo, create_fulfillments
from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_36
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, NonNullList, OrderError
from ...core.utils import WebhookEventInfo, get_duplicated_values
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
from ...warehouse.types import Warehouse
from ..types import Fulfillment, Order, OrderLine
from ..utils import prepare_insufficient_stock_order_validation_errors


class OrderFulfillStockInput(BaseInputObjectType):
    quantity = graphene.Int(
        description="The number of line items to be fulfilled from given warehouse.",
        required=True,
    )
    warehouse = graphene.ID(
        description="ID of the warehouse from which the item will be fulfilled.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderFulfillLineInput(BaseInputObjectType):
    order_line_id = graphene.ID(
        description="The ID of the order line.", name="orderLineId"
    )
    stocks = NonNullList(
        OrderFulfillStockInput,
        required=True,
        description="List of stock items to create.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderFulfillInput(BaseInputObjectType):
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
    tracking_number = graphene.String(
        description="Fulfillment tracking number." + ADDED_IN_36,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class FulfillmentUpdateTrackingInput(BaseInputObjectType):
    tracking_number = graphene.String(description="Fulfillment tracking number.")
    notify_customer = graphene.Boolean(
        default_value=False,
        description="If true, send an email notification to the customer.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


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
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.FULFILLMENT_CREATED,
                description="A new fulfillment is created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ORDER_FULFILLED,
                description="Order is fulfilled.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.FULFILLMENT_TRACKING_NUMBER_UPDATED,
                description="Sent when fulfillment tracking number is updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.FULFILLMENT_APPROVED,
                description="A fulfillment is approved.",
            ),
        ]

    @classmethod
    def clean_lines(cls, order_lines, quantities_for_lines):
        for order_line, line_quantities in zip(order_lines, quantities_for_lines):
            line_total_quantity = sum(line_quantities)
            line_quantity_unfulfilled = order_line.quantity_unfulfilled

            if line_total_quantity > line_quantity_unfulfilled:
                msg = (
                    "Only %(quantity)d item%(item_pluralize)s remaining to fulfill."
                ) % {
                    "quantity": line_quantity_unfulfilled,
                    "item_pluralize": pluralize(line_quantity_unfulfilled),
                }
                order_line_global_id = graphene.Node.to_global_id(
                    "OrderLine", order_line.pk
                )
                raise ValidationError(
                    {
                        "order_line_id": ValidationError(
                            msg,
                            code=OrderErrorCode.FULFILL_ORDER_LINE.value,
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
                            code=OrderErrorCode.DUPLICATED_INPUT_ITEM.value,
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
                        code=OrderErrorCode.DUPLICATED_INPUT_ITEM.value,
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
                            code=OrderErrorCode.FULFILL_ORDER_LINE.value,
                            params={"order_lines": [order_line_global_id]},
                        )
                    }
                )

    @classmethod
    def check_total_quantity_of_items(cls, quantities_for_lines: list[list[int]]):
        flat_quantities: list[int] = sum(quantities_for_lines, [])
        if sum(flat_quantities) <= 0:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Total quantity must be larger than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY.value,
                    )
                }
            )

    @classmethod
    def clean_input(cls, info: ResolveInfo, order, data, site):
        if not order.is_fully_paid() and (
            site.settings.fulfillment_auto_approve
            and not site.settings.fulfillment_allow_unpaid
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

        quantities_for_lines: list[list[int]] = [
            [stock["quantity"] for stock in line["stocks"]] for line in lines
        ]

        lines_ids = [line["order_line_id"] for line in lines]
        cls.check_lines_for_duplicates(lines_ids)
        order_lines = cls.get_nodes_or_error(
            lines_ids, field="lines", only_type=OrderLine
        )

        cls.clean_lines(order_lines, quantities_for_lines)

        if site.settings.fulfillment_auto_approve:
            cls.check_lines_for_preorder(order_lines)

        cls.check_total_quantity_of_items(quantities_for_lines)

        lines_for_warehouses: defaultdict[UUID, list[OrderFulfillmentLineInfo]] = (
            defaultdict(list)
        )
        for line, order_line in zip(lines, order_lines):
            for stock in line["stocks"]:
                if stock["quantity"] > 0:
                    warehouse_pk = UUID(
                        cls.get_global_id_or_error(
                            stock["warehouse"], only_type=Warehouse, field="warehouse"
                        )
                    )
                    lines_for_warehouses[warehouse_pk].append(
                        {"order_line": order_line, "quantity": stock["quantity"]}
                    )

        data["order_lines"] = order_lines
        data["lines_for_warehouses"] = lines_for_warehouses
        return data

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, order: Optional[str] = None
    ):
        instance = cls.get_node_or_error(
            info,
            order,
            field="order",
            only_type=Order,
            qs=order_models.Order.objects.prefetch_related("lines__variant"),
        )
        if not instance:
            # FIXME: order ID is optional but the code below will not work
            # unless given a valid order ID
            raise ValidationError(
                "Order does not exist.", code=OrderErrorCode.NOT_FOUND.value
            )
        cls.check_channel_permissions(info, [instance.channel_id])
        site = get_site_promise(info.context).get()
        cleaned_input = cls.clean_input(info, instance, input, site=site)

        context = info.context
        user = context.user
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        lines_for_warehouses = cleaned_input["lines_for_warehouses"]
        notify_customer = cleaned_input.get("notify_customer", True)
        allow_stock_to_be_exceeded = cleaned_input.get(
            "allow_stock_to_be_exceeded", False
        )
        approved = site.settings.fulfillment_auto_approve
        tracking_number = cleaned_input.get("tracking_number", "")
        try:
            fulfillments = create_fulfillments(
                user,
                app,
                instance,
                dict(lines_for_warehouses),
                manager,
                site.settings,
                notify_customer,
                allow_stock_to_be_exceeded=allow_stock_to_be_exceeded,
                approved=approved,
                tracking_number=tracking_number,
            )
        except InsufficientStock as exc:
            errors = prepare_insufficient_stock_order_validation_errors(exc)
            raise ValidationError({"stocks": errors})

        return OrderFulfill(fulfillments=fulfillments, order=instance)
