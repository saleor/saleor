import logging
import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from ...graphql.app.enums import CircuitBreakerState
from ...webhook.event_types import WebhookEventSyncType

if TYPE_CHECKING:
    from ...app.models import App
    from ...webhook.models import Webhook

BREAKER_BOARD_LOGGER_NAME = "breaker_board"
logger = logging.getLogger(BREAKER_BOARD_LOGGER_NAME)


# Time frame for webhook events to be analyzed by the breaker board.
BREAKER_BOARD_TTL_SECONDS: int = 5 * 60

# Minimum webhook failure count (within TTL) required to open circuit breaker.
BREAKER_BOARD_FAILURE_MIN_COUNT: int = 100

# Minimum webhook failures percentage (within TTL) required to open circuit breaker.
BREAKER_BOARD_FAILURE_THRESHOLD_PERCENTAGE: int = 35

# Minimum webhook failure count (within TTL) required to re-open circuit breaker in half-open state.
BREAKER_BOARD_FAILURE_MIN_COUNT_RECOVERY: int = 20

# Minimum webhook failures percentage (within TTL) required to re-open circuit breaker in half-open state.
BREAKER_BOARD_FAILURE_THRESHOLD_PERCENTAGE_RECOVERY: int = 30

# Minimum webhook success count (within TTL) required to fully recover (close half-opened circuit breaker).
BREAKER_BOARD_SUCCESS_COUNT_RECOVERY: int = 50

# Time to keep circuit breaker in opened state before starting recovery (half-open state).
BREAKER_BOARD_COOLDOWN_SECONDS: int = 2 * 60


class BreakerBoard:
    """Base class for breaker board implementations.

    Breaker board serves as single point of entry for different Webhooks from different
    Apps. Basing on the input it checks appropriate circuit breaker state and controls
    webhook execution.
    """

    def __init__(
        self,
        storage,
        failure_min_count: int,
        failure_threshold: int,
        failure_min_count_recovery: int,
        failure_threshold_recovery: int,
        success_count_recovery: int,
        cooldown_seconds: int,
        ttl_seconds: int,
    ):
        self.validate_sync_events()
        self.storage = storage
        self.failure_min_count = failure_min_count
        self.failure_min_count_recovery = failure_min_count_recovery
        self.success_count_recovery = success_count_recovery
        self.failure_threshold = failure_threshold
        self.failure_threshold_recovery = failure_threshold_recovery
        self.cooldown_seconds = cooldown_seconds
        self.ttl_seconds = ttl_seconds

    def validate_sync_events(self):
        if not settings.BREAKER_BOARD_SYNC_EVENTS:
            raise ImproperlyConfigured("BREAKER_BOARD_SYNC_EVENTS cannot be empty.")
        for event in settings.BREAKER_BOARD_SYNC_EVENTS:
            if not WebhookEventSyncType.EVENT_MAP.get(event):
                raise ImproperlyConfigured(
                    f'Event "{event}" is not supported by circuit breaker.'
                )
        for event in settings.BREAKER_BOARD_DRY_RUN_SYNC_EVENTS:
            if event not in settings.BREAKER_BOARD_SYNC_EVENTS:
                raise ImproperlyConfigured(
                    f'Dry-run event "{event}" is not monitored by circuit breaker.'
                )

    def exceeded_error_threshold(
        self, state: str, total_webhook_calls: int, errors: int
    ) -> bool:
        """Check if the error threshold has been exceeded.

        min_count and threshold (percentage) are different in different states.
        If min count is met and the percentage of errors is greater than the threshold,
        the breaker should be tripped (go to open state).
        """
        min_count = (
            self.failure_min_count_recovery
            if state == CircuitBreakerState.HALF_OPEN
            else self.failure_min_count
        )
        threshold = (
            self.failure_threshold_recovery
            if state == CircuitBreakerState.HALF_OPEN
            else self.failure_threshold
        )
        return errors >= min_count and (errors / total_webhook_calls) * 100 >= threshold

    def reached_half_open_target_success_count(self, total: int, errors: int) -> bool:
        return total - errors >= self.success_count_recovery

    def set_breaker_state(self, app: "App", state: str, total: int, errors: int) -> str:
        self.storage.clear_state_for_app(app.id)

        changed_at = int(time.time())
        self.storage.set_app_state(app.id, state, changed_at)

        logger.info(
            "[App ID: %r] Circuit breaker changed state to %s.",
            app.id,
            state,
            extra={
                "app_name": app.name,
                "webhooks_total_count": total,
                "webhooks_errors_count": errors,
                "webhooks_cooldown_seconds": self.cooldown_seconds,
            },
        )
        return state

    def update_breaker_state(self, app: "App") -> str:
        state, changed_at = self.storage.get_app_state(app.id)

        total = self.storage.get_event_count(app.id, "total") or 1
        errors = self.storage.get_event_count(app.id, "error")
        # CLOSED to OPEN
        if state == CircuitBreakerState.CLOSED and self.exceeded_error_threshold(
            state, total, errors
        ):
            return self.set_breaker_state(app, CircuitBreakerState.OPEN, total, errors)
        # OPEN TO HALF-OPEN
        if state == CircuitBreakerState.OPEN and changed_at < (
            time.time() - self.cooldown_seconds
        ):
            return self.set_breaker_state(
                app, CircuitBreakerState.HALF_OPEN, total, errors
            )
        # HALF-OPEN to CLOSED / OPEN
        if state == CircuitBreakerState.HALF_OPEN:
            if self.exceeded_error_threshold(state, total, errors):
                return self.set_breaker_state(
                    app, CircuitBreakerState.OPEN, total, errors
                )
            if self.reached_half_open_target_success_count(total, errors):
                return self.set_breaker_state(
                    app, CircuitBreakerState.CLOSED, total, errors
                )
        return state

    def register_error(self, app_id: int):
        self.storage.register_event(app_id, "error", self.ttl_seconds)
        self.storage.register_event(app_id, "total", self.ttl_seconds)

    def register_success(self, app_id: int):
        self.storage.register_event(app_id, "total", self.ttl_seconds)

    def __call__(self, func):
        def inner(*args, **kwargs):
            event_type: str = kwargs.get("event_type") or args[0]
            webhook: Webhook = kwargs.get("webhook") or args[2]

            if event_type not in settings.BREAKER_BOARD_SYNC_EVENTS:
                # Execute webhook without affecting breaker state
                return func(*args, **kwargs)

            app = webhook.app
            state = self.update_breaker_state(app)
            if state == CircuitBreakerState.OPEN:
                if event_type not in settings.BREAKER_BOARD_DRY_RUN_SYNC_EVENTS:
                    # Skip func execution to prevent sending webhooks
                    return None
                else:  # noqa: RET505
                    # Dry-run: execute webhook, but ignore result (pretend it's skipped)
                    return func(*args, **kwargs)

            response = func(*args, **kwargs)
            if response is None:
                self.register_error(app.id)
            else:
                self.register_success(app.id)

            return response

        inner.__wrapped__ = func  # type: ignore[attr-defined]

        return inner


def initialize_breaker_board() -> BreakerBoard | None:
    if not settings.BREAKER_BOARD_ENABLED:
        return None

    storage_class = import_string(settings.BREAKER_BOARD_STORAGE_CLASS)
    return BreakerBoard(
        storage=storage_class(),
        failure_min_count=BREAKER_BOARD_FAILURE_MIN_COUNT,
        failure_threshold=BREAKER_BOARD_FAILURE_THRESHOLD_PERCENTAGE,
        failure_min_count_recovery=BREAKER_BOARD_FAILURE_MIN_COUNT_RECOVERY,
        failure_threshold_recovery=BREAKER_BOARD_FAILURE_THRESHOLD_PERCENTAGE_RECOVERY,
        success_count_recovery=BREAKER_BOARD_SUCCESS_COUNT_RECOVERY,
        cooldown_seconds=BREAKER_BOARD_COOLDOWN_SECONDS,
        ttl_seconds=BREAKER_BOARD_TTL_SECONDS,
    )
