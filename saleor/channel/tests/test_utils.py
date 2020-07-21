import warnings

import pytest

from ..exceptions import ChannelSlugNotPassedException, NoChannelException
from ..utils import (
    DEPRECATION_WARNING_MESSAGE,
    get_channel_slug,
    get_default_channel_slug_if_available,
)


def test_get_default_channel_slug_if_available_without_channels():
    with pytest.raises(NoChannelException):
        get_default_channel_slug_if_available()


def test_get_default_channel_slug_if_available_with_one_channels(channel_USD):
    with warnings.catch_warnings(record=True) as warns:
        get_default_channel_slug_if_available()
        assert any(
            [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
        )


def test_get_default_channel_slug_if_available_with_many_channels(
    channel_USD, channel_PLN
):
    with pytest.raises(ChannelSlugNotPassedException):
        get_default_channel_slug_if_available()


def test_get_channel_slug_without_slug(channel_USD):
    result = get_channel_slug(None)

    assert result == channel_USD.slug


def test_get_channel_slug_without_slug_many_channels(channel_USD, channel_PLN):
    with pytest.raises(ChannelSlugNotPassedException):
        get_channel_slug(None)


def test_get_channel_slug_no_slug_without_channel():
    assert get_channel_slug(None) is None
