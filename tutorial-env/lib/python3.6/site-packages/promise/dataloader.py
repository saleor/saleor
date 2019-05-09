from collections import Iterable, namedtuple
from functools import partial

from .promise import Promise, async_instance, get_default_scheduler

if False:
    from typing import (
        Any,
        List,
        Sized,
        Callable,
        Optional,
        Tuple,
        Union,
        Iterator,
        Hashable,
    )  # flake8: noqa


def get_chunks(iterable_obj, chunk_size=1):
    # type: (List[Loader], int) -> Iterator
    chunk_size = max(1, chunk_size)
    return (
        iterable_obj[i : i + chunk_size]
        for i in range(0, len(iterable_obj), chunk_size)
    )


Loader = namedtuple("Loader", "key,resolve,reject")


class DataLoader(object):

    batch = True
    max_batch_size = None  # type: int
    cache = True

    def __init__(
        self,
        batch_load_fn=None,  # type: Callable
        batch=None,  # type: Optional[Any]
        max_batch_size=None,  # type: Optional[int]
        cache=None,  # type: Optional[Any]
        get_cache_key=None,  # type: Optional[Any]
        cache_map=None,  # type: Optional[Any]
        scheduler=None,  # type: Optional[Any]
    ):
        # type: (...) -> None

        if batch_load_fn is not None:
            self.batch_load_fn = batch_load_fn

        if not callable(self.batch_load_fn):
            raise TypeError(
                (
                    "DataLoader must be have a batch_load_fn which accepts "
                    "List<key> and returns Promise<List<value>>, but got: {}."
                ).format(batch_load_fn)
            )

        if batch is not None:
            self.batch = batch

        if max_batch_size is not None:
            self.max_batch_size = max_batch_size

        if cache is not None:
            self.cache = cache

        if get_cache_key is not None:
            self.get_cache_key = get_cache_key

        self._promise_cache = cache_map or {}
        self._queue = []  # type: List[Loader]
        self._scheduler = scheduler

    def get_cache_key(self, key):  # type: ignore
        return key

    def load(self, key=None):
        # type: (Hashable) -> Promise
        """
        Loads a key, returning a `Promise` for the value represented by that key.
        """
        if key is None:
            raise TypeError(
                (
                    "The loader.load() function must be called with a value,"
                    + "but got: {}."
                ).format(key)
            )

        cache_key = self.get_cache_key(key)

        # If caching and there is a cache-hit, return cached Promise.
        if self.cache:
            cached_promise = self._promise_cache.get(cache_key)
            if cached_promise:
                return cached_promise

        # Otherwise, produce a new Promise for this value.

        promise = Promise(partial(self.do_resolve_reject, key))  # type: ignore

        # If caching, cache this promise.
        if self.cache:
            self._promise_cache[cache_key] = promise

        return promise

    def do_resolve_reject(self, key, resolve, reject):
        # type: (Hashable, Callable, Callable) -> None
        # Enqueue this Promise to be dispatched.
        self._queue.append(Loader(key=key, resolve=resolve, reject=reject))
        # Determine if a dispatch of this queue should be scheduled.
        # A single dispatch should be scheduled per queue at the time when the
        # queue changes from "empty" to "full".
        if len(self._queue) == 1:
            if self.batch:
                # If batching, schedule a task to dispatch the queue.
                enqueue_post_promise_job(partial(dispatch_queue, self), self._scheduler)
            else:
                # Otherwise dispatch the (queue of one) immediately.
                dispatch_queue(self)

    def load_many(self, keys):
        # type: (Iterable[Hashable]) -> Promise
        """
        Loads multiple keys, promising an array of values

        >>> a, b = await my_loader.load_many([ 'a', 'b' ])

        This is equivalent to the more verbose:

        >>> a, b = await Promise.all([
        >>>    my_loader.load('a'),
        >>>    my_loader.load('b')
        >>> ])
        """
        if not isinstance(keys, Iterable):
            raise TypeError(
                (
                    "The loader.loadMany() function must be called with Array<key> "
                    + "but got: {}."
                ).format(keys)
            )

        return Promise.all([self.load(key) for key in keys])

    def clear(self, key):
        # type: (Hashable) -> DataLoader
        """
        Clears the value at `key` from the cache, if it exists. Returns itself for
        method chaining.
        """
        cache_key = self.get_cache_key(key)
        self._promise_cache.pop(cache_key, None)
        return self

    def clear_all(self):
        # type: () -> DataLoader
        """
        Clears the entire cache. To be used when some event results in unknown
        invalidations across this particular `DataLoader`. Returns itself for
        method chaining.
        """
        self._promise_cache = {}
        return self

    def prime(self, key, value):
        # type: (Hashable, Any) -> DataLoader
        """
        Adds the provied key and value to the cache. If the key already exists, no
        change is made. Returns itself for method chaining.
        """
        cache_key = self.get_cache_key(key)

        # Only add the key if it does not already exist.
        if cache_key not in self._promise_cache:
            # Cache a rejected promise if the value is an Error, in order to match
            # the behavior of load(key).
            if isinstance(value, Exception):
                promise = Promise.reject(value)
            else:
                promise = Promise.resolve(value)

            self._promise_cache[cache_key] = promise

        return self


# Private: Enqueue a Job to be executed after all "PromiseJobs" Jobs.
#
# ES6 JavaScript uses the concepts Job and JobQueue to schedule work to occur
# after the current execution context has completed:
# http://www.ecma-international.org/ecma-262/6.0/#sec-jobs-and-job-queues
#
# Node.js uses the `process.nextTick` mechanism to implement the concept of a
# Job, maintaining a global FIFO JobQueue for all Jobs, which is flushed after
# the current call stack ends.
#
# When calling `then` on a Promise, it enqueues a Job on a specific
# "PromiseJobs" JobQueue which is flushed in Node as a single Job on the
# global JobQueue.
#
# DataLoader batches all loads which occur in a single frame of execution, but
# should include in the batch all loads which occur during the flushing of the
# "PromiseJobs" JobQueue after that same execution frame.
#
# In order to avoid the DataLoader dispatch Job occuring before "PromiseJobs",
# A Promise Job is created with the sole purpose of enqueuing a global Job,
# ensuring that it always occurs after "PromiseJobs" ends.

# Private: cached resolved Promise instance
resolved_promise = None  # type: Optional[Promise[None]]


def enqueue_post_promise_job(fn, scheduler):
    # type: (Callable, Any) -> None
    global resolved_promise
    if not resolved_promise:
        resolved_promise = Promise.resolve(None)
    if not scheduler:
        scheduler = get_default_scheduler()

    def on_promise_resolve(v):
        # type: (Any) -> None
        async_instance.invoke(fn, scheduler)

    resolved_promise.then(on_promise_resolve)  # type: Promise[None]


def dispatch_queue(loader):
    # type: (DataLoader) -> None
    """
    Given the current state of a Loader instance, perform a batch load
    from its current queue.
    """
    # Take the current loader queue, replacing it with an empty queue.
    queue = loader._queue
    loader._queue = []

    # If a maxBatchSize was provided and the queue is longer, then segment the
    # queue into multiple batches, otherwise treat the queue as a single batch.
    max_batch_size = loader.max_batch_size

    if max_batch_size and max_batch_size < len(queue):
        chunks = get_chunks(queue, max_batch_size)
        for chunk in chunks:
            dispatch_queue_batch(loader, chunk)
    else:
        dispatch_queue_batch(loader, queue)


def dispatch_queue_batch(loader, queue):
    # type: (DataLoader, List[Loader]) -> None
    # Collect all keys to be loaded in this dispatch
    keys = [l.key for l in queue]

    # Call the provided batch_load_fn for this loader with the loader queue's keys.
    try:
        batch_promise = loader.batch_load_fn(keys)
    except Exception as e:
        failed_dispatch(loader, queue, e)
        return None

    # Assert the expected response from batch_load_fn
    if not batch_promise or not isinstance(batch_promise, Promise):
        failed_dispatch(
            loader,
            queue,
            TypeError(
                (
                    "DataLoader must be constructed with a function which accepts "
                    "Array<key> and returns Promise<Array<value>>, but the function did "
                    "not return a Promise: {}."
                ).format(batch_promise)
            ),
        )
        return None

    def batch_promise_resolved(values):
        # type: (Sized) -> None
        # Assert the expected resolution from batchLoadFn.
        if not isinstance(values, Iterable):
            raise TypeError(
                (
                    "DataLoader must be constructed with a function which accepts "
                    "Array<key> and returns Promise<Array<value>>, but the function did "
                    "not return a Promise of an Array: {}."
                ).format(values)
            )

        if len(values) != len(keys):
            raise TypeError(
                (
                    "DataLoader must be constructed with a function which accepts "
                    "Array<key> and returns Promise<Array<value>>, but the function did "
                    "not return a Promise of an Array of the same length as the Array "
                    "of keys."
                    "\n\nKeys:\n{}"
                    "\n\nValues:\n{}"
                ).format(keys, values)
            )

        # Step through the values, resolving or rejecting each Promise in the
        # loaded queue.
        for l, value in zip(queue, values):
            if isinstance(value, Exception):
                l.reject(value)
            else:
                l.resolve(value)

    batch_promise.then(batch_promise_resolved).catch(
        partial(failed_dispatch, loader, queue)
    )


def failed_dispatch(loader, queue, error):
    # type: (DataLoader, Iterable[Loader], Exception) -> None
    """
    Do not cache individual loads if the entire batch dispatch fails,
    but still reject each request so they do not hang.
    """
    for l in queue:
        loader.clear(l.key)
        l.reject(error)
