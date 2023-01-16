import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import events
from ....order.error_codes import OrderErrorCode
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...core.validators import validate_required_string_field
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order, OrderEvent
from .utils import get_webhook_handler_by_order_status


class OrderAddNoteInput(graphene.InputObjectType):
    message = graphene.String(
        description="Note message.", name="message", required=True
    )


class OrderAddNote(BaseMutation):
    order = graphene.Field(Order, description="Order with the note added.")
    event = graphene.Field(OrderEvent, description="Order note created.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of the order to add a note for.",
            name="order",
        )
        input = OrderAddNoteInput(
            required=True, description="Fields required to create a note for the order."
        )

    class Meta:
        description = "Adds note to the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_input(cls, _info, _instance, data):
        try:
            cleaned_input = validate_required_string_field(data, "message")
        except ValidationError:
            raise ValidationError(
                {
                    "message": ValidationError(
                        "Message can't be empty.",
                        code=OrderErrorCode.REQUIRED.value,
                    )
                }
            )
        return cleaned_input

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input
    ):
        order = cls.get_node_or_error(info, id, only_type=Order)
        cleaned_input = cls.clean_input(info, order, input)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            event = events.order_note_added_event(
                order=order,
                user=info.context.user,
                app=app,
                message=cleaned_input["message"],
            )
            func = get_webhook_handler_by_order_status(order.status, manager)
            cls.call_event(func, order)
        return OrderAddNote(order=order, event=event)
