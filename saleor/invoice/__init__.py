class InvoiceEvents:
    REQUESTED = "requested"
    REQUESTED_DELETION = "requested_deletion"
    CREATED = "created"
    DELETED = "deleted"
    SENT = "sent"

    CHOICES = [
        (REQUESTED, "The invoice was requested"),
        (REQUESTED_DELETION, "The invoice was requested for deletion"),
        (CREATED, "The invoice was created"),
        (DELETED, "The invoice was deleted"),
        (SENT, "The invoice has been sent"),
    ]
