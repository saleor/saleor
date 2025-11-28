from typing import Final

import graphene

from ...app.types import AppType
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


def breaker_description(enum):
    if enum is None:
        return "Enum determining the state of a circuit breaker."
    if enum == CircuitBreakerStateEnum.CLOSED:
        return "The breaker is conducting (requests are passing through)."
    if enum == CircuitBreakerStateEnum.HALF_OPEN:
        return (
            "The breaker is in a trial period (to close or open). "
            "Note that unlike classic breaker patterns, this is not a state "
            "where we are throttling the number of requests, it's a state "
            "similar to CLOSED but with different thresholds."
        )
    if enum == CircuitBreakerStateEnum.OPEN:
        return (
            "The breaker is tripped (no requests are passing). "
            "Breaker will enter half-open state after cooldown period."
        )
    return None


class CircuitBreakerState:
    CLOSED = "closed"
    HALF_OPEN = "half_open"
    OPEN = "open"

    CHOICES = [
        (CLOSED, "closed"),
        (HALF_OPEN, "half_open"),
        (OPEN, "open"),
    ]


CircuitBreakerStateEnum: Final[graphene.Enum] = to_enum(
    CircuitBreakerState, description=breaker_description
)
CircuitBreakerStateEnum.doc_category = DOC_CATEGORY_APPS

AppTypeEnum: Final[graphene.Enum] = to_enum(AppType, description=description)
AppTypeEnum.doc_category = DOC_CATEGORY_APPS
