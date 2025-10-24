import uuid

from kombu.asynchronous.aws.sqs.message import AsyncMessage
from kombu.transport.SQS import Channel as SqsChannel
from kombu.transport.SQS import Transport as SqsTransport
from kombu.utils.json import dumps


class Channel(SqsChannel):
    def _put(self, queue, message, **kwargs):
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
            if "MessageGroupId" in message["properties"]:
                kwargs["MessageGroupId"] = message["properties"]["MessageGroupId"]

            if queue.endswith(".fifo"):
                if "MessageGroupId" not in kwargs:
                    kwargs["MessageGroupId"] = "default"
                if "MessageDeduplicationId" in message["properties"]:
                    kwargs["MessageDeduplicationId"] = message["properties"][
                        "MessageDeduplicationId"
                    ]
                else:
                    kwargs["MessageDeduplicationId"] = str(uuid.uuid4())
            else:
                if "DelaySeconds" in message["properties"]:
                    kwargs["DelaySeconds"] = message["properties"]["DelaySeconds"]

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
