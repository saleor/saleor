import base64
import json
from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from celery import Task
from celery._state import _task_stack
from celery.app.trace import build_tracer
from celery.utils.threads import LocalStack
from django.utils import timezone
from freezegun import freeze_time

from ...celeryconf import app
from ..sqs import Channel


class DummyTask(Task):
    request_stack = LocalStack()


@app.task
def replacement_task():
    pass


@app.task(bind=True)
def replaced_task(self):
    raise self.replace(replacement_task.s())


@pytest.fixture
def sqs_client():
    return MagicMock()


@pytest.fixture
def sqs_channel(sqs_client):
    session = Mock()
    session.client.return_value = sqs_client
    connection = Mock()
    connection._used_channel_ids = []
    connection.channel_max = 5
    connection.client.transport_options = {}
    with patch("boto3.session.Session", return_value=session):
        yield Channel(connection)


@pytest.fixture
def executing_task():
    """Make a task the currently executing one, the way a Celery worker does."""
    task = DummyTask()

    def start(**request):
        task.push_request(**request)
        _task_stack.push(task)
        return task

    yield start
    if _task_stack.top is task:
        _task_stack.pop()
        task.pop_request()


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


def test_sqs_channel_put_retried_task_keeps_message_group_id(
    sqs_client, sqs_channel, executing_task
):
    # given
    task_id = "task-id"
    message_group_id = "example.com:app"
    executing_task(id=task_id, properties={"MessageGroupId": message_group_id})
    message = {"headers": {"id": task_id}, "properties": {}}

    # when
    sqs_channel._put("test-queue", message)

    # then
    sqs_client.send_message.assert_called_once()
    send_message_kwargs = sqs_client.send_message.call_args.kwargs
    assert send_message_kwargs["MessageGroupId"] == message_group_id
    # the worker reads the properties from the body, so the next retry needs it there
    published_message = json.loads(base64.b64decode(send_message_kwargs["MessageBody"]))
    assert published_message["properties"]["MessageGroupId"] == message_group_id


def test_sqs_channel_put_replacement_task_keeps_message_group_id(sqs_broker_client):
    # given
    task_id = "task-id"
    message_group_id = "example.com:app"
    # run the task the way a Celery worker does, so the replacement is really
    # published
    trace_task = build_tracer(replaced_task.name, replaced_task, app=app)

    # when
    trace_task(
        task_id,
        (),
        {},
        request={
            "id": task_id,
            "properties": {"MessageGroupId": message_group_id},
        },
    )

    # then
    sqs_broker_client.send_message.assert_called_once()
    send_message_kwargs = sqs_broker_client.send_message.call_args.kwargs
    assert send_message_kwargs["MessageGroupId"] == message_group_id
    published_message = json.loads(base64.b64decode(send_message_kwargs["MessageBody"]))
    assert published_message["headers"]["task"] == replacement_task.name
    # `Task.replace()` publishes the replacement under the ID of the replaced task
    assert published_message["headers"]["id"] == task_id
    assert published_message["properties"]["MessageGroupId"] == message_group_id


def test_sqs_channel_put_explicit_message_group_id_wins_over_retried_task(
    sqs_client, sqs_channel, executing_task
):
    # given
    task_id = "task-id"
    message_group_id = "example.com:explicit"
    executing_task(id=task_id, properties={"MessageGroupId": "example.com:app"})
    message = {
        "headers": {"id": task_id},
        "properties": {"MessageGroupId": message_group_id},
    }

    # when
    sqs_channel._put("test-queue", message)

    # then
    sqs_client.send_message.assert_called_once()
    send_message_kwargs = sqs_client.send_message.call_args.kwargs
    assert send_message_kwargs["MessageGroupId"] == message_group_id


@pytest.mark.parametrize(
    ("_case", "request_kwargs", "message"),
    [
        (
            "new task published by the executing task",
            {"id": "task-id", "properties": {"MessageGroupId": "example.com:app"}},
            {"headers": {"id": "other-task-id"}, "properties": {}},
        ),
        (
            "message without headers",
            {"id": "task-id", "properties": {"MessageGroupId": "example.com:app"}},
            {"properties": {}},
        ),
        (
            "executing task without message properties",
            {"id": "task-id", "properties": None},
            {"headers": {"id": "task-id"}, "properties": {}},
        ),
        (
            "executing task without group ID",
            {"id": "task-id", "properties": {}},
            {"headers": {"id": "task-id"}, "properties": {}},
        ),
    ],
)
def test_sqs_channel_put_does_not_inherit_message_group_id(
    _case, request_kwargs, message, sqs_client, sqs_channel, executing_task
):
    # given
    executing_task(**request_kwargs)

    # when
    sqs_channel._put("test-queue", message)

    # then
    sqs_client.send_message.assert_called_once()
    assert "MessageGroupId" not in sqs_client.send_message.call_args.kwargs


def test_sqs_channel_put_without_executing_task(sqs_client, sqs_channel):
    # given
    message = {"headers": {"id": "task-id"}, "properties": {}}

    # when
    sqs_channel._put("test-queue", message)

    # then
    sqs_client.send_message.assert_called_once()
    assert "MessageGroupId" not in sqs_client.send_message.call_args.kwargs
