from collections import defaultdict
from uuid import UUID

import graphene
from django.core.exceptions import ValidationError

from ....core.exceptions import InsufficientStock
from ....order import models as order_models
from ....order.actions import OrderFulfillmentLineInfo, create_fulfillments
from ....order.error_codes import OrderErrorCode
from ....order.utils import clean_order_line_quantities
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
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
    tracking_url = graphene.String(
        description="Fulfillment tracking URL.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class FulfillmentUpdateTrackingInput(BaseInputObjectType):
    tracking_url = graphene.String(description="Fulfillment tracking URL.")
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
        ]

    @classmethod
    def clean_lines(cls, order_lines, quantities_for_lines):
        clean_order_line_quantities(order_lines, quantities_for_lines)

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
    def check_unreceived_stock(cls, lines_for_warehouses: dict, auto_approved: bool):
        """Check if all stock for fulfillment has been physically received.

        Only enforced for OWNED warehouses when auto_approved=True (FULFILLED status).
        Non-owned warehouses are exempt from this validation.
        """
        if not auto_approved:
            return

        from ....warehouse.models import Warehouse
        from ....warehouse.stock_utils import get_received_quantity_for_order_line

        for warehouse_pk, lines_data in lines_for_warehouses.items():
            warehouse = Warehouse.objects.get(pk=warehouse_pk)
            if not warehouse.is_owned:
                continue  # Skip validation for non-owned warehouses

            for line_info in lines_data:
                order_line = line_info["order_line"]
                quantity_to_fulfill = line_info["quantity"]

                total_received = get_received_quantity_for_order_line(
                    order_line, warehouse_id=warehouse_pk
                )

                if total_received == 0:
                    order_line_global_id = graphene.Node.to_global_id(
                        "OrderLine", order_line.pk
                    )
                    raise ValidationError(
                        {
                            "stocks": ValidationError(
                                "Cannot fulfill order with unreceived stock. "
                                "Goods must be physically received before fulfillment.",
                                code=OrderErrorCode.CANNOT_FULFILL_UNRECEIVED_STOCK.value,
                                params={"order_lines": [order_line_global_id]},
                            )
                        }
                    )

                if total_received < quantity_to_fulfill:
                    order_line_global_id = graphene.Node.to_global_id(
                        "OrderLine", order_line.pk
                    )
                    raise ValidationError(
                        {
                            "stocks": ValidationError(
                                "Insufficient product stock.",
                                code=OrderErrorCode.INSUFFICIENT_STOCK.value,
                                params={
                                    "order_lines": [order_line_global_id],
                                    "warehouse": graphene.Node.to_global_id(
                                        "Warehouse", warehouse_pk
                                    ),
                                },
                            )
                        }
                    )

    @classmethod
    def check_poi_requires_attention(cls, order_lines):
        from ....inventory import PurchaseOrderItemStatus
        from ....warehouse.models import AllocationSource

        for order_line in order_lines:
            poi_requires_attention = AllocationSource.objects.filter(
                allocation__order_line=order_line,
                purchase_order_item__status=PurchaseOrderItemStatus.REQUIRES_ATTENTION,
            ).exists()
            if poi_requires_attention:
                order_line_global_id = graphene.Node.to_global_id(
                    "OrderLine", order_line.pk
                )
                raise ValidationError(
                    {
                        "order_line_id": ValidationError(
                            "Cannot fulfill order line: an associated purchase order "
                            "item requires attention.",
                            code=OrderErrorCode.CANNOT_FULFILL_POI_REQUIRES_ATTENTION.value,
                            params={"order_lines": [order_line_global_id]},
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

        if order.deposit_required:
            if not order.deposit_threshold_met:
                raise ValidationError(
                    {
                        "order": ValidationError(
                            "Cannot fulfill order: deposit threshold not met. "
                            f"Required: {order.deposit_percentage}% of order total.",
                            code=OrderErrorCode.INVALID.value,
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
            lines_ids,
            field="lines",
            only_type=OrderLine,
            qs=order_models.OrderLine.objects.select_related("variant"),
        )

        cls.clean_lines(order_lines, quantities_for_lines)
        cls.check_poi_requires_attention(order_lines)

        if site.settings.fulfillment_auto_approve:
            cls.check_lines_for_preorder(order_lines)

        cls.check_total_quantity_of_items(quantities_for_lines)

        lines_for_warehouses: defaultdict[UUID, list[OrderFulfillmentLineInfo]] = (
            defaultdict(list)
        )
        for line, order_line in zip(lines, order_lines, strict=False):
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

        # Check if all stock has been physically received (only for owned warehouses)
        auto_approved = site.settings.fulfillment_auto_approve
        cls.check_unreceived_stock(lines_for_warehouses, auto_approved)

        data["order_lines"] = order_lines
        data["lines_for_warehouses"] = lines_for_warehouses
        return data

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, order: str | None = None
    ):
        instance = cls.get_node_or_error(
            info,
            order,
            field="order",
            only_type=Order,
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
        tracking_number = cleaned_input.get("tracking_url") or ""
        try:
            fulfillments = create_fulfillments(
                user,
                app,
                instance,
                dict(lines_for_warehouses),
                manager,
                site.settings,
                notify_customer=notify_customer,
                allow_stock_to_be_exceeded=allow_stock_to_be_exceeded,
                auto_approved=approved,
                tracking_url=tracking_number,
            )
        except InsufficientStock as e:
            errors = prepare_insufficient_stock_order_validation_errors(e)
            raise ValidationError({"stocks": errors}) from e

        return OrderFulfill(
            fulfillments=[
                SyncWebhookControlContext(node=fulfillment)
                for fulfillment in fulfillments
            ],
            order=SyncWebhookControlContext(instance),
        )
