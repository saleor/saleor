class PasswordLoginMode:
    ENABLED = "enabled"
    CUSTOMERS_ONLY = "customers_only"
    DISABLED = "disabled"

    CHOICES = [
        (ENABLED, "Enabled"),
        (CUSTOMERS_ONLY, "Customers only"),
        (DISABLED, "Disabled"),
    ]


class GiftCardSettingsExpiryType:
    NEVER_EXPIRE = "never_expire"
    EXPIRY_PERIOD = "expiry_period"

    CHOICES = [
        (NEVER_EXPIRE, "Never expire"),
        (EXPIRY_PERIOD, "Expiry period"),
    ]
