from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from ..sqs import Channel


@pytest.mark.parametrize(
    ("eta_offset", "expected_delay"),
    [
        (timedelta(seconds=359, microseconds=84649), 359),
        # max delay for SQS
        (timedelta(minutes=16), 900),
        # no negative delays
        (-timedelta(minutes=10), 0),
    ],
)
@freeze_time("'2025-12-22T09:34:40.915351+00:00'")
def test_sqs_channel_put_delay_seconds(eta_offset, expected_delay):
    # given
    mock_sqs_client = MagicMock()
    mock_session = Mock()
    mock_session.client.return_value = mock_sqs_client

    # Create a mock connection object with all required attributes
    mock_connection = Mock()
    mock_connection._used_channel_ids = []
    mock_connection.channel_max = 5
    mock_connection.client.transport_options = {}

    queue_name = "test-queue"
    message = {
        # eta is set to 359.084649 seconds later than the frozen time above
        "headers": {"eta": (timezone.now() + eta_offset).isoformat()},
        "properties": {},
    }

    with patch("boto3.session.Session", return_value=mock_session):
        channel = Channel(mock_connection)

        # when
        channel._put(queue_name, message)

    # then
    mock_sqs_client.send_message.assert_called_once()
    call_kwargs = mock_sqs_client.send_message.call_args.kwargs
    assert "DelaySeconds" in call_kwargs

    assert call_kwargs["DelaySeconds"] == expected_delay


@freeze_time("'2025-12-22T09:34:40.915351+00:00'")
def test_sqs_channel_skips_delay_seconds_for_fifo():
    # given
    mock_sqs_client = MagicMock()
    mock_session = Mock()
    mock_session.client.return_value = mock_sqs_client

    # Create a mock connection object with all required attributes
    mock_connection = Mock()
    mock_connection._used_channel_ids = []
    mock_connection.channel_max = 5
    mock_connection.client.transport_options = {}

    queue_name = "test-queue.fifo"
    message = {
        # eta is set to 359.084649 seconds later than the frozen time above
        "headers": {"eta": (timezone.now() + timedelta(seconds=10)).isoformat()},
        "properties": {},
    }

    with patch("boto3.session.Session", return_value=mock_session):
        channel = Channel(mock_connection)

        # when
        channel._put(queue_name, message)

    # then
    mock_sqs_client.send_message.assert_called_once()
    call_kwargs = mock_sqs_client.send_message.call_args.kwargs
    # DelaySeconds is not supported for FIFO queues
    assert "DelaySeconds" not in call_kwargs
