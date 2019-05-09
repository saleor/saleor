"""
LRU cache implementation for Python 2.7

Ported from http://code.activestate.com/recipes/578078/ and simplified for our
use (only support maxsize > 0 and positional arguments).
"""

from collections import namedtuple
from functools import update_wrapper
from threading import RLock

_CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])


def lru_cache(maxsize=100):
    """Least-recently-used cache decorator.

    Arguments to the cached function must be hashable.

    See:  http://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

    """
    def decorating_function(user_function):

        cache = dict()
        stats = [0, 0]                  # make statistics updateable non-locally
        HITS, MISSES = 0, 1             # names for the stats fields
        cache_get = cache.get           # bound method to lookup key or return None
        _len = len                      # localize the global len() function
        lock = RLock()                  # linkedlist updates aren't threadsafe
        root = []                       # root of the circular doubly linked list
        root[:] = [root, root, None, None]      # initialize by pointing to self
        nonlocal_root = [root]                  # make updateable non-locally
        PREV, NEXT, KEY, RESULT = 0, 1, 2, 3    # names for the link fields

        assert maxsize and maxsize > 0, "maxsize %s not supported" % maxsize

        def wrapper(*args):
            # size limited caching that tracks accesses by recency
            key = args
            with lock:
                link = cache_get(key)
                if link is not None:
                    # record recent use of the key by moving it to the
                    # front of the list
                    root, = nonlocal_root
                    link_prev, link_next, key, result = link
                    link_prev[NEXT] = link_next
                    link_next[PREV] = link_prev
                    last = root[PREV]
                    last[NEXT] = root[PREV] = link
                    link[PREV] = last
                    link[NEXT] = root
                    stats[HITS] += 1
                    return result
            result = user_function(*args)
            with lock:
                root, = nonlocal_root
                if key in cache:
                    # getting here means that this same key was added to the
                    # cache while the lock was released.  since the link
                    # update is already done, we need only return the
                    # computed result and update the count of misses.
                    pass
                elif _len(cache) >= maxsize:
                    # use the old root to store the new key and result
                    oldroot = root
                    oldroot[KEY] = key
                    oldroot[RESULT] = result
                    # empty the oldest link and make it the new root
                    root = nonlocal_root[0] = oldroot[NEXT]
                    oldkey = root[KEY]
                    # oldvalue = root[RESULT]
                    root[KEY] = root[RESULT] = None
                    # now update the cache dictionary for the new links
                    del cache[oldkey]
                    cache[key] = oldroot
                else:
                    # put result in a new link at the front of the list
                    last = root[PREV]
                    link = [last, root, key, result]
                    last[NEXT] = root[PREV] = cache[key] = link
                stats[MISSES] += 1
            return result

        def cache_info():
            """Report cache statistics"""
            with lock:
                return _CacheInfo(stats[HITS], stats[MISSES], maxsize, len(cache))

        def cache_clear():
            """Clear the cache and cache statistics"""
            with lock:
                cache.clear()
                root = nonlocal_root[0]
                root[:] = [root, root, None, None]
                stats[:] = [0, 0]

        wrapper.__wrapped__ = user_function
        wrapper.cache_info = cache_info
        wrapper.cache_clear = cache_clear
        return update_wrapper(wrapper, user_function)

    return decorating_function
