import logging
import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from saleor.webhook.event_types import WebhookEventSyncType

from ...graphql.app.types import CircuitBreakerState

if TYPE_CHECKING:
    from ...webhook.models import Webhook


logger = logging.getLogger(__name__)


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
        if settings.BREAKER_BOARD_SYNC_EVENTS == [""]:
            raise ImproperlyConfigured("BREAKER_BOARD_SYNC_EVENTS cannot be empty.")
        for event in settings.BREAKER_BOARD_SYNC_EVENTS:
            if not WebhookEventSyncType.EVENT_MAP.get(event):
                raise ImproperlyConfigured(
                    f'Event "{event}" is not supported by circuit breaker.'
                )

    def exceeded_error_threshold(
        self, state: CircuitBreakerState, total: int, errors: int
    ) -> bool:
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
        return errors >= min_count and (errors / total) * 100 >= threshold

    def reached_half_open_target_success_count(self, total: int, errors: int) -> bool:
        return total - errors >= self.success_count_recovery

    def _open_breaker(self, app_id: int) -> str:
        self.storage.clear_state_for_app(app_id)
        self.storage.update_open(app_id, int(time.time()), CircuitBreakerState.OPEN)
        logger.info(
            "[App ID: %r] Circuit breaker tripped, cooldown is %r [seconds].",
            app_id,
            self.cooldown_seconds,
        )
        return CircuitBreakerState.OPEN

    def _half_open_breaker(self, app_id: int) -> str:
        self.storage.clear_state_for_app(app_id)
        self.storage.update_open(
            app_id, int(time.time()), CircuitBreakerState.HALF_OPEN
        )
        logger.info(
            "[App ID: %r] Circuit breaker state changed to %s.",
            app_id,
            CircuitBreakerState.HALF_OPEN,
        )
        return CircuitBreakerState.HALF_OPEN

    def _close_breaker(self, app_id: int) -> str:
        self.storage.clear_state_for_app(app_id)
        self.storage.update_open(app_id, 0, CircuitBreakerState.CLOSED)
        logger.info(
            "[App ID: %r] Circuit breaker fully recovered.",
            app_id,
        )
        return CircuitBreakerState.CLOSED

    def update_breaker_state(self, app_id: int) -> str:
        last_open, state = self.storage.last_open(app_id)
        total = self.storage.get_event_count(app_id, "total") or 1
        errors = self.storage.get_event_count(app_id, "error")
        # CLOSED to OPEN
        if state == CircuitBreakerState.CLOSED and self.exceeded_error_threshold(
            state, total, errors
        ):
            return self._open_breaker(app_id)
        # OPEN TO HALF-OPEN
        if state == CircuitBreakerState.OPEN and last_open < (
            time.time() - self.cooldown_seconds
        ):
            return self._half_open_breaker(app_id)
        # HALF-OPEN to CLOSED / OPEN
        if state == CircuitBreakerState.HALF_OPEN:
            if self.exceeded_error_threshold(state, total, errors):
                return self._open_breaker(app_id)
            if self.reached_half_open_target_success_count(total, errors):
                return self._close_breaker(app_id)
        return state

    def register_error(self, app_id: int, ttl: int):
        self.storage.register_event(app_id, "error", self.ttl_seconds)
        self.storage.register_event(app_id, "total", self.ttl_seconds)

    def register_success(self, app_id: int, ttl: int):
        self.storage.register_event(app_id, "total", self.ttl_seconds)

    def __call__(self, func):
        def inner(*args, **kwargs):
            event_type: str = args[0]
            webhook: Webhook = args[2]

            if event_type not in settings.BREAKER_BOARD_SYNC_EVENTS:
                return func(*args, **kwargs)

            app_id = webhook.app.id
            state = self.update_breaker_state(app_id)
            if state == CircuitBreakerState.OPEN:
                if not settings.BREAKER_BOARD_DRY_RUN:
                    # Skip func execution to prevent sending webhooks
                    return None
                else:  # noqa: RET505
                    logger.debug(
                        "[App ID: %r] Sending disabled webhook due to breaker dry-run",
                        app_id,
                    )
                    return func(*args, **kwargs)

            response = func(*args, **kwargs)
            if response is None:
                self.register_error(app_id, self.ttl_seconds)
            else:
                self.register_success(app_id, self.ttl_seconds)

            return response

        inner.__wrapped__ = func  # type: ignore[attr-defined]

        return inner


def initialize_breaker_board() -> BreakerBoard | None:
    if not settings.BREAKER_BOARD_ENABLED:
        return None

    storage_class = import_string(settings.BREAKER_BOARD_STORAGE_CLASS)
    return BreakerBoard(
        storage=storage_class(),
        failure_min_count=settings.BREAKER_BOARD_FAILURE_MIN_COUNT,
        failure_threshold=settings.BREAKER_BOARD_FAILURE_THRESHOLD_PERCENTAGE,
        failure_min_count_recovery=settings.BREAKER_BOARD_FAILURE_MIN_COUNT_RECOVERY,
        failure_threshold_recovery=settings.BREAKER_BOARD_FAILURE_THRESHOLD_PERCENTAGE_RECOVERY,
        success_count_recovery=settings.BREAKER_BOARD_SUCCESS_COUNT_RECOVERY,
        cooldown_seconds=settings.BREAKER_BOARD_COOLDOWN_SECONDS,
        ttl_seconds=settings.BREAKER_BOARD_TTL_SECONDS,
    )
