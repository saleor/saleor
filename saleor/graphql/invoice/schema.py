import graphene

from .mutations import (
    CreateInvoice,
    DeleteInvoice,
    RequestDeleteInvoice,
    RequestInvoice,
    SendInvoiceEmail,
    UpdateInvoice,
)


class InvoiceMutations(graphene.ObjectType):
    request_invoice = RequestInvoice.Field()
    request_delete_invoice = RequestDeleteInvoice.Field()
    create_invoice = CreateInvoice.Field()
    delete_invoice = DeleteInvoice.Field()
    update_invoice = UpdateInvoice.Field()
    send_invoice_email = SendInvoiceEmail.Field()
