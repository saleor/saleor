from ...app.types import AppExtensionMount, AppExtensionTarget, AppType
from ..core.doc_category import DOC_CATEGORY_APPS
from ..core.enums import to_enum


def description(enum):
    if enum is None:
        return "Enum determining type of your App."
    if enum == AppTypeEnum.LOCAL:
        return (
            "Local Saleor App. The app is fully manageable from dashboard. "
            "You can change assigned permissions, add webhooks, "
            "or authentication token"
        )
    if enum == AppTypeEnum.THIRDPARTY:
        return (
            "Third party external App. Installation is fully automated. "
            "Saleor uses a defined App manifest to gather all required information."
        )
    return None


class CircuitBreakerState:
    # CLOSED state means the breaker is conducting (requests are passing through).
    CLOSED = "closed"
    # HALF_OPEN state means the breaker is in a trial period (to close or open).
    # Requests are passing through in that state but the thresholds are different.
    HALF_OPEN = "half_open"
    # OPEN state means the breaker is tripped (no requests are passing).
    OPEN = "open"

    CHOICES = [
        (CLOSED, "closed"),
        (HALF_OPEN, "half_open"),
        (OPEN, "open"),
    ]


CircuitBreakerStateEnum = to_enum(CircuitBreakerState)
CircuitBreakerStateEnum.doc_category = DOC_CATEGORY_APPS

AppTypeEnum = to_enum(AppType, description=description)
AppTypeEnum.doc_category = DOC_CATEGORY_APPS

AppExtensionMountEnum = to_enum(
    AppExtensionMount, description=AppExtensionMount.__doc__
)
AppExtensionMountEnum.doc_category = DOC_CATEGORY_APPS

AppExtensionTargetEnum = to_enum(
    AppExtensionTarget, description=AppExtensionTarget.__doc__
)
AppExtensionTargetEnum.doc_category = DOC_CATEGORY_APPS
