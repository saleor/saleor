from typing import Any

import graphene

from ....order import FulfillmentStatus
from ....order import models as order_models
from ....order.actions import create_fulfillments_for_returned_products
from ....order.error_codes import OrderErrorCode
from ....payment import PaymentError
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.context import SyncWebhookControlContext
from ...core.descriptions import ADDED_IN_322
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.scalars import PositiveDecimal
from ...core.types import BaseInputObjectType, NonNullList, OrderError
from ...payment.utils import (
    resolve_reason_reference_page,
    validate_and_resolve_refund_reason_context,
)
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
from ..types import Fulfillment, Order
from .fulfillment_refund_and_return_product_base import (
    FulfillmentRefundAndReturnProductBase,
)


class OrderReturnLineInput(BaseInputObjectType):
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
    reason = graphene.String(
        description="Reason for returning the line." + ADDED_IN_322
    )
    reason_reference = graphene.ID(
        description=(
            "ID of a `Page` to reference as reason for returning this line. "
            "When provided, must match the configured `PageType` in refund settings. "
            "Always optional for both staff and apps."
        )
        + ADDED_IN_322
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderReturnFulfillmentLineInput(BaseInputObjectType):
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
    reason = graphene.String(
        description="Reason for returning the line." + ADDED_IN_322
    )
    reason_reference = graphene.ID(
        description=(
            "ID of a `Page` to reference as reason for returning this line. "
            "When provided, must match the configured `PageType` in refund settings. "
            "Always optional for both staff and apps."
        )
        + ADDED_IN_322
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderReturnProductsInput(BaseInputObjectType):
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
    reason = graphene.String(description="Global reason for the return." + ADDED_IN_322)
    reason_reference = graphene.ID(
        description=(
            "ID of a `Page` to reference as reason for the return. "
            "Required for staff users when refund reason reference type is configured. "
            "Always optional for apps."
        )
        + ADDED_IN_322
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


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
        doc_category = DOC_CATEGORY_ORDERS
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
        cleaned_input: dict[str, Any] = {}
        amount_to_refund = input.get("amount_to_refund")
        include_shipping_costs = input["include_shipping_costs"]
        refund = input["refund"]
        reason = input.get("reason") or ""
        reason_reference_id = input.get("reason_reference")

        qs = order_models.Order.objects.prefetch_related("payments")
        order = cls.get_node_or_error(
            info, order_id, field="order", only_type=Order, qs=qs
        )
        if refund:
            payment = order.get_last_payment()
            cls.clean_order_payment(payment, cleaned_input)
            charged_value = payment.captured_amount
            cls.clean_amount_to_refund(
                order, amount_to_refund, charged_value, cleaned_input
            )

        # Validate global reason reference
        requestor_is_app = info.context.app is not None
        requestor_is_user = info.context.user is not None and not requestor_is_app

        site = get_site_promise(info.context).get()

        refund_reason_context = validate_and_resolve_refund_reason_context(
            reason_reference_id=reason_reference_id,
            requestor_is_user=bool(requestor_is_user),
            refund_reference_field_name="reason_reference",
            error_code_enum=OrderErrorCode,
            site_settings=site.settings,
        )

        reason_reference_instance = None
        if refund_reason_context["should_apply"]:
            reason_reference_instance = resolve_reason_reference_page(
                str(reason_reference_id),
                refund_reason_context["refund_reason_reference_type"].pk,
                OrderErrorCode,
            )

        cleaned_input.update(
            {
                "include_shipping_costs": include_shipping_costs,
                "order": order,
                "refund": refund,
                "reason": reason,
                "reason_reference_instance": reason_reference_instance,
            }
        )

        order_lines_data = input.get("order_lines")
        fulfillment_lines_data = input.get("fulfillment_lines")

        if order_lines_data:
            cls.clean_lines(
                order_lines_data, cleaned_input, site_settings=site.settings
            )
        if fulfillment_lines_data:
            cls.clean_fulfillment_lines(
                fulfillment_lines_data,
                cleaned_input,
                whitelisted_statuses=[
                    FulfillmentStatus.FULFILLED,
                    FulfillmentStatus.REFUNDED,
                    FulfillmentStatus.WAITING_FOR_APPROVAL,
                ],
                site_settings=site.settings,
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
            response = create_fulfillments_for_returned_products(
                info.context.user,
                app,
                order,
                cleaned_input.get("payment"),
                cleaned_input.get("order_lines", []),
                cleaned_input.get("fulfillment_lines", []),
                manager,
                cleaned_input["refund"],
                cleaned_input.get("amount_to_refund"),
                cleaned_input["include_shipping_costs"],
                reason=cleaned_input.get("reason", ""),
                reason_reference=cleaned_input.get("reason_reference_instance"),
            )
        except PaymentError:
            cls.raise_error_for_payment_error()

        return_fulfillment, replace_fulfillment, replace_order = response
        return_fulfillment_response = SyncWebhookControlContext(node=return_fulfillment)
        replace_fulfillment_response = (
            SyncWebhookControlContext(node=replace_fulfillment)
            if replace_fulfillment
            else None
        )
        replace_order_response = (
            SyncWebhookControlContext(node=replace_order) if replace_order else None
        )
        return cls(
            order=SyncWebhookControlContext(order),
            return_fulfillment=return_fulfillment_response,
            replace_fulfillment=replace_fulfillment_response,
            replace_order=replace_order_response,
        )
