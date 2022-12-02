import warnings

import pytest

from ..exceptions import ChannelNotDefined, NoDefaultChannel
from ..utils import DEPRECATION_WARNING_MESSAGE, get_default_channel


def test_get_default_channel_without_channels():
    with pytest.raises(NoDefaultChannel):
        get_default_channel()


def test_get_default_channel_with_one_channels(channel_USD):
    with warnings.catch_warnings(record=True) as warns:
        get_default_channel()
        assert any(
            [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
        )


def test_get_default_channel_with_many_channels(channel_USD, channel_PLN):
    with pytest.raises(ChannelNotDefined):
        get_default_channel()
