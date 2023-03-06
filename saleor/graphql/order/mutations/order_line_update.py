import graphene
from django.core.exceptions import ValidationError

from ....core.exceptions import InsufficientStock
from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import models
from ....order.error_codes import OrderErrorCode
from ....order.fetch import OrderLineInfo
from ....order.utils import (
    change_order_line_quantity,
    invalidate_order_prices,
    recalculate_order_weight,
)
from ...app.dataloaders import load_app
from ...core.mutations import ModelMutation
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Order, OrderLine
from .draft_order_create import OrderLineInput
from .utils import EditableOrderValidationMixin, get_webhook_handler_by_order_status


class OrderLineUpdate(EditableOrderValidationMixin, ModelMutation):
    order = graphene.Field(Order, description="Related order.")

    class Arguments:
        id = graphene.ID(description="ID of the order line to update.", required=True)
        input = OrderLineInput(
            required=True, description="Fields required to update an order line."
        )

    class Meta:
        description = "Updates an order line of an order."
        model = models.OrderLine
        object_type = OrderLine
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        instance.old_quantity = instance.quantity
        cleaned_input = super().clean_input(info, instance, data)
        cls.validate_order(instance.order)

        quantity = data["quantity"]
        if quantity <= 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "Ensure this value is greater than 0.",
                        code=OrderErrorCode.ZERO_QUANTITY,
                    )
                }
            )
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        warehouse_pk = (
            instance.allocations.first().stock.warehouse.pk
            if instance.order.is_unconfirmed()
            else None
        )
        app = load_app(info.context)
        with traced_atomic_transaction():
            line_info = OrderLineInfo(
                line=instance,
                quantity=instance.quantity,
                variant=instance.variant,
                warehouse_pk=warehouse_pk,
            )
            try:
                change_order_line_quantity(
                    info.context.user,
                    app,
                    line_info,
                    instance.old_quantity,
                    instance.quantity,
                    instance.order.channel,
                    manager,
                )
            except InsufficientStock:
                raise ValidationError(
                    "Cannot set new quantity because of insufficient stock.",
                    code=OrderErrorCode.INSUFFICIENT_STOCK,
                )
            invalidate_order_prices(instance.order)
            recalculate_order_weight(instance.order)
            instance.order.save(update_fields=["should_refresh_prices", "weight"])

            func = get_webhook_handler_by_order_status(instance.order.status, manager)
            cls.call_event(func, instance.order)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.order = instance.order
        return response
