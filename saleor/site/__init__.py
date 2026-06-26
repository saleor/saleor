class GiftCardSettingsExpiryType:
    NEVER_EXPIRE = "never_expire"
    EXPIRY_PERIOD = "expiry_period"

    CHOICES = [
        (NEVER_EXPIRE, "Never expire"),
        (EXPIRY_PERIOD, "Expiry period"),
    ]


class AnnouncementImportance:
    """Defines a shop-level announcement's level/severity."""

    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNSET = "unset"

    CHOICES = [
        (CRITICAL, "Critical"),
        (HIGH, "High"),
        (MODERATE, "Moderate"),
        (LOW, "Low"),
        (UNSET, "Unset"),
    ]
