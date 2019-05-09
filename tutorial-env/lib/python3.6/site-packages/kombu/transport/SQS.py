"""Amazon SQS Transport.

Amazon SQS transport module for Kombu.  This package implements an AMQP-like
interface on top of Amazons SQS service, with the goal of being optimized for
high performance and reliability.

The default settings for this module are focused now on high performance in
task queue situations where tasks are small, idempotent and run very fast.

SQS Features supported by this transport:
  Long Polling:
    https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-long-polling.html

    Long polling is enabled by setting the `wait_time_seconds` transport
    option to a number > 1.  Amazon supports up to 20 seconds.  This is
    enabled with 10 seconds by default.

  Batch API Actions:
   https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-batch-api.html

    The default behavior of the SQS Channel.drain_events() method is to
    request up to the 'prefetch_count' messages on every request to SQS.
    These messages are stored locally in a deque object and passed back
    to the Transport until the deque is empty, before triggering a new
    API call to Amazon.

    This behavior dramatically speeds up the rate that you can pull tasks
    from SQS when you have short-running tasks (or a large number of workers).

    When a Celery worker has multiple queues to monitor, it will pull down
    up to 'prefetch_count' messages from queueA and work on them all before
    moving on to queueB.  If queueB is empty, it will wait up until
    'polling_interval' expires before moving back and checking on queueA.
"""  # noqa: E501

from __future__ import absolute_import, unicode_literals

import base64
import socket
import string
import uuid

from vine import transform, ensure_promise, promise

from kombu.asynchronous import get_event_loop
from kombu.asynchronous.aws.ext import boto3, exceptions
from kombu.asynchronous.aws.sqs.connection import AsyncSQSConnection
from kombu.asynchronous.aws.sqs.message import AsyncMessage
from kombu.five import Empty, range, string_t, text_t
from kombu.log import get_logger
from kombu.utils import scheduling
from kombu.utils.encoding import bytes_to_str, safe_str
from kombu.utils.json import loads, dumps
from kombu.utils.objects import cached_property

from . import virtual

logger = get_logger(__name__)

# dots are replaced by dash, dash remains dash, all other punctuation
# replaced by underscore.
CHARS_REPLACE_TABLE = {
    ord(c): 0x5f for c in string.punctuation if c not in '-_.'
}
CHARS_REPLACE_TABLE[0x2e] = 0x2d  # '.' -> '-'

#: SQS bulk get supports a maximum of 10 messages at a time.
SQS_MAX_MESSAGES = 10


def maybe_int(x):
    """Try to convert x' to int, or return x' if that fails."""
    try:
        return int(x)
    except ValueError:
        return x


class Channel(virtual.Channel):
    """SQS Channel."""

    default_region = 'us-east-1'
    default_visibility_timeout = 1800  # 30 minutes.
    default_wait_time_seconds = 10  # up to 20 seconds max
    domain_format = 'kombu%(vhost)s'
    _asynsqs = None
    _sqs = None
    _queue_cache = {}
    _noack_queues = set()

    def __init__(self, *args, **kwargs):
        if boto3 is None:
            raise ImportError('boto3 is not installed')
        super(Channel, self).__init__(*args, **kwargs)

        # SQS blows up if you try to create a new queue when one already
        # exists but with a different visibility_timeout.  This prepopulates
        # the queue_cache to protect us from recreating
        # queues that are known to already exist.
        self._update_queue_cache(self.queue_name_prefix)

        self.hub = kwargs.get('hub') or get_event_loop()

    def _update_queue_cache(self, queue_name_prefix):
        resp = self.sqs.list_queues(QueueNamePrefix=queue_name_prefix)
        for url in resp.get('QueueUrls', []):
            queue_name = url.split('/')[-1]
            self._queue_cache[queue_name] = url

    def basic_consume(self, queue, no_ack, *args, **kwargs):
        if no_ack:
            self._noack_queues.add(queue)
        if self.hub:
            self._loop1(queue)
        return super(Channel, self).basic_consume(
            queue, no_ack, *args, **kwargs
        )

    def basic_cancel(self, consumer_tag):
        if consumer_tag in self._consumers:
            queue = self._tag_to_queue[consumer_tag]
            self._noack_queues.discard(queue)
        return super(Channel, self).basic_cancel(consumer_tag)

    def drain_events(self, timeout=None, callback=None, **kwargs):
        """Return a single payload message from one of our queues.

        Raises:
            Queue.Empty: if no messages available.
        """
        # If we're not allowed to consume or have no consumers, raise Empty
        if not self._consumers or not self.qos.can_consume():
            raise Empty()

        # At this point, go and get more messages from SQS
        self._poll(self.cycle, callback, timeout=timeout)

    def _reset_cycle(self):
        """Reset the consume cycle.

        Returns:
            FairCycle: object that points to our _get_bulk() method
                rather than the standard _get() method.  This allows for
                multiple messages to be returned at once from SQS (
                based on the prefetch limit).
        """
        self._cycle = scheduling.FairCycle(
            self._get_bulk, self._active_queues, Empty,
        )

    def entity_name(self, name, table=CHARS_REPLACE_TABLE):
        """Format AMQP queue name into a legal SQS queue name."""
        if name.endswith('.fifo'):
            partial = name[:-len('.fifo')]
            partial = text_t(safe_str(partial)).translate(table)
            return partial + '.fifo'
        else:
            return text_t(safe_str(name)).translate(table)

    def canonical_queue_name(self, queue_name):
        return self.entity_name(self.queue_name_prefix + queue_name)

    def _new_queue(self, queue, **kwargs):
        """Ensure a queue with given name exists in SQS."""
        if not isinstance(queue, string_t):
            return queue
        # Translate to SQS name for consistency with initial
        # _queue_cache population.
        queue = self.canonical_queue_name(queue)

        # The SQS ListQueues method only returns 1000 queues.  When you have
        # so many queues, it's possible that the queue you are looking for is
        # not cached.  In this case, we could update the cache with the exact
        # queue name first.
        if queue not in self._queue_cache:
            self._update_queue_cache(queue)
        try:
            return self._queue_cache[queue]
        except KeyError:
            attributes = {'VisibilityTimeout': str(self.visibility_timeout)}
            if queue.endswith('.fifo'):
                attributes['FifoQueue'] = 'true'

            resp = self._create_queue(queue, attributes)
            self._queue_cache[queue] = resp['QueueUrl']
            return resp['QueueUrl']

    def _create_queue(self, queue_name, attributes):
        """Create an SQS queue with a given name and nominal attributes."""
        # Allow specifying additional boto create_queue Attributes
        # via transport options
        attributes.update(
            self.transport_options.get('sqs-creation-attributes') or {},
        )

        return self.sqs.create_queue(
            QueueName=queue_name,
            Attributes=attributes,
        )

    def _delete(self, queue, *args, **kwargs):
        """Delete queue by name."""
        super(Channel, self)._delete(queue)
        self._queue_cache.pop(queue, None)

    def _put(self, queue, message, **kwargs):
        """Put message onto queue."""
        q_url = self._new_queue(queue)
        kwargs = {'QueueUrl': q_url,
                  'MessageBody': AsyncMessage().encode(dumps(message))}
        if queue.endswith('.fifo'):
            if 'MessageGroupId' in message['properties']:
                kwargs['MessageGroupId'] = \
                    message['properties']['MessageGroupId']
            else:
                kwargs['MessageGroupId'] = 'default'
            if 'MessageDeduplicationId' in message['properties']:
                kwargs['MessageDeduplicationId'] = \
                    message['properties']['MessageDeduplicationId']
            else:
                kwargs['MessageDeduplicationId'] = str(uuid.uuid4())
        if message.get('redelivered'):
            self.sqs.change_message_visibility(
                QueueUrl=q_url,
                ReceiptHandle=message['properties']['delivery_tag'],
                VisibilityTimeout=0
            )
        else:
            self.sqs.send_message(**kwargs)

    def _message_to_python(self, message, queue_name, queue):
        try:
            body = base64.b64decode(message['Body'].encode())
        except TypeError:
            body = message['Body'].encode()
        payload = loads(bytes_to_str(body))
        if queue_name in self._noack_queues:
            queue = self._new_queue(queue_name)
            self.asynsqs.delete_message(queue, message['ReceiptHandle'])
        else:
            try:
                properties = payload['properties']
                delivery_info = payload['properties']['delivery_info']
            except KeyError:
                # json message not sent by kombu?
                delivery_info = {}
                properties = {'delivery_info': delivery_info}
                payload.update({
                    'body': bytes_to_str(body),
                    'properties': properties,
                })
            # set delivery tag to SQS receipt handle
            delivery_info.update({
                'sqs_message': message, 'sqs_queue': queue,
            })
            properties['delivery_tag'] = message['ReceiptHandle']
        return payload

    def _messages_to_python(self, messages, queue):
        """Convert a list of SQS Message objects into Payloads.

        This method handles converting SQS Message objects into
        Payloads, and appropriately updating the queue depending on
        the 'ack' settings for that queue.

        Arguments:
            messages (SQSMessage): A list of SQS Message objects.
            queue (str): Name representing the queue they came from.

        Returns:
            List: A list of Payload objects
        """
        q = self._new_queue(queue)
        return [self._message_to_python(m, queue, q) for m in messages]

    def _get_bulk(self, queue,
                  max_if_unlimited=SQS_MAX_MESSAGES, callback=None):
        """Try to retrieve multiple messages off ``queue``.

        Where :meth:`_get` returns a single Payload object, this method
        returns a list of Payload objects.  The number of objects returned
        is determined by the total number of messages available in the queue
        and the number of messages the QoS object allows (based on the
        prefetch_count).

        Note:
            Ignores QoS limits so caller is responsible for checking
            that we are allowed to consume at least one message from the
            queue.  get_bulk will then ask QoS for an estimate of
            the number of extra messages that we can consume.

        Arguments:
            queue (str): The queue name to pull from.

        Returns:
            List[Message]
        """
        # drain_events calls `can_consume` first, consuming
        # a token, so we know that we are allowed to consume at least
        # one message.

        # Note: ignoring max_messages for SQS with boto3
        max_count = self._get_message_estimate()
        if max_count:
            q_url = self._new_queue(queue)
            resp = self.sqs.receive_message(
                QueueUrl=q_url, MaxNumberOfMessages=max_count,
                WaitTimeSeconds=self.wait_time_seconds)
            if resp.get('Messages'):
                for m in resp['Messages']:
                    m['Body'] = AsyncMessage(body=m['Body']).decode()
                for msg in self._messages_to_python(resp['Messages'], queue):
                    self.connection._deliver(msg, queue)
                return
        raise Empty()

    def _get(self, queue):
        """Try to retrieve a single message off ``queue``."""
        q_url = self._new_queue(queue)
        resp = self.sqs.receive_message(
            QueueUrl=q_url, MaxNumberOfMessages=1,
            WaitTimeSeconds=self.wait_time_seconds)
        if resp.get('Messages'):
            body = AsyncMessage(body=resp['Messages'][0]['Body']).decode()
            resp['Messages'][0]['Body'] = body
            return self._messages_to_python(resp['Messages'], queue)[0]
        raise Empty()

    def _loop1(self, queue, _=None):
        self.hub.call_soon(self._schedule_queue, queue)

    def _schedule_queue(self, queue):
        if queue in self._active_queues:
            if self.qos.can_consume():
                self._get_bulk_async(
                    queue, callback=promise(self._loop1, (queue,)),
                )
            else:
                self._loop1(queue)

    def _get_message_estimate(self, max_if_unlimited=SQS_MAX_MESSAGES):
        maxcount = self.qos.can_consume_max_estimate()
        return min(
            max_if_unlimited if maxcount is None else max(maxcount, 1),
            max_if_unlimited,
        )

    def _get_bulk_async(self, queue,
                        max_if_unlimited=SQS_MAX_MESSAGES, callback=None):
        maxcount = self._get_message_estimate()
        if maxcount:
            return self._get_async(queue, maxcount, callback=callback)
        # Not allowed to consume, make sure to notify callback..
        callback = ensure_promise(callback)
        callback([])
        return callback

    def _get_async(self, queue, count=1, callback=None):
        q = self._new_queue(queue)
        qname = self.canonical_queue_name(queue)
        return self._get_from_sqs(
            qname, count=count, connection=self.asynsqs,
            callback=transform(self._on_messages_ready, callback, q, queue),
        )

    def _on_messages_ready(self, queue, qname, messages):
        if 'Messages' in messages and messages['Messages']:
            callbacks = self.connection._callbacks
            for msg in messages['Messages']:
                msg_parsed = self._message_to_python(msg, qname, queue)
                callbacks[qname](msg_parsed)

    def _get_from_sqs(self, queue,
                      count=1, connection=None, callback=None):
        """Retrieve and handle messages from SQS.

        Uses long polling and returns :class:`~vine.promises.promise`.
        """
        connection = connection if connection is not None else queue.connection
        return connection.receive_message(
            queue, number_messages=count,
            wait_time_seconds=self.wait_time_seconds,
            callback=callback,
        )

    def _restore(self, message,
                 unwanted_delivery_info=('sqs_message', 'sqs_queue')):
        for unwanted_key in unwanted_delivery_info:
            # Remove objects that aren't JSON serializable (Issue #1108).
            message.delivery_info.pop(unwanted_key, None)
        return super(Channel, self)._restore(message)

    def basic_ack(self, delivery_tag, multiple=False):
        try:
            message = self.qos.get(delivery_tag).delivery_info
            sqs_message = message['sqs_message']
        except KeyError:
            pass
        else:
            self.sqs.delete_message(QueueUrl=message['sqs_queue'],
                                    ReceiptHandle=sqs_message['ReceiptHandle'])
        super(Channel, self).basic_ack(delivery_tag)

    def _size(self, queue):
        """Return the number of messages in a queue."""
        url = self._new_queue(queue)
        resp = self.sqs.get_queue_attributes(
            QueueUrl=url,
            AttributeNames=['ApproximateNumberOfMessages'])
        return int(resp['Attributes']['ApproximateNumberOfMessages'])

    def _purge(self, queue):
        """Delete all current messages in a queue."""
        q = self._new_queue(queue)
        # SQS is slow at registering messages, so run for a few
        # iterations to ensure messages are detected and deleted.
        size = 0
        for i in range(10):
            size += int(self._size(queue))
            if not size:
                break
        self.sqs.purge_queue(QueueUrl=q)
        return size

    def close(self):
        super(Channel, self).close()
        # if self._asynsqs:
        #     try:
        #         self.asynsqs.close()
        #     except AttributeError as exc:  # FIXME ???
        #         if "can't set attribute" not in str(exc):
        #             raise

    @property
    def sqs(self):
        if self._sqs is None:
            session = boto3.session.Session(
                region_name=self.region,
                aws_access_key_id=self.conninfo.userid,
                aws_secret_access_key=self.conninfo.password,
            )
            is_secure = self.is_secure if self.is_secure is not None else True
            client_kwargs = {
                'use_ssl': is_secure
            }
            if self.endpoint_url is not None:
                client_kwargs['endpoint_url'] = self.endpoint_url
            self._sqs = session.client('sqs', **client_kwargs)
        return self._sqs

    @property
    def asynsqs(self):
        if self._asynsqs is None:
            self._asynsqs = AsyncSQSConnection(
                sqs_connection=self.sqs,
                region=self.region
            )
        return self._asynsqs

    @property
    def conninfo(self):
        return self.connection.client

    @property
    def transport_options(self):
        return self.connection.client.transport_options

    @cached_property
    def visibility_timeout(self):
        return (self.transport_options.get('visibility_timeout') or
                self.default_visibility_timeout)

    @cached_property
    def queue_name_prefix(self):
        return self.transport_options.get('queue_name_prefix', '')

    @cached_property
    def supports_fanout(self):
        return False

    @cached_property
    def region(self):
        return (self.transport_options.get('region') or
                boto3.Session().region_name or
                self.default_region)

    @cached_property
    def regioninfo(self):
        return self.transport_options.get('regioninfo')

    @cached_property
    def is_secure(self):
        return self.transport_options.get('is_secure')

    @cached_property
    def port(self):
        return self.transport_options.get('port')

    @cached_property
    def endpoint_url(self):
        if self.conninfo.hostname is not None:
            scheme = 'https' if self.is_secure else 'http'
            if self.conninfo.port is not None:
                port = ':{}'.format(self.conninfo.port)
            else:
                port = ''
            return '{}://{}{}'.format(
                scheme,
                self.conninfo.hostname,
                port
            )

    @cached_property
    def wait_time_seconds(self):
        return self.transport_options.get('wait_time_seconds',
                                          self.default_wait_time_seconds)


class Transport(virtual.Transport):
    """SQS Transport.

    Additional queue attributes can be supplied to SQS during queue
    creation by passing an ``sqs-creation-attributes`` key in
    transport_options. ``sqs-creation-attributes`` must be a dict whose
    key-value pairs correspond with Attributes in the
    `CreateQueue SQS API`_.

    For example, to have SQS queues created with server-side encryption
    enabled using the default Amazon Managed Customer Master Key, you
    can set ``KmsMasterKeyId`` Attribute. When the queue is initially
    created by Kombu, encryption will be enabled.

    .. code-block:: python

        from kombu.transport.SQS import Transport

        transport = Transport(
            ...,
            transport_options={
                'sqs-creation-attributes': {
                    'KmsMasterKeyId': 'alias/aws/sqs',
                },
            }
        )

    .. _CreateQueue SQS API: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_CreateQueue.html#API_CreateQueue_RequestParameters
    """  # noqa: E501

    Channel = Channel

    polling_interval = 1
    wait_time_seconds = 0
    default_port = None
    connection_errors = (
        virtual.Transport.connection_errors +
        (exceptions.BotoCoreError, socket.error)
    )
    channel_errors = (
        virtual.Transport.channel_errors + (exceptions.BotoCoreError,)
    )
    driver_type = 'sqs'
    driver_name = 'sqs'

    implements = virtual.Transport.implements.extend(
        asynchronous=True,
        exchange_type=frozenset(['direct']),
    )

    @property
    def default_connection_params(self):
        return {'port': self.default_port}
