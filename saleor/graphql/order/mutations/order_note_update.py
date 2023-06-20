import graphene
from django.db import transaction

from ....order import OrderEvents, error_codes, events, models
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.types import Error
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order, OrderEvent
from .order_note_common import OrderNoteCommon
from .utils import get_webhook_handler_by_order_status

OrderNoteUpdateErrorCode = graphene.Enum.from_enum(error_codes.OrderNoteUpdateErrorCode)
OrderNoteUpdateErrorCode.doc_category = DOC_CATEGORY_ORDERS


class OrderNoteUpdateError(Error):
    code = OrderNoteUpdateErrorCode(description="The error code.", required=False)

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderNoteUpdate(OrderNoteCommon):
    order = graphene.Field(Order, description="Order with the note updated.")
    event = graphene.Field(OrderEvent, description="Order note updated.")

    class Arguments(OrderNoteCommon.Arguments):
        id = graphene.ID(
            required=True,
            description="ID of the note.",
            name="note",
        )

    class Meta:
        description = "Updates note of an order." + ADDED_IN_315 + PREVIEW_FEATURE
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderNoteUpdateError

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input
    ):
        qs = models.OrderEvent.objects.filter(
            type__in=[OrderEvents.NOTE_ADDED, OrderEvents.NOTE_UPDATED]
        ).select_related("order")
        order_event_to_update = cls.get_node_or_error(
            info, id, only_type=OrderEvent, qs=qs
        )
        order = order_event_to_update.order
        cleaned_input = cls.clean_input(info, order, input)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        with transaction.atomic():
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
