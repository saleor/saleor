import datetime

from freezegun import freeze_time

from ....graphql.app.enums import CircuitBreakerState

APP_ID = 1
NAME = "total"
NOW = 1726215980
TTL_SECONDS = 60


def test_get_app_state(breaker_storage):
    # given
    status, changed_at = breaker_storage.get_app_state(APP_ID)
    assert status == CircuitBreakerState.CLOSED

    # when
    breaker_storage.set_app_state(APP_ID, CircuitBreakerState.OPEN, 100)

    # then
    status, changed_at = breaker_storage.get_app_state(APP_ID)
    assert status == CircuitBreakerState.OPEN
    assert changed_at == 100


def test_manually_clear_state_for_app(breaker_storage):
    # given
    breaker_storage.set_app_state(APP_ID, CircuitBreakerState.OPEN, 100)
    status, _ = breaker_storage.get_app_state(APP_ID)
    assert status == CircuitBreakerState.OPEN

    # when
    error = breaker_storage.clear_state_for_app(APP_ID)

    # then
    assert not error
    status, changed_at = breaker_storage.get_app_state(APP_ID)
    assert status == CircuitBreakerState.CLOSED
    assert changed_at == 0


def test_register_event(breaker_storage):
    with freeze_time(datetime.datetime.fromtimestamp(NOW, tz=datetime.UTC)):
        breaker_storage.register_event(APP_ID, NAME, TTL_SECONDS)
        assert breaker_storage.get_event_count(APP_ID, NAME) == 1

    with freeze_time(
        datetime.datetime.fromtimestamp(NOW + TTL_SECONDS - 1, tz=datetime.UTC)
    ):
        breaker_storage.register_event(APP_ID, NAME, TTL_SECONDS)
        assert breaker_storage.get_event_count(APP_ID, NAME) == 2

    with freeze_time(
        datetime.datetime.fromtimestamp(NOW + TTL_SECONDS, tz=datetime.UTC)
    ):
        breaker_storage.register_event(APP_ID, NAME, TTL_SECONDS)
        assert breaker_storage.get_event_count(APP_ID, NAME) == 2


def test_get_app_state_does_not_crash_on_redis_error(breaker_not_connected_storage):
    status, changed_at = breaker_not_connected_storage.get_app_state(APP_ID)
    assert status == CircuitBreakerState.CLOSED
    assert changed_at == 0


def test_set_app_state_does_not_crash_on_redis_error(breaker_not_connected_storage):
    assert (
        breaker_not_connected_storage.set_app_state(
            APP_ID, CircuitBreakerState.OPEN, 100
        )
        is None
    )


def test_register_event_does_not_crash_on_redis_error(
    breaker_not_connected_storage,
):
    breaker_not_connected_storage.register_event(APP_ID, NAME, 5)
