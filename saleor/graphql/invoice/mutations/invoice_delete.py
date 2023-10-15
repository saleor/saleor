import graphene

from ....invoice import events, models
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import ModelDeleteMutation
from ...core.types import InvoiceError
from ..types import Invoice


class InvoiceDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an invoice to delete.")

    class Meta:
        description = "Deletes an invoice."
        model = models.Invoice
        object_type = Invoice
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = InvoiceError
        error_type_field = "invoice_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        invoice = cls.get_instance(info, **data)
        cls.check_channel_permissions(info, [invoice.order.channel_id])
        response = super().perform_mutation(_root, info, **data)
        app = get_app_promise(info.context).get()
        events.invoice_deleted_event(
            user=info.context.user, app=app, invoice_id=invoice.pk
        )
        return response
