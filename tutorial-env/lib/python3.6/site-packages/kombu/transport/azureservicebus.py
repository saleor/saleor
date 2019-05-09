"""Azure Service Bus Message Queue transport.

The transport can be enabled by setting the CELERY_BROKER_URL to:

```
azureservicebus://{SAS policy name}:{SAS key}@{Service Bus Namespace}
```

Note that the Shared Access Policy used to connect to Azure Service Bus
requires Manage, Send and Listen claims since the broker will create new
queues and delete old queues as required.

Note that if the SAS key for the Service Bus account contains a slash, it will
have to be regenerated before it can be used in the connection URL.

More information about Azure Service Bus:
https://azure.microsoft.com/en-us/services/service-bus/

"""
from __future__ import absolute_import, unicode_literals

import string

from kombu.five import Empty, text_t
from kombu.utils.encoding import bytes_to_str, safe_str
from kombu.utils.json import loads, dumps
from kombu.utils.objects import cached_property

from . import virtual

try:
    # azure-servicebus version <= 0.21.1
    from azure.servicebus import ServiceBusService, Message, Queue
except ImportError:
    try:
        # azure-servicebus version >= 0.50.0
        from azure.servicebus.control_client import \
            ServiceBusService, Message, Queue
    except ImportError:
        ServiceBusService = Message = Queue = None

# dots are replaced by dash, all other punctuation replaced by underscore.
CHARS_REPLACE_TABLE = {
    ord(c): 0x5f for c in string.punctuation if c not in '_'
}


class Channel(virtual.Channel):
    """Azure Service Bus channel."""

    default_visibility_timeout = 1800  # 30 minutes.
    domain_format = 'kombu%(vhost)s'
    _queue_service = None
    _queue_cache = {}

    def __init__(self, *args, **kwargs):
        if ServiceBusService is None:
            raise ImportError('Azure Service Bus transport requires the '
                              'azure-servicebus library')

        super(Channel, self).__init__(*args, **kwargs)

        for queue in self.queue_service.list_queues():
            self._queue_cache[queue] = queue

    def entity_name(self, name, table=CHARS_REPLACE_TABLE):
        """Format AMQP queue name into a valid ServiceBus queue name."""
        return text_t(safe_str(name)).translate(table)

    def _new_queue(self, queue, **kwargs):
        """Ensure a queue exists in ServiceBus."""
        queue = self.entity_name(self.queue_name_prefix + queue)
        try:
            return self._queue_cache[queue]
        except KeyError:
            self.queue_service.create_queue(queue, fail_on_exist=False)
            q = self._queue_cache[queue] = self.queue_service.get_queue(queue)
            return q

    def _delete(self, queue, *args, **kwargs):
        """Delete queue by name."""
        queue_name = self.entity_name(queue)
        self._queue_cache.pop(queue_name, None)
        self.queue_service.delete_queue(queue_name)
        super(Channel, self)._delete(queue_name)

    def _put(self, queue, message, **kwargs):
        """Put message onto queue."""
        msg = Message(dumps(message))
        self.queue_service.send_queue_message(self.entity_name(queue), msg)

    def _get(self, queue, timeout=None):
        """Try to retrieve a single message off ``queue``."""
        message = self.queue_service.receive_queue_message(
            self.entity_name(queue), timeout=timeout, peek_lock=False)

        if message.body is None:
            raise Empty()

        return loads(bytes_to_str(message.body))

    def _size(self, queue):
        """Return the number of messages in a queue."""
        return self._new_queue(queue).message_count

    def _purge(self, queue):
        """Delete all current messages in a queue."""
        n = 0

        while True:
            message = self.queue_service.read_delete_queue_message(
                self.entity_name(queue), timeout=0.1)

            if not message.body:
                break
            else:
                n += 1

        return n

    @property
    def queue_service(self):
        if self._queue_service is None:
            self._queue_service = ServiceBusService(
                service_namespace=self.conninfo.hostname,
                shared_access_key_name=self.conninfo.userid,
                shared_access_key_value=self.conninfo.password)

        return self._queue_service

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


class Transport(virtual.Transport):
    """Azure Service Bus transport."""

    Channel = Channel

    polling_interval = 1
    default_port = None
