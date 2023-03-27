import graphene
from django.core.exceptions import ValidationError

from ....core.tracing import traced_atomic_transaction
from ....order import OrderEvents, events, models
from ....order.error_codes import OrderErrorCode
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_314, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, OrderError
from ...core.validators import validate_required_string_field
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order, OrderEvent
from .utils import get_webhook_handler_by_order_status


class OrderNoteUpdateInput(BaseInputObjectType):
    message = graphene.String(
        description="Note message.", name="message", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderNoteUpdate(BaseMutation):
    order = graphene.Field(Order, description="Order with the note updated.")
    event = graphene.Field(OrderEvent, description="Order note updated.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of the note.",
            name="note",
        )
        input = OrderNoteUpdateInput(
            required=True, description="Fields required to create a note for the order."
        )

    class Meta:
        description = "Updates note of an order." + ADDED_IN_314 + PREVIEW_FEATURE
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError

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
        qs = models.OrderEvent.objects.filter(
            type__in=[OrderEvents.NOTE_ADDED, OrderEvents.NOTE_UPDATED]
        )
        order_event_to_update = cls.get_node_or_error(
            info, id, only_type=OrderEvent, qs=qs
        )
        order = order_event_to_update.order
        cleaned_input = cls.clean_input(info, order, input)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            event = events.order_note_updated_event(
                order=order,
                user=info.context.user,
                app=app,
                message=cleaned_input["message"],
                related_event=order_event_to_update,
            )
            func = get_webhook_handler_by_order_status(order.status, manager)
            cls.call_event(func, order)
        return OrderNoteUpdate(order=order, event=event)
