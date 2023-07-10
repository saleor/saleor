import graphene

from ....core import JobStatus
from ....invoice import events, models
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import InvoiceError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Invoice


class InvoiceRequestDelete(ModelMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of an invoice to request the deletion."
        )

    class Meta:
        description = "Requests deletion of an invoice."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.INVOICE_DELETED,
                description="An invoice was requested to delete.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id
    ):
        invoice = cls.get_node_or_error(info, id, only_type=Invoice)
        cls.check_channel_permissions(info, [invoice.order.channel_id])
        invoice.status = JobStatus.PENDING
        invoice.save(update_fields=["status", "updated_at"])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.invoice_delete, invoice)
        app = get_app_promise(info.context).get()
        events.invoice_requested_deletion_event(
            user=info.context.user, app=app, invoice=invoice
        )
        return InvoiceRequestDelete(invoice=invoice)
