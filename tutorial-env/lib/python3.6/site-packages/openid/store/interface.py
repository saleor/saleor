"""
This module contains the definition of the C{L{OpenIDStore}}
interface.
"""


class OpenIDStore(object):
    """
    This is the interface for the store objects the OpenID library
    uses.  It is a single class that provides all of the persistence
    mechanisms that the OpenID library needs, for both servers and
    consumers.

    @change: Version 2.0 removed the C{storeNonce}, C{getAuthKey}, and C{isDumb}
        methods, and changed the behavior of the C{L{useNonce}} method
        to support one-way nonces.  It added C{L{cleanupNonces}},
        C{L{cleanupAssociations}}, and C{L{cleanup}}.

    @sort: storeAssociation, getAssociation, removeAssociation,
        useNonce
    """

    def storeAssociation(self, server_url, association):
        """
        This method puts a C{L{Association
        <openid.association.Association>}} object into storage,
        retrievable by server URL and handle.


        @param server_url: The URL of the identity server that this
            association is with.  Because of the way the server
            portion of the library uses this interface, don't assume
            there are any limitations on the character set of the
            input string.  In particular, expect to see unescaped
            non-url-safe characters in the server_url field.

        @type server_url: C{str}


        @param association: The C{L{Association
            <openid.association.Association>}} to store.

        @type association: C{L{Association
            <openid.association.Association>}}


        @return: C{None}

        @rtype: C{NoneType}
        """
        raise NotImplementedError

    def getAssociation(self, server_url, handle=None):
        """
        This method returns an C{L{Association
        <openid.association.Association>}} object from storage that
        matches the server URL and, if specified, handle. It returns
        C{None} if no such association is found or if the matching
        association is expired.

        If no handle is specified, the store may return any
        association which matches the server URL.  If multiple
        associations are valid, the recommended return value for this
        method is the one most recently issued.

        This method is allowed (and encouraged) to garbage collect
        expired associations when found. This method must not return
        expired associations.


        @param server_url: The URL of the identity server to get the
            association for.  Because of the way the server portion of
            the library uses this interface, don't assume there are
            any limitations on the character set of the input string.
            In particular, expect to see unescaped non-url-safe
            characters in the server_url field.

        @type server_url: C{str}


        @param handle: This optional parameter is the handle of the
            specific association to get.  If no specific handle is
            provided, any valid association matching the server URL is
            returned.

        @type handle: C{str} or C{NoneType}


        @return: The C{L{Association
            <openid.association.Association>}} for the given identity
            server.

        @rtype: C{L{Association <openid.association.Association>}} or
            C{NoneType}
        """
        raise NotImplementedError

    def removeAssociation(self, server_url, handle):
        """
        This method removes the matching association if it's found,
        and returns whether the association was removed or not.


        @param server_url: The URL of the identity server the
            association to remove belongs to.  Because of the way the
            server portion of the library uses this interface, don't
            assume there are any limitations on the character set of
            the input string.  In particular, expect to see unescaped
            non-url-safe characters in the server_url field.

        @type server_url: C{str}


        @param handle: This is the handle of the association to
            remove.  If there isn't an association found that matches
            both the given URL and handle, then there was no matching
            handle found.

        @type handle: C{str}


        @return: Returns whether or not the given association existed.

        @rtype: C{bool} or C{int}
        """
        raise NotImplementedError

    def useNonce(self, server_url, timestamp, salt):
        """Called when using a nonce.

        This method should return C{True} if the nonce has not been
        used before, and store it for a while to make sure nobody
        tries to use the same value again.  If the nonce has already
        been used or the timestamp is not current, return C{False}.

        You may use L{openid.store.nonce.SKEW} for your timestamp window.

        @change: In earlier versions, round-trip nonces were used and
           a nonce was only valid if it had been previously stored
           with C{storeNonce}.  Version 2.0 uses one-way nonces,
           requiring a different implementation here that does not
           depend on a C{storeNonce} call.  (C{storeNonce} is no
           longer part of the interface.)

        @param server_url: The URL of the server from which the nonce
            originated.

        @type server_url: C{str}

        @param timestamp: The time that the nonce was created (to the
            nearest second), in seconds since January 1 1970 UTC.
        @type timestamp: C{int}

        @param salt: A random string that makes two nonces from the
            same server issued during the same second unique.
        @type salt: str

        @return: Whether or not the nonce was valid.

        @rtype: C{bool}
        """
        raise NotImplementedError

    def cleanupNonces(self):
        """Remove expired nonces from the store.

        Discards any nonce from storage that is old enough that its
        timestamp would not pass L{useNonce}.

        This method is not called in the normal operation of the
        library.  It provides a way for store admins to keep
        their storage from filling up with expired data.

        @return: the number of nonces expired.
        @returntype: int
        """
        raise NotImplementedError

    def cleanupAssociations(self):
        """Remove expired associations from the store.

        This method is not called in the normal operation of the
        library.  It provides a way for store admins to keep
        their storage from filling up with expired data.

        @return: the number of associations expired.
        @returntype: int
        """
        raise NotImplementedError

    def cleanup(self):
        """Shortcut for C{L{cleanupNonces}()}, C{L{cleanupAssociations}()}.

        This method is not called in the normal operation of the
        library.  It provides a way for store admins to keep
        their storage from filling up with expired data.
        """
        return self.cleanupNonces(), self.cleanupAssociations()
