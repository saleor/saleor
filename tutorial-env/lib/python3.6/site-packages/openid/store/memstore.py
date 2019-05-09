"""A simple store using only in-process memory."""

from openid.store import nonce

import copy
import time


class ServerAssocs(object):
    def __init__(self):
        self.assocs = {}

    def set(self, assoc):
        self.assocs[assoc.handle] = assoc

    def get(self, handle):
        return self.assocs.get(handle)

    def remove(self, handle):
        try:
            del self.assocs[handle]
        except KeyError:
            return False
        else:
            return True

    def best(self):
        """Returns association with the oldest issued date.

        or None if there are no associations.
        """
        best = None
        for assoc in list(self.assocs.values()):
            if best is None or best.issued < assoc.issued:
                best = assoc
        return best

    def cleanup(self):
        """Remove expired associations.

        @return: tuple of (removed associations, remaining associations)
        """
        remove = []
        for handle, assoc in self.assocs.items():
            if assoc.expiresIn == 0:
                remove.append(handle)
        for handle in remove:
            del self.assocs[handle]
        return len(remove), len(self.assocs)


class MemoryStore(object):
    """In-process memory store.

    Use for single long-running processes.  No persistence supplied.
    """

    def __init__(self):
        self.server_assocs = {}
        self.nonces = {}

    def _getServerAssocs(self, server_url):
        try:
            return self.server_assocs[server_url]
        except KeyError:
            assocs = self.server_assocs[server_url] = ServerAssocs()
            return assocs

    def storeAssociation(self, server_url, assoc):
        assocs = self._getServerAssocs(server_url)
        assocs.set(copy.deepcopy(assoc))

    def getAssociation(self, server_url, handle=None):
        assocs = self._getServerAssocs(server_url)
        if handle is None:
            return assocs.best()
        else:
            return assocs.get(handle)

    def removeAssociation(self, server_url, handle):
        assocs = self._getServerAssocs(server_url)
        return assocs.remove(handle)

    def useNonce(self, server_url, timestamp, salt):
        if abs(timestamp - time.time()) > nonce.SKEW:
            return False

        anonce = (str(server_url), int(timestamp), str(salt))
        if anonce in self.nonces:
            return False
        else:
            self.nonces[anonce] = None
            return True

    def cleanupNonces(self):
        now = time.time()
        expired = []
        for anonce in self.nonces.keys():
            if abs(anonce[1] - now) > nonce.SKEW:
                # removing items while iterating over the set could be bad.
                expired.append(anonce)

        for anonce in expired:
            del self.nonces[anonce]
        return len(expired)

    def cleanupAssociations(self):
        remove_urls = []
        removed_assocs = 0
        for server_url, assocs in self.server_assocs.items():
            removed, remaining = assocs.cleanup()
            removed_assocs += removed
            if not remaining:
                remove_urls.append(server_url)

        # Remove entries from server_assocs that had none remaining.
        for server_url in remove_urls:
            del self.server_assocs[server_url]
        return removed_assocs

    def __eq__(self, other):
        return ((self.server_assocs == other.server_assocs) and
                (self.nonces == other.nonces))

    def __ne__(self, other):
        return not (self == other)
