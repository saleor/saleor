class PasswordLoginMode:
    """Controls whether password-based authentication is allowed.

    ENABLED - any user can log in with a password. This is the default behavior.
    CUSTOMERS_ONLY - only customer users can log in with a password.
        If a staff user logs in with a password, they will be treated as a customer
        — the issued token will not contain any staff permissions.
    DISABLED - no user can log in with a password. The tokenCreate mutation returns an error.
    """

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
