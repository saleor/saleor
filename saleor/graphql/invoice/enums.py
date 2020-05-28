class InvoiceStatus:
    PENDING = "pending"
    PENDING_DELETE = "pending_delete"
    DELETED = "deleted"
    READY = "ready"

    CHOICES = [
        (PENDING, "pending"),
        (PENDING_DELETE, "pending_delete"),
        (DELETED, "deleted"),
        (READY, "ready"),
    ]
