class GiftCardSettingsExpiryType:
    NEVER_EXPIRE = "never_expire"
    EXPIRY_PERIOD = "expiry_period"

    CHOICES = [
        (NEVER_EXPIRE, "Never expire"),
        (EXPIRY_PERIOD, "Expiry period"),
    ]


class AccountConfirmMode:
    """AccountConfirmMode set the account merging mode for anonymous objects.

    This dictates the behavior of the `confirmAccount()` mutation for
    password-based authentication when attempting to merge orders & giftcard
    that aren't associated to a user account.

    Modes:

    - MERGE_DISABLED disables merging only when the authentication method
      is password (i.e., when not using OIDC)
    - REQUIRE_PASSWORD enables account merging who accounts that use password
      authentication but it requires the user to enter their password
    """

    MERGE_DISABLED = "merge_disabled"
    REQUIRE_PASSWORD = "require_password"

    CHOICES = [
        (MERGE_DISABLED, "Account merging disabled"),
        (REQUIRE_PASSWORD, "Require password for merging"),
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
