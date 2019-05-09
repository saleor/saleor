"""Consul Transport.

It uses Consul.io's Key/Value store to transport messages in Queues

It uses python-consul for talking to Consul's HTTP API
"""
from __future__ import absolute_import, unicode_literals

import uuid
import socket

from collections import defaultdict
from contextlib import contextmanager

from kombu.exceptions import ChannelError
from kombu.five import Empty, monotonic
from kombu.log import get_logger
from kombu.utils.json import loads, dumps
from kombu.utils.objects import cached_property

from . import virtual

try:
    import consul
except ImportError:
    consul = None

logger = get_logger('kombu.transport.consul')

DEFAULT_PORT = 8500
DEFAULT_HOST = 'localhost'


class LockError(Exception):
    """An error occurred while trying to acquire the lock."""


class Channel(virtual.Channel):
    """Consul Channel class which talks to the Consul Key/Value store."""

    prefix = 'kombu'
    index = None
    timeout = '10s'
    session_ttl = 30

    def __init__(self, *args, **kwargs):
        if consul is None:
            raise ImportError('Missing python-consul library')

        super(Channel, self).__init__(*args, **kwargs)

        port = self.connection.client.port or self.connection.default_port
        host = self.connection.client.hostname or DEFAULT_HOST

        logger.debug('Host: %s Port: %s Timeout: %s', host, port, self.timeout)

        self.queues = defaultdict(dict)

        self.client = consul.Consul(host=host, port=int(port))

    def _lock_key(self, queue):
        return '{0}/{1}.lock'.format(self.prefix, queue)

    def _key_prefix(self, queue):
        return '{0}/{1}'.format(self.prefix, queue)

    def _get_or_create_session(self, queue):
        """Get or create consul session.

        Try to renew the session if it exists, otherwise create a new
        session in Consul.

        This session is used to acquire a lock inside Consul so that we achieve
        read-consistency between the nodes.

        Arguments:
            queue (str): The name of the Queue.

        Returns:
            str: The ID of the session.
        """
        try:
            session_id = self.queues[queue]['session_id']
        except KeyError:
            session_id = None
        return (self._renew_existing_session(session_id)
                if session_id is not None else self._create_new_session())

    def _renew_existing_session(self, session_id):
        logger.debug('Trying to renew existing session %s', session_id)
        session = self.client.session.renew(session_id=session_id)
        return session.get('ID')

    def _create_new_session(self):
        logger.debug('Creating session %s with TTL %s',
                     self.lock_name, self.session_ttl)
        session_id = self.client.session.create(
            name=self.lock_name, ttl=self.session_ttl)
        logger.debug('Created session %s with id %s',
                     self.lock_name, session_id)
        return session_id

    @contextmanager
    def _queue_lock(self, queue, raising=LockError):
        """Try to acquire a lock on the Queue.

        It does so by creating a object called 'lock' which is locked by the
        current session..

        This way other nodes are not able to write to the lock object which
        means that they have to wait before the lock is released.

        Arguments:
            queue (str): The name of the Queue.
            raising (Exception): Set custom lock error class.

        Raises:
            LockError: if the lock cannot be acquired.

        Returns:
            bool: success?
        """
        self._acquire_lock(queue, raising=raising)
        try:
            yield
        finally:
            self._release_lock(queue)

    def _acquire_lock(self, queue, raising=LockError):
        session_id = self._get_or_create_session(queue)
        lock_key = self._lock_key(queue)

        logger.debug('Trying to create lock object %s with session %s',
                     lock_key, session_id)

        if self.client.kv.put(key=lock_key,
                              acquire=session_id,
                              value=self.lock_name):
            self.queues[queue]['session_id'] = session_id
            return
        logger.info('Could not acquire lock on key %s', lock_key)
        raise raising()

    def _release_lock(self, queue):
        """Try to release a lock.

        It does so by simply removing the lock key in Consul.

        Arguments:
            queue (str): The name of the queue we want to release
                the lock from.
        """
        logger.debug('Removing lock key %s', self._lock_key(queue))
        self.client.kv.delete(key=self._lock_key(queue))

    def _destroy_session(self, queue):
        """Destroy a previously created Consul session.

        Will release all locks it still might hold.

        Arguments:
            queue (str): The name of the Queue.
        """
        logger.debug('Destroying session %s', self.queues[queue]['session_id'])
        self.client.session.destroy(self.queues[queue]['session_id'])

    def _new_queue(self, queue, **_):
        self.queues[queue] = {'session_id': None}
        return self.client.kv.put(key=self._key_prefix(queue), value=None)

    def _delete(self, queue, *args, **_):
        self._destroy_session(queue)
        self.queues.pop(queue, None)
        self._purge(queue)

    def _put(self, queue, payload, **_):
        """Put `message` onto `queue`.

        This simply writes a key to the K/V store of Consul
        """
        key = '{0}/msg/{1}_{2}'.format(
            self._key_prefix(queue),
            int(round(monotonic() * 1000)),
            uuid.uuid4(),
        )
        if not self.client.kv.put(key=key, value=dumps(payload), cas=0):
            raise ChannelError('Cannot add key {0!r} to consul'.format(key))

    def _get(self, queue, timeout=None):
        """Get the first available message from the queue.

        Before it does so it acquires a lock on the Key/Value store so
        only one node reads at the same time. This is for read consistency
        """
        with self._queue_lock(queue, raising=Empty):
            key = '{0}/msg/'.format(self._key_prefix(queue))
            logger.debug('Fetching key %s with index %s', key, self.index)
            self.index, data = self.client.kv.get(
                key=key, recurse=True,
                index=self.index, wait=self.timeout,
            )

            try:
                if data is None:
                    raise Empty()

                logger.debug('Removing key %s with modifyindex %s',
                             data[0]['Key'], data[0]['ModifyIndex'])

                self.client.kv.delete(key=data[0]['Key'],
                                      cas=data[0]['ModifyIndex'])

                return loads(data[0]['Value'])
            except TypeError:
                pass

        raise Empty()

    def _purge(self, queue):
        self._destroy_session(queue)
        return self.client.kv.delete(
            key='{0}/msg/'.format(self._key_prefix(queue)),
            recurse=True,
        )

    def _size(self, queue):
        size = 0
        try:
            key = '{0}/msg/'.format(self._key_prefix(queue))
            logger.debug('Fetching key recursively %s with index %s',
                         key, self.index)
            self.index, data = self.client.kv.get(
                key=key, recurse=True,
                index=self.index, wait=self.timeout,
            )
            size = len(data)
        except TypeError:
            pass

        logger.debug('Found %s keys under %s with index %s',
                     size, key, self.index)
        return size

    @cached_property
    def lock_name(self):
        return '{0}'.format(socket.gethostname())


class Transport(virtual.Transport):
    """Consul K/V storage Transport for Kombu."""

    Channel = Channel

    default_port = DEFAULT_PORT
    driver_type = 'consul'
    driver_name = 'consul'

    def __init__(self, *args, **kwargs):
        if consul is None:
            raise ImportError('Missing python-consul library')

        super(Transport, self).__init__(*args, **kwargs)

        self.connection_errors = (
            virtual.Transport.connection_errors + (
                consul.ConsulException, consul.base.ConsulException
            )
        )

        self.channel_errors = (
            virtual.Transport.channel_errors + (
                consul.ConsulException, consul.base.ConsulException
            )
        )

    def verify_connection(self, connection):
        port = connection.client.port or self.default_port
        host = connection.client.hostname or DEFAULT_HOST

        logger.debug('Verify Consul connection to %s:%s', host, port)

        try:
            client = consul.Consul(host=host, port=int(port))
            client.agent.self()
            return True
        except ValueError:
            pass

        return False

    def driver_version(self):
        return consul.__version__
