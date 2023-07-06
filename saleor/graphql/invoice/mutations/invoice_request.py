import graphene
from django.core.exceptions import ValidationError

from ....core import JobStatus
from ....invoice import events, models
from ....invoice.error_codes import InvoiceErrorCode
from ....order import events as order_events
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import InvoiceError
from ...core.utils import WebhookEventInfo
from ...order.types import Order
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Invoice
from ..utils import is_event_active_for_any_plugin


class InvoiceRequest(ModelMutation):
    order = graphene.Field(Order, description="Order related to an invoice.")

    class Meta:
        description = "Request an invoice for the order using plugin."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.INVOICE_REQUESTED,
                description="An invoice was requested.",
            )
        ]

    class Arguments:
        order_id = graphene.ID(
            required=True, description="ID of the order related to invoice."
        )
        number = graphene.String(
            required=False,
            description="Invoice number, if not provided it will be generated.",
        )

    @staticmethod
    def clean_order(order):
        if order.is_draft() or order.is_unconfirmed() or order.is_expired():
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Cannot request an invoice for draft, "
                        "unconfirmed or expired order.",
                        code=InvoiceErrorCode.INVALID_STATUS.value,
                    )
                }
            )

        if not order.billing_address:
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "Cannot request an invoice for order without billing address.",
                        code=InvoiceErrorCode.NOT_READY.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, number=None, order_id
    ):
        order = cls.get_node_or_error(info, order_id, only_type=Order, field="orderId")
        cls.check_channel_permissions(info, [order.channel_id])
        cls.clean_order(order)
        manager = get_plugin_manager_promise(info.context).get()
        if not is_event_active_for_any_plugin("invoice_request", manager.all_plugins):
            raise ValidationError(
                {
                    "orderId": ValidationError(
                        "No app or plugin is configured to handle invoice requests.",
                        code=InvoiceErrorCode.NO_INVOICE_PLUGIN.value,
                    )
                }
            )

        shallow_invoice = models.Invoice.objects.create(
            order=order,
            number=number,
        )

        invoice = manager.invoice_request(
            order=order, invoice=shallow_invoice, number=number
        )
        app = get_app_promise(info.context).get()
        if invoice and invoice.status == JobStatus.SUCCESS:
            order_events.invoice_generated_event(
                order=order,
                user=info.context.user,
                app=app,
                invoice_number=invoice.number,
            )
        else:
            order_events.invoice_requested_event(
                user=info.context.user, app=app, order=order
            )

        events.invoice_requested_event(
            user=info.context.user,
            app=app,
            order=order,
            number=number,
        )
        return InvoiceRequest(invoice=invoice, order=order)
