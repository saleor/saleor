from typing import Any

import graphene

from ....order import FulfillmentStatus
from ....order import models as order_models
from ....order.actions import create_refund_fulfillment
from ....payment import PaymentError
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.scalars import PositiveDecimal
from ...core.types import BaseInputObjectType, NonNullList, OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Fulfillment, Order
from .fulfillment_refund_and_return_product_base import (
    FulfillmentRefundAndReturnProductBase,
)


class OrderRefundLineInput(BaseInputObjectType):
    order_line_id = graphene.ID(
        description="The ID of the order line to refund.",
        name="orderLineId",
        required=True,
    )
    quantity = graphene.Int(
        description="The number of items to be refunded.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderRefundFulfillmentLineInput(BaseInputObjectType):
    fulfillment_line_id = graphene.ID(
        description="The ID of the fulfillment line to refund.",
        name="fulfillmentLineId",
        required=True,
    )
    quantity = graphene.Int(
        description="The number of items to be refunded.",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderRefundProductsInput(BaseInputObjectType):
    order_lines = NonNullList(
        OrderRefundLineInput,
        description="List of unfulfilled lines to refund.",
    )
    fulfillment_lines = NonNullList(
        OrderRefundFulfillmentLineInput,
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

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


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
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, order_id, input):
        cleaned_input: dict[str, Any] = {}
        amount_to_refund = input.get("amount_to_refund")
        include_shipping_costs = input["include_shipping_costs"]

        qs = order_models.Order.objects.prefetch_related("payments")
        order = cls.get_node_or_error(
            info, order_id, field="order", only_type=Order, qs=qs
        )
        payment = order.get_last_payment()
        cls.clean_order_payment(payment, cleaned_input)
        charged_value = payment.captured_amount
        cls.clean_amount_to_refund(
            order, amount_to_refund, charged_value, cleaned_input
        )

        cleaned_input.update(
            {
                "include_shipping_costs": include_shipping_costs,
                "order": order,
                "payment": payment,
            }
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
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        cleaned_input = cls.clean_input(info, data.get("order"), data.get("input"))
        order = cleaned_input["order"]
        cls.check_channel_permissions(info, [order.channel_id])
        manager = get_plugin_manager_promise(info.context).get()
        try:
            app = get_app_promise(info.context).get()
            refund_fulfillment = create_refund_fulfillment(
                info.context.user,
                app,
                order,
                cleaned_input["payment"],
                cleaned_input.get("order_lines", []),
                cleaned_input.get("fulfillment_lines", []),
                manager,
                cleaned_input["amount_to_refund"],
                cleaned_input["include_shipping_costs"],
            )
        except PaymentError:
            cls.raise_error_for_payment_error()
        return cls(
            order=SyncWebhookControlContext(order),
            fulfillment=SyncWebhookControlContext(node=refund_fulfillment),
        )
