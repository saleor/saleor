from datetime import timedelta
from unittest import mock

from django.utils import timezone

from ..usage_telemetry import get_usage_telemetry, send_usage_telemetry_task


def test_get_usage_telemetry(site_settings):
    # given
    site_settings.usage_telemetry_reported_at = None
    site_settings.save(update_fields=["usage_telemetry_reported_at"])

    expected_instance_keys = {
        "instance_id",
        "python_version",
        "saleor_version",
        "is_debug",
        "is_local",
    }

    expected_usage_keys = {
        "app_count",
        "attribute_count",
        "attribute_entity_type_count",
        "attribute_type_count",
        "attribute_input_type_count",
        "attribute_page_count",
        "attribute_variant_count",
        "attribute_product_count",
        "channel_count",
        "currencies",
        "model_count",
        "product_count",
        "saleor_apps",
    }

    # when
    data = get_usage_telemetry()

    # then
    assert data is not None

    assert "reported_at" in data

    instance = data["instance"]
    assert set(instance.keys()) == expected_instance_keys

    usage = data["usage"]
    assert set(usage.keys()) == expected_usage_keys


def test_get_usage_telemetry_checks_reported_at(site_settings, settings):
    # given
    site_settings.usage_telemetry_reported_at = timezone.now() - timedelta(days=30)
    site_settings.save(update_fields=["usage_telemetry_reported_at"])

    assert settings.SEND_USAGE_TELEMETRY_AFTER_TIMEDELTA.days < 30

    # when
    data = get_usage_telemetry()

    # then
    assert data is not None
