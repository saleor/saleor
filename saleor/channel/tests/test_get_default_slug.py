import warnings

import pytest

from ..exceptions import ChannelSlugNotPassedException, NoChannelException
from ..utils import deprecation_warning_message, get_default_channel_slug_if_available


def test_get_default_channel_slug_if_available_without_channels():
    with pytest.raises(NoChannelException):
        get_default_channel_slug_if_available()


def test_get_default_channel_slug_if_available_with_one_channels(channel_USD):
    with warnings.catch_warnings(record=True) as warns:
        get_default_channel_slug_if_available()
        assert any(
            [str(warning.message) == deprecation_warning_message for warning in warns]
        )


def test_get_default_channel_slug_if_available_with_many_channels(
    channel_USD, channel_PLN
):
    with pytest.raises(ChannelSlugNotPassedException):
        get_default_channel_slug_if_available()
