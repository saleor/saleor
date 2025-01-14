from ..account.models import User
from ..app.models import App
from ..order.models import Order
from .models import Invoice, InvoiceEvent, InvoiceEvents


def invoice_requested_event(
    *, user: User | None, app: App | None, order: Order, number: str | None
) -> InvoiceEvent:
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.REQUESTED,
        user=user,
        app=app,
        order=order,
        parameters={"number": number},
    )


def invoice_requested_deletion_event(
    *, user: User | None, app: App | None, invoice: Invoice
) -> InvoiceEvent:
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.REQUESTED_DELETION,
        user=user,
        app=app,
        invoice=invoice,
        order=invoice.order,
    )


def invoice_created_event(
    *, user: User | None, app: App | None, invoice: Invoice, number: str, url: str
) -> InvoiceEvent:
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.CREATED,
        user=user,
        app=app,
        invoice=invoice,
        order=invoice.order,
        parameters={"number": number, "url": url},
    )


def invoice_deleted_event(
    *, user: User | None, app: App | None, invoice_id: int
) -> InvoiceEvent:
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.DELETED,
        user=user,
        app=app,
        parameters={"invoice_id": invoice_id},
    )


def notification_invoice_sent_event(
    *,
    user_id: int | None,
    app_id: int | None,
    invoice_id: int,
    customer_email: str,
) -> InvoiceEvent:
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.SENT,
        user_id=user_id,
        app_id=app_id,
        invoice_id=invoice_id,
        parameters={"email": customer_email},
    )
