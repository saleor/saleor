import datetime

from freezegun import freeze_time

from ....graphql.app.enums import CircuitBreakerState

APP_ID = 1
NAME = "total"
NOW = 1726215980
TTL_SECONDS = 60


def test_update_open(breaker_storage):
    # given
    assert breaker_storage.last_open(APP_ID) == (0, CircuitBreakerState.CLOSED)

    # when
    breaker_storage.update_open(APP_ID, 100, CircuitBreakerState.OPEN)

    # then
    assert breaker_storage.last_open(APP_ID) == (100, CircuitBreakerState.OPEN)


def test_manually_clear_state_for_app(breaker_storage):
    # given
    breaker_storage.update_open(APP_ID, 100, CircuitBreakerState.OPEN)
    assert breaker_storage.last_open(APP_ID) == (100, CircuitBreakerState.OPEN)

    # when
    error = breaker_storage.clear_state_for_app(APP_ID)

    # then
    assert not error
    assert breaker_storage.last_open(APP_ID) == (0, CircuitBreakerState.CLOSED)


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


def test_last_open_does_not_crash_on_redis_error(breaker_not_connected_storage):
    assert breaker_not_connected_storage.last_open(APP_ID) == (
        0,
        CircuitBreakerState.CLOSED,
    )


def test_update_open_does_not_crash_on_redis_error(breaker_not_connected_storage):
    breaker_not_connected_storage.update_open(APP_ID, 100, CircuitBreakerState.OPEN)
    assert breaker_not_connected_storage.last_open(APP_ID) == (
        0,
        CircuitBreakerState.CLOSED,
    )


def test_register_event_does_not_crash_on_redis_error(
    breaker_not_connected_storage,
):
    breaker_not_connected_storage.register_event(APP_ID, NAME, 5)
