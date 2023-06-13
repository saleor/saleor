import graphene
from django.db import transaction

from ....order import error_codes, events
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.descriptions import (
    ADDED_IN_315,
    DEPRECATED_IN_3X_INPUT,
    DEPRECATED_IN_3X_MUTATION,
    PREVIEW_FEATURE,
)
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.types import BaseInputObjectType, Error, OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Order, OrderEvent
from .order_note_common import OrderNoteCommon
from .utils import get_webhook_handler_by_order_status

OrderNoteAddErrorCode = graphene.Enum.from_enum(error_codes.OrderNoteAddErrorCode)
OrderNoteAddErrorCode.doc_category = DOC_CATEGORY_ORDERS


class OrderNoteAddError(Error):
    code = OrderNoteAddErrorCode(description="The error code.", required=False)

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderNoteAdd(OrderNoteCommon):
    order = graphene.Field(Order, description="Order with the note added.")
    event = graphene.Field(OrderEvent, description="Order note created.")

    class Arguments(OrderNoteCommon.Arguments):
        id = graphene.ID(
            required=True,
            description="ID of the order to add a note for.",
            name="order",
        )

    class Meta:
        description = "Adds note to the order." + ADDED_IN_315 + PREVIEW_FEATURE
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderNoteAddError

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input
    ):
        order = cls.get_node_or_error(info, id, only_type=Order)
        cls.check_channel_permissions(info, [order.channel_id])
        cleaned_input = cls.clean_input(info, order, input)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        with transaction.atomic():
            event = events.order_note_added_event(
                order=order,
                user=info.context.user,
                app=app,
                message=cleaned_input["message"],
            )
            func = get_webhook_handler_by_order_status(order.status, manager)
            cls.call_event(func, order)
        return OrderNoteAdd(order=order, event=event)


class OrderAddNoteInput(BaseInputObjectType):
    message = graphene.String(
        description="Note message." + DEPRECATED_IN_3X_INPUT,
        name="message",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderAddNote(OrderNoteAdd):
    class Arguments(OrderNoteAdd.Arguments):
        input = OrderAddNoteInput(
            required=True, description="Fields required to create a note for the order."
        )

    class Meta:
        description = "Adds note to the order." + DEPRECATED_IN_3X_MUTATION
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
