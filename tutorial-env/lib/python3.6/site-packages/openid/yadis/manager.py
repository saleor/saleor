class YadisServiceManager(object):
    """Holds the state of a list of selected Yadis services, managing
    storing it in a session and iterating over the services in order."""

    def __init__(self, starting_url, yadis_url, services, session_key):
        # The URL that was used to initiate the Yadis protocol
        self.starting_url = starting_url

        # The URL after following redirects (the identifier)
        self.yadis_url = yadis_url

        # List of service elements
        self.services = list(services)

        self.session_key = session_key

        # Reference to the current service object
        self._current = None

    def __len__(self):
        """How many untried services remain?"""
        return len(self.services)

    def __iter__(self):
        return self

    def __next__(self):
        """Return the next service

        self.current() will continue to return that service until the
        next call to this method."""
        try:
            self._current = self.services.pop(0)
        except IndexError:
            raise StopIteration
        else:
            return self._current

    def current(self):
        """Return the current service.

        Returns None if there are no services left.
        """
        return self._current

    def forURL(self, url):
        return url in [self.starting_url, self.yadis_url]

    def started(self):
        """Has the first service been returned?"""
        return self._current is not None

    def store(self, session):
        """Store this object in the session, by its session key."""
        session[self.session_key] = self


class Discovery(object):
    """State management for discovery.

    High-level usage pattern is to call .getNextService(discover) in
    order to find the next available service for this user for this
    session. Once a request completes, call .finish() to clean up the
    session state.

    @ivar session: a dict-like object that stores state unique to the
        requesting user-agent. This object must be able to store
        serializable objects.

    @ivar url: the URL that is used to make the discovery request

    @ivar session_key_suffix: The suffix that will be used to identify
        this object in the session object.
    """

    DEFAULT_SUFFIX = 'auth'
    PREFIX = '_yadis_services_'

    def __init__(self, session, url, session_key_suffix=None):
        """Initialize a discovery object"""
        self.session = session
        self.url = url
        if session_key_suffix is None:
            session_key_suffix = self.DEFAULT_SUFFIX

        self.session_key_suffix = session_key_suffix

    def getNextService(self, discover):
        """Return the next authentication service for the pair of
        user_input and session.  This function handles fallback.


        @param discover: a callable that takes a URL and returns a
            list of services

        @type discover: str -> [service]


        @return: the next available service
        """
        manager = self.getManager()
        if manager is not None and not manager:
            self.destroyManager()

        if not manager:
            yadis_url, services = discover(self.url)
            manager = self.createManager(services, yadis_url)

        if manager:
            service = next(manager)
            manager.store(self.session)
        else:
            service = None

        return service

    def cleanup(self, force=False):
        """Clean up Yadis-related services in the session and return
        the most-recently-attempted service from the manager, if one
        exists.

        @param force: True if the manager should be deleted regardless
        of whether it's a manager for self.url.

        @return: current service endpoint object or None if there is
            no current service
        """
        manager = self.getManager(force=force)
        if manager is not None:
            service = manager.current()
            self.destroyManager(force=force)
        else:
            service = None

        return service

    ### Lower-level methods

    def getSessionKey(self):
        """Get the session key for this starting URL and suffix

        @return: The session key
        @rtype: str
        """
        return self.PREFIX + self.session_key_suffix

    def getManager(self, force=False):
        """Extract the YadisServiceManager for this object's URL and
        suffix from the session.

        @param force: True if the manager should be returned
        regardless of whether it's a manager for self.url.

        @return: The current YadisServiceManager, if it's for this
            URL, or else None
        """
        manager = self.session.get(self.getSessionKey())
        if (manager is not None and (manager.forURL(self.url) or force)):
            return manager
        else:
            return None

    def createManager(self, services, yadis_url=None):
        """Create a new YadisService Manager for this starting URL and
        suffix, and store it in the session.

        @raises KeyError: When I already have a manager.

        @return: A new YadisServiceManager or None
        """
        key = self.getSessionKey()
        if self.getManager():
            raise KeyError('There is already a %r manager for %r' %
                           (key, self.url))

        if not services:
            return None

        manager = YadisServiceManager(self.url, yadis_url, services, key)
        manager.store(self.session)
        return manager

    def destroyManager(self, force=False):
        """Delete any YadisServiceManager with this starting URL and
        suffix from the session.

        If there is no service manager or the service manager is for a
        different URL, it silently does nothing.

        @param force: True if the manager should be deleted regardless
        of whether it's a manager for self.url.
        """
        if self.getManager(force=force) is not None:
            key = self.getSessionKey()
            del self.session[key]
