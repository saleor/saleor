import logging
from importlib.metadata import entry_points
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.metrics import NoOpMeterProvider

from .. import initialize_telemetry, instrument_libraries

DEFAULT_INSTRUMENTORS = [
    "psycopg",
    "celery",
    "redis",
    "requests",
    "botocore",
    "threading",
]


class Invalid:
    pass


def test_initialize_telemetry_invalid_tracer_class(settings):
    settings.TELEMETRY_TRACER_CLASS = "saleor.core.telemetry.tests.test_init.Invalid"

    with pytest.raises(
        ValueError,
        match="settings.TELEMETRY_TRACER_CLASS must point to a subclass of Tracer",
    ):
        initialize_telemetry()


def test_initialize_telemetry_invalid_meter_class(settings):
    settings.TELEMETRY_METER_CLASS = "saleor.core.telemetry.tests.test_init.Invalid"

    with pytest.raises(
        ValueError,
        match="settings.TELEMETRY_METER_CLASS must point to a subclass of Meter",
    ):
        initialize_telemetry()


@patch("saleor.core.telemetry.instrument_libraries")
def test_initialize_telemetry_instruments_configured_libraries(
    mocked_instrument_libraries, settings
):
    settings.TELEMETRY_INSTRUMENTORS = ["psycopg", "redis"]

    initialize_telemetry()

    mocked_instrument_libraries.assert_called_once_with(["psycopg", "redis"])


def fake_instrumentor_cls(already_instrumented=False):
    instrumentor_cls = MagicMock()
    instrumentor_cls.return_value.is_instrumented_by_opentelemetry = (
        already_instrumented
    )
    return instrumentor_cls


def fake_entry_points(instrumentors):
    def _entry_points(*, group, name):
        assert group == "opentelemetry_instrumentor"
        if name not in instrumentors:
            return ()
        entry_point = MagicMock()
        entry_point.load.return_value = instrumentors[name]
        return (entry_point,)

    return _entry_points


def test_instrument_libraries_instruments_each_name():
    psycopg_cls, redis_cls = fake_instrumentor_cls(), fake_instrumentor_cls()

    with patch(
        "saleor.core.telemetry.entry_points",
        fake_entry_points({"psycopg": psycopg_cls, "redis": redis_cls}),
    ):
        instrument_libraries(["psycopg", "redis"])

    for instrumentor_cls in (psycopg_cls, redis_cls):
        instrumentor_cls.assert_called_once_with()
        instrumentor_cls.return_value.instrument.assert_called_once()
        kwargs = instrumentor_cls.return_value.instrument.call_args.kwargs
        assert isinstance(kwargs["meter_provider"], NoOpMeterProvider)


def test_instrument_libraries_skips_unknown_name(caplog):
    redis_cls = fake_instrumentor_cls()

    with (
        caplog.at_level(logging.ERROR),
        patch(
            "saleor.core.telemetry.entry_points",
            fake_entry_points({"redis": redis_cls}),
        ),
    ):
        instrument_libraries(["unknown", "redis"])

    assert "Telemetry instrumentor not found: unknown" in caplog.text
    redis_cls.return_value.instrument.assert_called_once()


def test_instrument_libraries_skips_failing_instrumentor(caplog):
    psycopg_cls, redis_cls = fake_instrumentor_cls(), fake_instrumentor_cls()
    psycopg_cls.return_value.instrument.side_effect = RuntimeError("boom")

    with (
        caplog.at_level(logging.ERROR),
        patch(
            "saleor.core.telemetry.entry_points",
            fake_entry_points({"psycopg": psycopg_cls, "redis": redis_cls}),
        ),
    ):
        instrument_libraries(["psycopg", "redis"])

    assert "Telemetry instrumentor failed to set up: psycopg" in caplog.text
    assert "boom" in caplog.text
    redis_cls.return_value.instrument.assert_called_once()


def test_instrument_libraries_skips_already_instrumented(caplog):
    psycopg_cls = fake_instrumentor_cls(already_instrumented=True)
    redis_cls = fake_instrumentor_cls()

    with (
        caplog.at_level(logging.WARNING),
        patch(
            "saleor.core.telemetry.entry_points",
            fake_entry_points({"psycopg": psycopg_cls, "redis": redis_cls}),
        ),
    ):
        instrument_libraries(["psycopg", "redis"])

    assert (
        "Telemetry instrumentor already set up outside Saleor: psycopg" in caplog.text
    )
    psycopg_cls.return_value.instrument.assert_not_called()
    redis_cls.return_value.instrument.assert_called_once()


def test_instrument_libraries_with_no_names():
    with patch("saleor.core.telemetry.entry_points") as mocked_entry_points:
        instrument_libraries([])

    mocked_entry_points.assert_not_called()


@pytest.mark.parametrize("name", DEFAULT_INSTRUMENTORS)
def test_default_instrumentors_are_installed(name):
    assert entry_points(group="opentelemetry_instrumentor", name=name)
