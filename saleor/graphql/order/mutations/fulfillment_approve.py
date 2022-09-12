import graphene
from django.core.exceptions import ValidationError

from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....order import FulfillmentStatus
from ....order.actions import approve_fulfillment
from ....order.error_codes import OrderErrorCode
from ...app.dataloaders import load_app
from ...core.descriptions import ADDED_IN_31
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...site.dataloaders import load_site
from ..types import Fulfillment, Order
from ..utils import prepare_insufficient_stock_order_validation_errors
from .order_fulfill import OrderFulfill


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
        description = "Approve existing fulfillment." + ADDED_IN_31
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
        site = load_site(info.context)
        if (
            not site.settings.fulfillment_allow_unpaid
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
        app = load_app(info.context)
        site = load_site(info.context)
        try:
            fulfillment = approve_fulfillment(
                fulfillment,
                info.context.user,
                app,
                info.context.plugins,
                site.settings,
                notify_customer=data["notify_customer"],
                allow_stock_to_be_exceeded=data.get("allow_stock_to_be_exceeded"),
            )
        except InsufficientStock as exc:
            errors = prepare_insufficient_stock_order_validation_errors(exc)
            raise ValidationError({"stocks": errors})

        order.refresh_from_db(fields=["status"])
        return FulfillmentApprove(fulfillment=fulfillment, order=order)
