class GiftCardExpiryType:
    """The gift card expiry options."""

    NEVER_EXPIRE = "never-expiry"
    EXPIRY_PERIOD = "expiry-period"
    EXPIRY_DATE = "expiry-date"

    CHOICES = [
        (NEVER_EXPIRE, "Never expire"),
        (EXPIRY_PERIOD, "Expiry period"),
        (EXPIRY_DATE, "Expiry date"),
    ]
