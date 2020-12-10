from typing import Optional

from ..account.models import User
from ..order.models import Order
from .models import Invoice, InvoiceEvent, InvoiceEvents

UserType = Optional[User]


def _user_is_valid(user: UserType) -> bool:
    return bool(user and not user.is_anonymous)


def invoice_requested_event(
    *, user: UserType, order: Order, number: str
) -> InvoiceEvent:
    if not _user_is_valid(user):
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
    if not _user_is_valid(user):
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
    if not _user_is_valid(user):
        user = None
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.CREATED,
        user=user,
        invoice=invoice,
        order=invoice.order,
        parameters={"number": number, "url": url},
    )


def invoice_deleted_event(*, user: UserType, invoice_id: int) -> InvoiceEvent:
    if not _user_is_valid(user):
        user = None
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.DELETED, user=user, parameters={"invoice_id": invoice_id}
    )


def invoice_sent_event(*, user: UserType, invoice: Invoice) -> InvoiceEvent:
    if not _user_is_valid(user):
        user = None
    return InvoiceEvent.objects.create(
        type=InvoiceEvents.SENT,
        user=user,
        invoice=invoice,
        parameters={"email": invoice.order.get_customer_email()},  # type: ignore
    )
