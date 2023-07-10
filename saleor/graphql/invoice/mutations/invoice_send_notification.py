from typing import cast

import graphene
from django.core.exceptions import ValidationError

from ....account.models import User
from ....core import JobStatus
from ....invoice import models
from ....invoice.error_codes import InvoiceErrorCode
from ....invoice.notifications import send_invoice
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import InvoiceError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Invoice


class InvoiceSendNotification(ModelMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an invoice to be sent.")

    class Meta:
        description = "Send an invoice notification to the customer."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.INVOICE_SENT,
                description="A notification for invoice send",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for invoice send",
            ),
        ]

    @classmethod
    def clean_instance(cls, _info: ResolveInfo, instance):
        validation_errors = {}
        if instance.status != JobStatus.SUCCESS:
            validation_errors["invoice"] = ValidationError(
                "Provided invoice is not ready to be sent.",
                code=InvoiceErrorCode.NOT_READY.value,
            )
        if not instance.url:
            validation_errors["url"] = ValidationError(
                "Provided invoice needs to have an URL.",
                code=InvoiceErrorCode.URL_NOT_SET.value,
            )
        if not instance.number:
            validation_errors["number"] = ValidationError(
                "Provided invoice needs to have an invoice number.",
                code=InvoiceErrorCode.NUMBER_NOT_SET.value,
            )
        if not instance.order.get_customer_email():
            validation_errors["order"] = ValidationError(
                "Provided invoice order needs an email address.",
                code=InvoiceErrorCode.EMAIL_NOT_SET.value,
            )

        if validation_errors:
            raise ValidationError(validation_errors)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id
    ):
        user = info.context.user
        user = cast(User, user)
        instance = cls.get_instance(info, id=id)
        cls.check_channel_permissions(info, [instance.order.channel_id])
        cls.clean_instance(info, instance)
        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        send_invoice(
            invoice=instance,
            staff_user=user,
            app=app,
            manager=manager,
        )
        return InvoiceSendNotification(invoice=instance)
