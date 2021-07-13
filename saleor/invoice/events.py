from typing import Optional

from ..account.models import User
from ..core.utils.validators import user_is_valid
from ..order.models import Order
from .models import Invoice, InvoiceEvent, InvoiceEvents

UserType = Optional[User]


def invoice_requested_event(
    *, user: UserType, order: Order, number: str
) -> InvoiceEvent:
    if not user_is_valid(user):
        user = None
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.REQUESTED,
        user=user,
        order=order,
        parameters={"number": number},
    )


def invoice_requested_deletion_event(
    *, user: UserType, invoice: Invoice
) -> InvoiceEvent:
    if not user_is_valid(user):
        user = None
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.REQUESTED_DELETION,
        user=user,
        invoice=invoice,
        order=invoice.order,
    )


def invoice_created_event(
    *, user: UserType, invoice: Invoice, number: str, url: str
) -> InvoiceEvent:
    if not user_is_valid(user):
        user = None
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.CREATED,
        user=user,
        invoice=invoice,
        order=invoice.order,
        parameters={"number": number, "url": url},
    )


def invoice_deleted_event(*, user: UserType, invoice_id: int) -> InvoiceEvent:
    if not user_is_valid(user):
        user = None
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.DELETED, user=user, parameters={"invoice_id": invoice_id}
    )


def notification_invoice_sent_event(
    *, user_id: Optional[int], invoice_id: int, customer_email: str
) -> InvoiceEvent:
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.SENT,
        user_id=user_id,
        invoice_id=invoice_id,
        parameters={"email": customer_email},  # type: ignore
    )
