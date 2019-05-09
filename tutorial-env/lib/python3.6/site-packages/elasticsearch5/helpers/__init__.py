from __future__ import unicode_literals

import logging
from operator import methodcaller
import time

from ..exceptions import ElasticsearchException, TransportError
from ..compat import map, string_types, Queue


logger = logging.getLogger('elasticsearch.helpers')

class BulkIndexError(ElasticsearchException):
    @property
    def errors(self):
        """ List of errors from execution of the last chunk. """
        return self.args[1]


class ScanError(ElasticsearchException):
    def __init__(self, scroll_id, *args, **kwargs):
        super(ScanError, self).__init__(*args, **kwargs)
        self.scroll_id = scroll_id

def expand_action(data):
    """
    From one document or action definition passed in by the user extract the
    action/data lines needed for elasticsearch's
    :meth:`~elasticsearch.Elasticsearch.bulk` api.
    """
    # when given a string, assume user wants to index raw json
    if isinstance(data, string_types):
        return '{"index":{}}', data

    # make sure we don't alter the action
    data = data.copy()
    op_type = data.pop('_op_type', 'index')
    action = {op_type: {}}
    for key in ('_index', '_parent', '_percolate', '_routing', '_timestamp',
                '_type', '_version', '_version_type', '_id',
                '_retry_on_conflict', 'pipeline'):
        if key in data:
            action[op_type][key] = data.pop(key)

    # no data payload for delete
    if op_type == 'delete':
        return action, None

    return action, data.get('_source', data)

def _chunk_actions(actions, chunk_size, max_chunk_bytes, serializer):
    """
    Split actions into chunks by number or size, serialize them into strings in
    the process.
    """
    bulk_actions, bulk_data = [], []
    size, action_count = 0, 0
    for action, data in actions:
        raw_data, raw_action = data, action
        action = serializer.dumps(action)
        cur_size = len(action) + 1

        if data is not None:
            data = serializer.dumps(data)
            cur_size += len(data) + 1

        # full chunk, send it and start a new one
        if bulk_actions and (size + cur_size > max_chunk_bytes or action_count == chunk_size):
            yield bulk_data, bulk_actions
            bulk_actions, bulk_data = [], []
            size, action_count = 0, 0

        bulk_actions.append(action)
        if data is not None:
            bulk_actions.append(data)
            bulk_data.append((raw_action, raw_data))
        else:
            bulk_data.append((raw_action, ))

        size += cur_size
        action_count += 1

    if bulk_actions:
        yield bulk_data, bulk_actions

def _process_bulk_chunk(client, bulk_actions, bulk_data, raise_on_exception=True, raise_on_error=True, **kwargs):
    """
    Send a bulk request to elasticsearch and process the output.
    """
    # if raise on error is set, we need to collect errors per chunk before raising them
    errors = []

    try:
        # send the actual request
        resp = client.bulk('\n'.join(bulk_actions) + '\n', **kwargs)
    except TransportError as e:
        # default behavior - just propagate exception
        if raise_on_exception:
            raise e

        # if we are not propagating, mark all actions in current chunk as failed
        err_message = str(e)
        exc_errors = []

        for data in bulk_data:
            # collect all the information about failed actions
            op_type, action = data[0].copy().popitem()
            info = {"error": err_message, "status": e.status_code, "exception": e}
            if op_type != 'delete':
                info['data'] = data[1]
            info.update(action)
            exc_errors.append({op_type: info})

        # emulate standard behavior for failed actions
        if raise_on_error:
            raise BulkIndexError('%i document(s) failed to index.' % len(exc_errors), exc_errors)
        else:
            for err in exc_errors:
                yield False, err
            return

    # go through request-reponse pairs and detect failures
    for data, (op_type, item) in zip(bulk_data, map(methodcaller('popitem'), resp['items'])):
        ok = 200 <= item.get('status', 500) < 300
        if not ok and raise_on_error:
            # include original document source
            if len(data) > 1:
                item['data'] = data[1]
            errors.append({op_type: item})

        if ok or not errors:
            # if we are not just recording all errors to be able to raise
            # them all at once, yield items individually
            yield ok, {op_type: item}

    if errors:
        raise BulkIndexError('%i document(s) failed to index.' % len(errors), errors)

def streaming_bulk(client, actions, chunk_size=500, max_chunk_bytes=100 * 1024 * 1024,
                   raise_on_error=True, expand_action_callback=expand_action,
                   raise_on_exception=True, max_retries=0, initial_backoff=2,
                   max_backoff=600, yield_ok=True, **kwargs):

    """
    Streaming bulk consumes actions from the iterable passed in and yields
    results per action. For non-streaming usecases use
    :func:`~elasticsearch.helpers.bulk` which is a wrapper around streaming
    bulk that returns summary information about the bulk operation once the
    entire input is consumed and sent.

    If you specify ``max_retries`` it will also retry any documents that were
    rejected with a ``429`` status code. To do this it will wait (**by calling
    time.sleep which will block**) for ``initial_backoff`` seconds and then,
    every subsequent rejection for the same chunk, for double the time every
    time up to ``max_backoff`` seconds.

    :arg client: instance of :class:`~elasticsearch.Elasticsearch` to use
    :arg actions: iterable containing the actions to be executed
    :arg chunk_size: number of docs in one chunk sent to es (default: 500)
    :arg max_chunk_bytes: the maximum size of the request in bytes (default: 100MB)
    :arg raise_on_error: raise ``BulkIndexError`` containing errors (as `.errors`)
        from the execution of the last chunk when some occur. By default we raise.
    :arg raise_on_exception: if ``False`` then don't propagate exceptions from
        call to ``bulk`` and just report the items that failed as failed.
    :arg expand_action_callback: callback executed on each action passed in,
        should return a tuple containing the action line and the data line
        (`None` if data line should be omitted).
    :arg max_retries: maximum number of times a document will be retried when
        ``429`` is received, set to 0 (default) for no retires on ``429``
    :arg initial_backoff: number of seconds we should wait before the first
        retry. Any subsequent retries will be powers of ``inittial_backoff *
        2**retry_number``
    :arg max_backoff: maximum number of seconds a retry will wait
    :arg yield_ok: if set to False will skip successful documents in the output
    """
    actions = map(expand_action_callback, actions)

    for bulk_data, bulk_actions in _chunk_actions(actions, chunk_size,
                                                  max_chunk_bytes,
                                                  client.transport.serializer):

        for attempt in range(max_retries + 1):
            to_retry, to_retry_data = [], []
            if attempt:
                time.sleep(min(max_backoff, initial_backoff * 2**(attempt-1)))

            try:
                for data, (ok, info) in zip(
                            bulk_data,
                            _process_bulk_chunk(client, bulk_actions, bulk_data,
                                                raise_on_exception,
                                                raise_on_error, **kwargs)
                        ):

                    if not ok:
                        action, info = info.popitem()
                        # retry if retries enabled, we get 429, and we are not
                        # in the last attempt
                        if max_retries \
                                and info['status'] == 429 \
                                and (attempt+1) <= max_retries:
                            # _process_bulk_chunk expects strings so we need to
                            # re-serialize the data
                            to_retry.extend(map(client.transport.serializer.dumps, data))
                            to_retry_data.append(data)
                        else:
                            yield ok, {action: info}
                    elif yield_ok:
                        yield ok, info

            except TransportError as e:
                # suppress 429 errors since we will retry them
                if not max_retries or e.status_code != 429:
                    raise
            else:
                if not to_retry:
                    break
                # retry only subset of documents that didn't succeed
                bulk_actions, bulk_data = to_retry, to_retry_data


def bulk(client, actions, stats_only=False, **kwargs):
    """
    Helper for the :meth:`~elasticsearch.Elasticsearch.bulk` api that provides
    a more human friendly interface - it consumes an iterator of actions and
    sends them to elasticsearch in chunks. It returns a tuple with summary
    information - number of successfully executed actions and either list of
    errors or number of errors if ``stats_only`` is set to ``True``. Note that
    by default we raise a ``BulkIndexError`` when we encounter an error so
    options like ``stats_only`` only apply when ``raise_on_error`` is set to
    ``False``.

    When errors are being collected original document data is included in the
    error dictionary which can lead to an extra high memory usage. If you need
    to process a lot of data and want to ignore/collect errors please consider
    using the :func:`~elasticsearch.helpers.streaming_bulk` helper which will
    just return the errors and not store them in memory.


    :arg client: instance of :class:`~elasticsearch.Elasticsearch` to use
    :arg actions: iterator containing the actions
    :arg stats_only: if `True` only report number of successful/failed
        operations instead of just number of successful and a list of error responses

    Any additional keyword arguments will be passed to
    :func:`~elasticsearch.helpers.streaming_bulk` which is used to execute
    the operation, see :func:`~elasticsearch.helpers.streaming_bulk` for more
    accepted parameters.
    """
    success, failed = 0, 0

    # list of errors to be collected is not stats_only
    errors = []

    # make streaming_bulk yield successful results so we can count them
    kwargs['yield_ok'] = True
    for ok, item in streaming_bulk(client, actions, **kwargs):
        # go through request-reponse pairs and detect failures
        if not ok:
            if not stats_only:
                errors.append(item)
            failed += 1
        else:
            success += 1

    return success, failed if stats_only else errors

def parallel_bulk(client, actions, thread_count=4, chunk_size=500,
        max_chunk_bytes=100 * 1024 * 1024, queue_size=4,
        expand_action_callback=expand_action, **kwargs):
    """
    Parallel version of the bulk helper run in multiple threads at once.

    :arg client: instance of :class:`~elasticsearch.Elasticsearch` to use
    :arg actions: iterator containing the actions
    :arg thread_count: size of the threadpool to use for the bulk requests
    :arg chunk_size: number of docs in one chunk sent to es (default: 500)
    :arg max_chunk_bytes: the maximum size of the request in bytes (default: 100MB)
    :arg raise_on_error: raise ``BulkIndexError`` containing errors (as `.errors`)
        from the execution of the last chunk when some occur. By default we raise.
    :arg raise_on_exception: if ``False`` then don't propagate exceptions from
        call to ``bulk`` and just report the items that failed as failed.
    :arg expand_action_callback: callback executed on each action passed in,
        should return a tuple containing the action line and the data line
        (`None` if data line should be omitted).
    :arg queue_size: size of the task queue between the main thread (producing
        chunks to send) and the processing threads.
    """
    # Avoid importing multiprocessing unless parallel_bulk is used
    # to avoid exceptions on restricted environments like App Engine
    from multiprocessing.pool import ThreadPool

    actions = map(expand_action_callback, actions)

    class BlockingPool(ThreadPool):
        def _setup_queues(self):
            super(BlockingPool, self)._setup_queues()
            self._inqueue = Queue(queue_size)
            self._quick_put = self._inqueue.put

    pool = BlockingPool(thread_count)

    try:
        for result in pool.imap(
            lambda bulk_chunk: list(_process_bulk_chunk(client, bulk_chunk[1], bulk_chunk[0], **kwargs)),
            _chunk_actions(actions, chunk_size, max_chunk_bytes, client.transport.serializer)
            ):
            for item in result:
                yield item

    finally:
        pool.close()
        pool.join()

def scan(client, query=None, scroll='5m', raise_on_error=True,
         preserve_order=False, size=1000, request_timeout=None, clear_scroll=True,
         scroll_kwargs=None, **kwargs):
    """
    Simple abstraction on top of the
    :meth:`~elasticsearch.Elasticsearch.scroll` api - a simple iterator that
    yields all hits as returned by underlining scroll requests.

    By default scan does not return results in any pre-determined order. To
    have a standard order in the returned documents (either by score or
    explicit sort definition) when scrolling, use ``preserve_order=True``. This
    may be an expensive operation and will negate the performance benefits of
    using ``scan``.

    :arg client: instance of :class:`~elasticsearch.Elasticsearch` to use
    :arg query: body for the :meth:`~elasticsearch.Elasticsearch.search` api
    :arg scroll: Specify how long a consistent view of the index should be
        maintained for scrolled search
    :arg raise_on_error: raises an exception (``ScanError``) if an error is
        encountered (some shards fail to execute). By default we raise.
    :arg preserve_order: don't set the ``search_type`` to ``scan`` - this will
        cause the scroll to paginate with preserving the order. Note that this
        can be an extremely expensive operation and can easily lead to
        unpredictable results, use with caution.
    :arg size: size (per shard) of the batch send at each iteration.
    :arg request_timeout: explicit timeout for each call to ``scan``
    :arg clear_scroll: explicitly calls delete on the scroll id via the clear
        scroll API at the end of the method on completion or error, defaults
        to true.
    :arg scroll_kwargs: additional kwargs to be passed to
        :meth:`~elasticsearch.Elasticsearch.scroll`

    Any additional keyword arguments will be passed to the initial
    :meth:`~elasticsearch.Elasticsearch.search` call::

        scan(es,
            query={"query": {"match": {"title": "python"}}},
            index="orders-*",
            doc_type="books"
        )

    """
    scroll_kwargs = scroll_kwargs or {}

    if not preserve_order:
        query = query.copy() if query else {}
        query["sort"] = "_doc"
    # initial search
    resp = client.search(body=query, scroll=scroll, size=size,
                         request_timeout=request_timeout, **kwargs)

    scroll_id = resp.get('_scroll_id')
    if scroll_id is None:
        return

    try:
        first_run = True
        while True:
            # if we didn't set search_type to scan initial search contains data
            if first_run:
                first_run = False
            else:
                resp = client.scroll(scroll_id, scroll=scroll,
                                     request_timeout=request_timeout,
                                     **scroll_kwargs)

            for hit in resp['hits']['hits']:
                yield hit

            # check if we have any errrors
            if resp["_shards"]["successful"] < resp["_shards"]["total"]:
                logger.warning(
                    'Scroll request has only succeeded on %d shards out of %d.',
                    resp['_shards']['successful'], resp['_shards']['total']
                )
                if raise_on_error:
                    raise ScanError(
                        scroll_id,
                        'Scroll request has only succeeded on %d shards out of %d.' %
                            (resp['_shards']['successful'], resp['_shards']['total'])
                    )

            scroll_id = resp.get('_scroll_id')
            # end of scroll
            if scroll_id is None or not resp['hits']['hits']:
                break
    finally:
        if scroll_id and clear_scroll:
            client.clear_scroll(body={'scroll_id': [scroll_id]}, ignore=(404, ))

def reindex(client, source_index, target_index, query=None, target_client=None,
        chunk_size=500, scroll='5m', scan_kwargs={}, bulk_kwargs={}):

    """
    Reindex all documents from one index that satisfy a given query
    to another, potentially (if `target_client` is specified) on a different cluster.
    If you don't specify the query you will reindex all the documents.

    Since ``2.3`` a :meth:`~elasticsearch.Elasticsearch.reindex` api is
    available as part of elasticsearch itself. It is recommended to use the api
    instead of this helper wherever possible. The helper is here mostly for
    backwards compatibility and for situations where more flexibility is
    needed.

    .. note::

        This helper doesn't transfer mappings, just the data.

    :arg client: instance of :class:`~elasticsearch.Elasticsearch` to use (for
        read if `target_client` is specified as well)
    :arg source_index: index (or list of indices) to read documents from
    :arg target_index: name of the index in the target cluster to populate
    :arg query: body for the :meth:`~elasticsearch.Elasticsearch.search` api
    :arg target_client: optional, is specified will be used for writing (thus
        enabling reindex between clusters)
    :arg chunk_size: number of docs in one chunk sent to es (default: 500)
    :arg scroll: Specify how long a consistent view of the index should be
        maintained for scrolled search
    :arg scan_kwargs: additional kwargs to be passed to
        :func:`~elasticsearch.helpers.scan`
    :arg bulk_kwargs: additional kwargs to be passed to
        :func:`~elasticsearch.helpers.bulk`
    """
    target_client = client if target_client is None else target_client

    docs = scan(client,
        query=query,
        index=source_index,
        scroll=scroll,
        **scan_kwargs
    )
    def _change_doc_index(hits, index):
        for h in hits:
            h['_index'] = index
            if 'fields' in h:
                h.update(h.pop('fields'))
            yield h

    kwargs = {
        'stats_only': True,
    }
    kwargs.update(bulk_kwargs)
    return bulk(target_client, _change_doc_index(docs, target_index),
        chunk_size=chunk_size, **kwargs)
