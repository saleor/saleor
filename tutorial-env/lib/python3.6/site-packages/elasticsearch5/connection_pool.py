import time
import random
import logging
import threading

try:
    from Queue import PriorityQueue, Empty
except ImportError:
    from queue import PriorityQueue, Empty

from .exceptions import ImproperlyConfigured

logger = logging.getLogger('elasticsearch')

class ConnectionSelector(object):
    """
    Simple class used to select a connection from a list of currently live
    connection instances. In init time it is passed a dictionary containing all
    the connections' options which it can then use during the selection
    process. When the `select` method is called it is given a list of
    *currently* live connections to choose from.

    The options dictionary is the one that has been passed to
    :class:`~elasticsearch.Transport` as `hosts` param and the same that is
    used to construct the Connection object itself. When the Connection was
    created from information retrieved from the cluster via the sniffing
    process it will be the dictionary returned by the `host_info_callback`.

    Example of where this would be useful is a zone-aware selector that would
    only select connections from it's own zones and only fall back to other
    connections where there would be none in it's zones.
    """
    def __init__(self, opts):
        """
        :arg opts: dictionary of connection instances and their options
        """
        self.connection_opts = opts

    def select(self, connections):
        """
        Select a connection from the given list.

        :arg connections: list of live connections to choose from
        """
        pass


class RandomSelector(ConnectionSelector):
    """
    Select a connection at random
    """
    def select(self, connections):
        return random.choice(connections)


class RoundRobinSelector(ConnectionSelector):
    """
    Selector using round-robin.
    """
    def __init__(self, opts):
        super(RoundRobinSelector, self).__init__(opts)
        self.data = threading.local()

    def select(self, connections):
        self.data.rr = getattr(self.data, 'rr', -1) + 1
        self.data.rr %= len(connections)
        return connections[self.data.rr]

class ConnectionPool(object):
    """
    Container holding the :class:`~elasticsearch.Connection` instances,
    managing the selection process (via a
    :class:`~elasticsearch.ConnectionSelector`) and dead connections.

    It's only interactions are with the :class:`~elasticsearch.Transport` class
    that drives all the actions within `ConnectionPool`.

    Initially connections are stored on the class as a list and, along with the
    connection options, get passed to the `ConnectionSelector` instance for
    future reference.

    Upon each request the `Transport` will ask for a `Connection` via the
    `get_connection` method. If the connection fails (it's `perform_request`
    raises a `ConnectionError`) it will be marked as dead (via `mark_dead`) and
    put on a timeout (if it fails N times in a row the timeout is exponentially
    longer - the formula is `default_timeout * 2 ** (fail_count - 1)`). When
    the timeout is over the connection will be resurrected and returned to the
    live pool. A connection that has been previously marked as dead and
    succeeds will be marked as live (its fail count will be deleted).
    """
    def __init__(self, connections, dead_timeout=60, timeout_cutoff=5,
        selector_class=RoundRobinSelector, randomize_hosts=True, **kwargs):
        """
        :arg connections: list of tuples containing the
            :class:`~elasticsearch.Connection` instance and it's options
        :arg dead_timeout: number of seconds a connection should be retired for
            after a failure, increases on consecutive failures
        :arg timeout_cutoff: number of consecutive failures after which the
            timeout doesn't increase
        :arg selector_class: :class:`~elasticsearch.ConnectionSelector`
            subclass to use if more than one connection is live
        :arg randomize_hosts: shuffle the list of connections upon arrival to
            avoid dog piling effect across processes
        """
        if not connections:
            raise ImproperlyConfigured("No defined connections, you need to "
                    "specify at least one host.")
        self.connection_opts = connections
        self.connections = [c for (c, opts) in connections]
        # remember original connection list for resurrect(force=True)
        self.orig_connections = tuple(self.connections)
        # PriorityQueue for thread safety and ease of timeout management
        self.dead = PriorityQueue(len(self.connections))
        self.dead_count = {}

        if randomize_hosts:
            # randomize the connection list to avoid all clients hitting same node
            # after startup/restart
            random.shuffle(self.connections)

        # default timeout after which to try resurrecting a connection
        self.dead_timeout = dead_timeout
        self.timeout_cutoff = timeout_cutoff

        self.selector = selector_class(dict(connections))

    def mark_dead(self, connection, now=None):
        """
        Mark the connection as dead (failed). Remove it from the live pool and
        put it on a timeout.

        :arg connection: the failed instance
        """
        # allow inject for testing purposes
        now = now if now else time.time()
        try:
            self.connections.remove(connection)
        except ValueError:
            # connection not alive or another thread marked it already, ignore
            return
        else:
            dead_count = self.dead_count.get(connection, 0) + 1
            self.dead_count[connection] = dead_count
            timeout = self.dead_timeout * 2 ** min(dead_count - 1, self.timeout_cutoff)
            self.dead.put((now + timeout, connection))
            logger.warning(
                'Connection %r has failed for %i times in a row, putting on %i second timeout.',
                connection, dead_count, timeout
            )

    def mark_live(self, connection):
        """
        Mark connection as healthy after a resurrection. Resets the fail
        counter for the connection.

        :arg connection: the connection to redeem
        """
        try:
            del self.dead_count[connection]
        except KeyError:
            # race condition, safe to ignore
            pass

    def resurrect(self, force=False):
        """
        Attempt to resurrect a connection from the dead pool. It will try to
        locate one (not all) eligible (it's timeout is over) connection to
        return to the live pool. Any resurrected connection is also returned.

        :arg force: resurrect a connection even if there is none eligible (used
            when we have no live connections). If force is specified resurrect
            always returns a connection.

        """
        # no dead connections
        if self.dead.empty():
            # we are forced to return a connection, take one from the original
            # list. This is to avoid a race condition where get_connection can
            # see no live connections but when it calls resurrect self.dead is
            # also empty. We assume that other threat has resurrected all
            # available connections so we can safely return one at random.
            if force:
                return random.choice(self.orig_connections)
            return

        try:
            # retrieve a connection to check
            timeout, connection = self.dead.get(block=False)
        except Empty:
            # other thread has been faster and the queue is now empty. If we
            # are forced, return a connection at random again.
            if force:
                return random.choice(self.orig_connections)
            return

        if not force and timeout > time.time():
            # return it back if not eligible and not forced
            self.dead.put((timeout, connection))
            return

        # either we were forced or the connection is elligible to be retried
        self.connections.append(connection)
        logger.info('Resurrecting connection %r (force=%s).', connection, force)
        return connection

    def get_connection(self):
        """
        Return a connection from the pool using the `ConnectionSelector`
        instance.

        It tries to resurrect eligible connections, forces a resurrection when
        no connections are availible and passes the list of live connections to
        the selector instance to choose from.

        Returns a connection instance and it's current fail count.
        """
        self.resurrect()
        connections = self.connections[:]

        # no live nodes, resurrect one by force and return it
        if not connections:
            return self.resurrect(True)

        # only call selector if we have a selection
        if len(connections) > 1:
            return self.selector.select(connections)

        # only one connection, no need for a selector
        return connections[0]

    def close(self):
        """
        Explicitly closes connections
        """
        for conn in self.orig_connections:
            conn.close()

class DummyConnectionPool(ConnectionPool):
    def __init__(self, connections, **kwargs):
        if len(connections) != 1:
            raise ImproperlyConfigured("DummyConnectionPool needs exactly one "
                    "connection defined.")
        # we need connection opts for sniffing logic
        self.connection_opts = connections
        self.connection = connections[0][0]
        self.connections = (self.connection, )

    def get_connection(self):
        return self.connection

    def close(self):
        """
        Explicitly closes connections
        """
        self.connection.close()

    def _noop(self, *args, **kwargs):
        pass
    mark_dead = mark_live = resurrect = _noop


