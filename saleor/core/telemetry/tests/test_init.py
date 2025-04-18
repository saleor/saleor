import pytest

from .. import initialize_telemetry


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
