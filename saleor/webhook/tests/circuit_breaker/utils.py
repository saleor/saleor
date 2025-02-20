from saleor.webhook.circuit_breaker.breaker_board import BreakerBoard


def create_breaker_board(
    storage,
    failure_min_count=0,
    failure_threshold=1,
    failure_min_count_recovery=0,
    failure_threshold_recovery=1,
    success_count_recovery=10,
    cooldown_seconds=10,
    ttl_seconds=10,
):
    return BreakerBoard(
        storage=storage,
        failure_min_count=failure_min_count,
        failure_threshold=failure_threshold,
        failure_min_count_recovery=failure_min_count_recovery,
        failure_threshold_recovery=failure_threshold_recovery,
        success_count_recovery=success_count_recovery,
        cooldown_seconds=cooldown_seconds,
        ttl_seconds=ttl_seconds,
    )
