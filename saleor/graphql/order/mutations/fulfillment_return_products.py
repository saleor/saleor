from typing import Any, Dict

import graphene

from ....order import FulfillmentStatus
from ....order import models as order_models
from ....order.actions import create_fulfillments_for_returned_products
from ....payment import PaymentError
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.scalars import PositiveDecimal
from ...core.types import NonNullList, OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Fulfillment, Order
from .fulfillment_refund_and_return_product_base import (
    FulfillmentRefundAndReturnProductBase,
)


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
    order_lines = NonNullList(
        OrderReturnLineInput,
        description="List of unfulfilled lines to return.",
    )
    fulfillment_lines = NonNullList(
        OrderReturnFulfillmentLineInput,
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
    def clean_input(cls, info: ResolveInfo, order_id, input):
        cleaned_input: Dict[str, Any] = {}
        amount_to_refund = input.get("amount_to_refund")
        include_shipping_costs = input["include_shipping_costs"]
        refund = input["refund"]

        qs = order_models.Order.objects.prefetch_related("payments")
        order = cls.get_node_or_error(
            info, order_id, field="order", only_type=Order, qs=qs
        )
        if refund:
            payment = order.get_last_payment()
            transactions = list(order.payment_transactions.all())
            if transactions:
                # For know we handle refunds only for last transaction. We need to add
                # an interface to process a refund requests on multiple transactions
                charged_value = transactions[-1].charged_value
            else:
                cls.clean_order_payment(payment, cleaned_input)
                charged_value = payment.captured_amount
            cls.clean_amount_to_refund(
                order, amount_to_refund, charged_value, cleaned_input
            )
            cleaned_input["transactions"] = transactions

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
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        cleaned_input = cls.clean_input(info, data.get("order"), data.get("input"))
        order = cleaned_input["order"]
        manager = get_plugin_manager_promise(info.context).get()
        try:
            app = get_app_promise(info.context).get()
            response = create_fulfillments_for_returned_products(
                info.context.user,
                app,
                order,
                cleaned_input.get("payment"),
                cleaned_input.get("transactions"),
                cleaned_input.get("order_lines", []),
                cleaned_input.get("fulfillment_lines", []),
                manager,
                cleaned_input["refund"],
                cleaned_input.get("amount_to_refund"),
                cleaned_input["include_shipping_costs"],
            )
        except PaymentError:
            cls.raise_error_for_payment_error(cleaned_input.get("transactions"))

        return_fulfillment, replace_fulfillment, replace_order = response
        return cls(
            order=order,
            return_fulfillment=return_fulfillment,
            replace_fulfillment=replace_fulfillment,
            replace_order=replace_order,
        )
