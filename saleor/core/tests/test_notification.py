import pytest
from django.core.exceptions import ValidationError

from ...core.notification.validation import validate_and_get_channel
from ...graphql.notifications.error_codes import ExternalNotificationErrorCodes


def test_validate_and_get_channel_for_non_existing_slug():
    with pytest.raises(ValidationError):
        validate_and_get_channel(
            {"channel": "test-slug"}, ExternalNotificationErrorCodes
        )


def test_validate_and_get_channel_for_inactive_channel(channel_PLN):
    channel_PLN.is_active = False
    channel_PLN.save()
    assert not channel_PLN.is_active
    with pytest.raises(ValidationError):
        validate_and_get_channel(
            {"channel": channel_PLN.slug}, ExternalNotificationErrorCodes
        )


def test_validate_and_get_channel_for_lack_of_input():
    with pytest.raises(ValidationError):
        validate_and_get_channel({}, ExternalNotificationErrorCodes)


def test_validate_and_get_channel(channel_PLN):
    result = validate_and_get_channel(
        {"channel": channel_PLN.slug}, ExternalNotificationErrorCodes
    )
    assert result == channel_PLN.slug
