import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....giftcard.utils import order_has_gift_card_lines
from ....order import FulfillmentStatus
from ....order.actions import cancel_fulfillment, cancel_waiting_fulfillment
from ....order.error_codes import OrderErrorCode
from ...app.dataloaders import load_app
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Fulfillment, Order


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

        app = load_app(info.context)
        manager = load_plugin_manager(info.context)
        if fulfillment.status == FulfillmentStatus.WAITING_FOR_APPROVAL:
            fulfillment = cancel_waiting_fulfillment(
                fulfillment,
                info.context.user,
                app,
                manager,
            )
        else:
            fulfillment = cancel_fulfillment(
                fulfillment,
                info.context.user,
                app,
                warehouse,
                manager,
            )
        order.refresh_from_db(fields=["status"])
        return FulfillmentCancel(fulfillment=fulfillment, order=order)
