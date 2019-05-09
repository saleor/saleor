"""Azure Storage Queues transport.

The transport can be enabled by setting the CELERY_BROKER_URL to:

```
azurestoragequeues://:{Storage Account Access Key}@{Storage Account Name}
```

Note that if the access key for the storage account contains a slash, it will
have to be regenerated before it can be used in the connection URL.

More information about Azure Storage Queues:
https://azure.microsoft.com/en-us/services/storage/queues/

"""
from __future__ import absolute_import, unicode_literals

import string

from kombu.five import Empty, text_t
from kombu.utils.encoding import safe_str
from kombu.utils.json import loads, dumps
from kombu.utils.objects import cached_property

from . import virtual

try:
    from azure.storage.queue import QueueService
except ImportError:  # pragma: no cover
    QueueService = None  # noqa

# Azure storage queues allow only alphanumeric and dashes
# so, replace everything with a dash
CHARS_REPLACE_TABLE = {
    ord(c): 0x2d for c in string.punctuation
}


class Channel(virtual.Channel):
    """Azure Storage Queues channel."""

    domain_format = 'kombu%(vhost)s'
    _queue_service = None
    _queue_name_cache = {}
    no_ack = True
    _noack_queues = set()

    def __init__(self, *args, **kwargs):
        if QueueService is None:
            raise ImportError('Azure Storage Queues transport requires the '
                              'azure-storage-queue library')

        super(Channel, self).__init__(*args, **kwargs)

        for queue_name in self.queue_service.list_queues():
            self._queue_name_cache[queue_name] = queue_name

    def basic_consume(self, queue, no_ack, *args, **kwargs):
        if no_ack:
            self._noack_queues.add(queue)

        return super(Channel, self).basic_consume(queue, no_ack,
                                                  *args, **kwargs)

    def entity_name(self, name, table=CHARS_REPLACE_TABLE):
        """Format AMQP queue name into a valid Azure Storage Queue name."""
        return text_t(safe_str(name)).translate(table)

    def _ensure_queue(self, queue):
        """Ensure a queue exists."""
        queue = self.entity_name(self.queue_name_prefix + queue)
        try:
            return self._queue_name_cache[queue]
        except KeyError:
            self.queue_service.create_queue(queue, fail_on_exist=False)
            q = self._queue_name_cache[queue] = queue
            return q

    def _delete(self, queue, *args, **kwargs):
        """Delete queue by name."""
        queue_name = self.entity_name(queue)
        self._queue_name_cache.pop(queue_name, None)
        self.queue_service.delete_queue(queue_name)
        super(Channel, self)._delete(queue_name)

    def _put(self, queue, message, **kwargs):
        """Put message onto queue."""
        q = self._ensure_queue(queue)
        encoded_message = dumps(message)
        self.queue_service.put_message(q, encoded_message)

    def _get(self, queue, timeout=None):
        """Try to retrieve a single message off ``queue``."""
        q = self._ensure_queue(queue)

        messages = self.queue_service.get_messages(q, num_messages=1,
                                                   timeout=timeout)
        if not messages:
            raise Empty()

        message = messages[0]
        raw_content = self.queue_service.decode_function(message.content)
        content = loads(raw_content)

        self.queue_service.delete_message(q, message.id, message.pop_receipt)

        return content

    def _size(self, queue):
        """Return the number of messages in a queue."""
        q = self._ensure_queue(queue)
        metadata = self.queue_service.get_queue_metadata(q)
        return metadata.approximate_message_count

    def _purge(self, queue):
        """Delete all current messages in a queue."""
        q = self._ensure_queue(queue)
        n = self._size(q)
        self.queue_service.clear_messages(q)
        return n

    @property
    def queue_service(self):
        if self._queue_service is None:
            self._queue_service = QueueService(
                account_name=self.conninfo.hostname,
                account_key=self.conninfo.password)

        return self._queue_service

    @property
    def conninfo(self):
        return self.connection.client

    @property
    def transport_options(self):
        return self.connection.client.transport_options

    @cached_property
    def queue_name_prefix(self):
        return self.transport_options.get('queue_name_prefix', '')


class Transport(virtual.Transport):
    """Azure Storage Queues transport."""

    Channel = Channel

    polling_interval = 1
    default_port = None
