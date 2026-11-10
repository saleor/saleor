import uuid
from datetime import datetime
from typing import Any

from celery import current_task
from django.utils import timezone
from kombu.asynchronous.aws.sqs.message import AsyncMessage
from kombu.transport.SQS import Channel as SqsChannel
from kombu.transport.SQS import Transport as SqsTransport
from kombu.utils.json import dumps


def get_retried_task_message_group_id(message: dict[str, Any]) -> str | None:
    """Return the `MessageGroupId` of the executing task if `message` is its retry.

    `Task.retry()` rebuilds the publish options from the task request and drops
    custom message properties, so a retried message would lose the group ID it was
    first published with. A retry is republished under the same task ID, which is
    how it is told apart from a new task published by the executing one.
    """
    if not current_task:
        return None
    request = current_task.request
    task_id = (message.get("headers") or {}).get("id")
    if task_id is None or task_id != request.id:
        return None
    return (request.properties or {}).get("MessageGroupId")


class Channel(SqsChannel):
    def _put(self, queue: str, message: dict[str, Any], **kwargs):
        """Put message onto queue."""
        q_url = self._new_queue(queue)
        kwargs = {"QueueUrl": q_url}

        if "properties" in message:
            if "message_attributes" in message["properties"]:
                # we don't want to want to have the attribute in the body
                kwargs["MessageAttributes"] = message["properties"].pop(
                    "message_attributes"
                )

            # Mitigation of https://github.com/celery/kombu/issues/2400
            # Allows passing MessageGroupId for non-FIFO queues
            message_group_id = message["properties"].get("MessageGroupId")
            if message_group_id is None:
                message_group_id = get_retried_task_message_group_id(message)
                if message_group_id is not None:
                    # Keep it in the message body, which is where the worker
                    # reads the properties from, so the next retry inherits it too.
                    message["properties"]["MessageGroupId"] = message_group_id
            if message_group_id is not None:
                kwargs["MessageGroupId"] = message_group_id

            if queue.endswith(".fifo"):
                if "MessageGroupId" not in kwargs:
                    kwargs["MessageGroupId"] = "default"
                if "MessageDeduplicationId" in message["properties"]:
                    kwargs["MessageDeduplicationId"] = message["properties"][
                        "MessageDeduplicationId"
                    ]
                else:
                    kwargs["MessageDeduplicationId"] = str(uuid.uuid4())
            elif headers := message.get("headers"):
                if eta := headers.get("eta"):
                    datetime_eta = datetime.fromisoformat(eta)
                    delay_in_seconds = max(
                        0, int((datetime_eta - timezone.now()).total_seconds())
                    )
                    # 900 is max delay for SQS
                    kwargs["DelaySeconds"] = min(delay_in_seconds, 900)

        if self.sqs_base64_encoding:
            body = AsyncMessage().encode(dumps(message))
        else:
            body = dumps(message)
        kwargs["MessageBody"] = body

        c = self.sqs(queue=self.canonical_queue_name(queue))
        if message.get("redelivered"):
            c.change_message_visibility(
                QueueUrl=q_url,
                ReceiptHandle=message["properties"]["delivery_tag"],
                VisibilityTimeout=self.wait_time_seconds,
            )
        else:
            c.send_message(**kwargs)


class Transport(SqsTransport):
    Channel = Channel
