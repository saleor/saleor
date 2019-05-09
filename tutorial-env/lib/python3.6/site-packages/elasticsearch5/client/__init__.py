from __future__ import unicode_literals
import logging

from ..transport import Transport
from ..exceptions import TransportError
from ..compat import string_types, urlparse, unquote
from .indices import IndicesClient
from .ingest import IngestClient
from .cluster import ClusterClient
from .cat import CatClient
from .nodes import NodesClient
from .remote import RemoteClient
from .snapshot import SnapshotClient
from .tasks import TasksClient
from .utils import query_params, _make_path, SKIP_IN_PATH

logger = logging.getLogger('elasticsearch')

def _normalize_hosts(hosts):
    """
    Helper function to transform hosts argument to
    :class:`~elasticsearch.Elasticsearch` to a list of dicts.
    """
    # if hosts are empty, just defer to defaults down the line
    if hosts is None:
        return [{}]

    # passed in just one string
    if isinstance(hosts, string_types):
        hosts = [hosts]

    out = []
    # normalize hosts to dicts
    for host in hosts:
        if isinstance(host, string_types):
            if '://' not in host:
                host = "//%s" % host

            parsed_url = urlparse(host)
            h = {"host": parsed_url.hostname}

            if parsed_url.port:
                h["port"] = parsed_url.port

            if parsed_url.scheme == "https":
                h['port'] = parsed_url.port or 443
                h['use_ssl'] = True

            if parsed_url.username or parsed_url.password:
                h['http_auth'] = '%s:%s' % (unquote(parsed_url.username),
                                            unquote(parsed_url.password))

            if parsed_url.path and parsed_url.path != '/':
                h['url_prefix'] = parsed_url.path

            out.append(h)
        else:
            out.append(host)
    return out


class Elasticsearch(object):
    """
    Elasticsearch low-level client. Provides a straightforward mapping from
    Python to ES REST endpoints.

    The instance has attributes ``cat``, ``cluster``, ``indices``, ``ingest``,
    ``nodes``, ``snapshot`` and ``tasks`` that provide access to instances of
    :class:`~elasticsearch.client.CatClient`,
    :class:`~elasticsearch.client.ClusterClient`,
    :class:`~elasticsearch.client.IndicesClient`,
    :class:`~elasticsearch.client.IngestClient`,
    :class:`~elasticsearch.client.NodesClient`,
    :class:`~elasticsearch.client.SnapshotClient` and
    :class:`~elasticsearch.client.TasksClient` respectively. This is the
    preferred (and only supported) way to get access to those classes and their
    methods.

    You can specify your own connection class which should be used by providing
    the ``connection_class`` parameter::

        # create connection to localhost using the ThriftConnection
        es = Elasticsearch(connection_class=ThriftConnection)

    If you want to turn on :ref:`sniffing` you have several options (described
    in :class:`~elasticsearch.Transport`)::

        # create connection that will automatically inspect the cluster to get
        # the list of active nodes. Start with nodes running on 'esnode1' and
        # 'esnode2'
        es = Elasticsearch(
            ['esnode1', 'esnode2'],
            # sniff before doing anything
            sniff_on_start=True,
            # refresh nodes after a node fails to respond
            sniff_on_connection_fail=True,
            # and also every 60 seconds
            sniffer_timeout=60
        )

    Different hosts can have different parameters, use a dictionary per node to
    specify those::

        # connect to localhost directly and another node using SSL on port 443
        # and an url_prefix. Note that ``port`` needs to be an int.
        es = Elasticsearch([
            {'host': 'localhost'},
            {'host': 'othernode', 'port': 443, 'url_prefix': 'es', 'use_ssl': True},
        ])

    If using SSL, there are several parameters that control how we deal with
    certificates (see :class:`~elasticsearch.Urllib3HttpConnection` for
    detailed description of the options)::

        es = Elasticsearch(
            ['localhost:443', 'other_host:443'],
            # turn on SSL
            use_ssl=True,
            # make sure we verify SSL certificates (off by default)
            verify_certs=True,
            # provide a path to CA certs on disk
            ca_certs='/path/to/CA_certs'
        )

    SSL client authentication is supported
    (see :class:`~elasticsearch.Urllib3HttpConnection` for
    detailed description of the options)::

        es = Elasticsearch(
            ['localhost:443', 'other_host:443'],
            # turn on SSL
            use_ssl=True,
            # make sure we verify SSL certificates (off by default)
            verify_certs=True,
            # provide a path to CA certs on disk
            ca_certs='/path/to/CA_certs',
            # PEM formatted SSL client certificate
            client_cert='/path/to/clientcert.pem',
            # PEM formatted SSL client key
            client_key='/path/to/clientkey.pem'
        )

    Alternatively you can use RFC-1738 formatted URLs, as long as they are not
    in conflict with other options::

        es = Elasticsearch(
            [
                'http://user:secret@localhost:9200/',
                'https://user:secret@other_host:443/production'
            ],
            verify_certs=True
        )

    """
    def __init__(self, hosts=None, transport_class=Transport, **kwargs):
        """
        :arg hosts: list of nodes we should connect to. Node should be a
            dictionary ({"host": "localhost", "port": 9200}), the entire dictionary
            will be passed to the :class:`~elasticsearch.Connection` class as
            kwargs, or a string in the format of ``host[:port]`` which will be
            translated to a dictionary automatically.  If no value is given the
            :class:`~elasticsearch.Urllib3HttpConnection` class defaults will be used.

        :arg transport_class: :class:`~elasticsearch.Transport` subclass to use.

        :arg kwargs: any additional arguments will be passed on to the
            :class:`~elasticsearch.Transport` class and, subsequently, to the
            :class:`~elasticsearch.Connection` instances.
        """
        self.transport = transport_class(_normalize_hosts(hosts), **kwargs)

        # namespaced clients for compatibility with API names
        self.indices = IndicesClient(self)
        self.ingest = IngestClient(self)
        self.cluster = ClusterClient(self)
        self.cat = CatClient(self)
        self.nodes = NodesClient(self)
        self.remote = RemoteClient(self)
        self.snapshot = SnapshotClient(self)
        self.tasks = TasksClient(self)

    def __repr__(self):
        try:
            # get a lost of all connections
            cons = self.transport.hosts
            # truncate to 10 if there are too many
            if len(cons) > 5:
                cons = cons[:5] + ['...']
            return '<Elasticsearch(%r)>' % cons
        except:
            # probably operating on custom transport and connection_pool, ignore
            return super(Elasticsearch, self).__repr__()

    def _bulk_body(self, body):
        # if not passed in a string, serialize items and join by newline
        if not isinstance(body, string_types):
            body = '\n'.join(map(self.transport.serializer.dumps, body))

        # bulk body must end with a newline
        if not body.endswith('\n'):
            body += '\n'

        return body

    @query_params()
    def ping(self, params=None):
        """
        Returns True if the cluster is up, False otherwise.
        `<http://www.elastic.co/guide/>`_
        """
        try:
            return self.transport.perform_request('HEAD', '/', params=params)
        except TransportError:
            return False

    @query_params()
    def info(self, params=None):
        """
        Get the basic info from the current cluster.
        `<http://www.elastic.co/guide/>`_
        """
        return self.transport.perform_request('GET', '/', params=params)

    @query_params('parent', 'pipeline', 'refresh', 'routing', 'timeout',
        'timestamp', 'ttl', 'version', 'version_type', 'wait_for_active_shards')
    def create(self, index, doc_type, id, body, params=None):
        """
        Adds a typed JSON document in a specific index, making it searchable.
        Behind the scenes this method calls index(..., op_type='create')
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index_.html>`_

        :arg index: The name of the index
        :arg doc_type: The type of the document
        :arg id: Document ID
        :arg body: The document
        :arg parent: ID of the parent document
        :arg pipeline: The pipeline id to preprocess incoming documents with
        :arg refresh: If `true` then refresh the affected shards to make this
            operation visible to search, if `wait_for` then wait for a refresh
            to make this operation visible to search, if `false` (the default)
            then do nothing with refreshes., valid choices are: u'true',
            u'false', u'wait_for'
        :arg routing: Specific routing value
        :arg timeout: Explicit operation timeout
        :arg timestamp: Explicit timestamp for the document
        :arg ttl: Expiration time for the document
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are:
            u'internal', u'external', u'external_gte', u'force'
        :arg wait_for_active_shards: Sets the number of shard copies that must
            be active before proceeding with the index operation. Defaults to 1,
            meaning the primary shard only. Set to `all` for all shard copies,
            otherwise set to any non-negative value less than or equal to the
            total number of copies for the shard (number of replicas + 1)
        """
        for param in (index, doc_type, id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path(index, doc_type,
            id, '_create'), params=params, body=body)

    @query_params('op_type', 'parent', 'pipeline', 'refresh', 'routing',
        'timeout', 'timestamp', 'ttl', 'version', 'version_type',
        'wait_for_active_shards')
    def index(self, index, doc_type, body, id=None, params=None):
        """
        Adds or updates a typed JSON document in a specific index, making it searchable.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-index_.html>`_

        :arg index: The name of the index
        :arg doc_type: The type of the document
        :arg body: The document
        :arg id: Document ID
        :arg op_type: Explicit operation type, default 'index', valid choices
            are: 'index', 'create'
        :arg parent: ID of the parent document
        :arg pipeline: The pipeline id to preprocess incoming documents with
        :arg refresh: If `true` then refresh the affected shards to make this
            operation visible to search, if `wait_for` then wait for a refresh
            to make this operation visible to search, if `false` (the default)
            then do nothing with refreshes., valid choices are: u'true',
            u'false', u'wait_for'
        :arg routing: Specific routing value
        :arg timeout: Explicit operation timeout
        :arg timestamp: Explicit timestamp for the document
        :arg ttl: Expiration time for the document
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        :arg wait_for_active_shards: Sets the number of shard copies that must
            be active before proceeding with the index operation. Defaults to 1,
            meaning the primary shard only. Set to `all` for all shard copies,
            otherwise set to any non-negative value less than or equal to the
            total number of copies for the shard (number of replicas + 1)
        """
        for param in (index, doc_type, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST' if id in SKIP_IN_PATH else 'PUT',
            _make_path(index, doc_type, id), params=params, body=body)

    @query_params('_source', '_source_exclude', '_source_include', 'parent',
        'preference', 'realtime', 'refresh', 'routing', 'stored_fields',
        'version', 'version_type')
    def exists(self, index, doc_type, id, params=None):
        """
        Returns a boolean indicating whether or not given document exists in Elasticsearch.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-get.html>`_

        :arg index: The name of the index
        :arg doc_type: The type of the document (use `_all` to fetch the first
            document matching the ID across all types)
        :arg id: The document ID
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg parent: The ID of the parent document
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg realtime: Specify whether to perform the operation in realtime or
            search mode
        :arg refresh: Refresh the shard containing the document before
            performing the operation
        :arg routing: Specific routing value
        :arg stored_fields: A comma-separated list of stored fields to return in
            the response
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        """
        for param in (index, doc_type, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('HEAD', _make_path(index,
            doc_type, id), params=params)

    @query_params('_source', '_source_exclude', '_source_include', 'parent',
        'preference', 'realtime', 'refresh', 'routing', 'version',
        'version_type')
    def exists_source(self, index, doc_type, id, params=None):
        """
        `<http://www.elastic.co/guide/en/elasticsearch/reference/master/docs-get.html>`_

        :arg index: The name of the index
        :arg doc_type: The type of the document; use `_all` to fetch the first
            document matching the ID across all types
        :arg id: The document ID
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg parent: The ID of the parent document
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg realtime: Specify whether to perform the operation in realtime or
            search mode
        :arg refresh: Refresh the shard containing the document before
            performing the operation
        :arg routing: Specific routing value
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        """
        for param in (index, doc_type, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('HEAD', _make_path(index,
            doc_type, id, '_source'), params=params)

    @query_params('_source', '_source_exclude', '_source_include', 'parent',
        'preference', 'realtime', 'refresh', 'routing', 'stored_fields',
        'version', 'version_type')
    def get(self, index, id, doc_type='_all', params=None):
        """
        Get a typed JSON document from the index based on its id.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-get.html>`_

        :arg index: The name of the index
        :arg id: The document ID
        :arg doc_type: The type of the document (use `_all` to fetch the first
            document matching the ID across all types)
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg parent: The ID of the parent document
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg realtime: Specify whether to perform the operation in realtime or
            search mode
        :arg refresh: Refresh the shard containing the document before
            performing the operation
        :arg routing: Specific routing value
        :arg stored_fields: A comma-separated list of stored fields to return in
            the response
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        """
        for param in (index, doc_type, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, id), params=params)

    @query_params('_source', '_source_exclude', '_source_include', 'parent',
        'preference', 'realtime', 'refresh', 'routing', 'version',
        'version_type')
    def get_source(self, index, doc_type, id, params=None):
        """
        Get the source of a document by it's index, type and id.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-get.html>`_

        :arg index: The name of the index
        :arg doc_type: The type of the document; use `_all` to fetch the first
            document matching the ID across all types
        :arg id: The document ID
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg parent: The ID of the parent document
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg realtime: Specify whether to perform the operation in realtime or
            search mode
        :arg refresh: Refresh the shard containing the document before
            performing the operation
        :arg routing: Specific routing value
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        """
        for param in (index, doc_type, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, id, '_source'), params=params)

    @query_params('_source', '_source_exclude', '_source_include', 'preference',
        'realtime', 'refresh', 'stored_fields')
    def mget(self, body, index=None, doc_type=None, params=None):
        """
        Get multiple documents based on an index, type (optional) and ids.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-multi-get.html>`_

        :arg body: Document identifiers; can be either `docs` (containing full
            document information) or `ids` (when index and type is provided in
            the URL.
        :arg index: The name of the index
        :arg doc_type: The type of the document
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg realtime: Specify whether to perform the operation in realtime or
            search mode
        :arg refresh: Refresh the shard containing the document before
            performing the operation
        :arg stored_fields: A comma-separated list of stored fields to return in
            the response
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_mget'), params=params, body=body)

    @query_params('_source', '_source_exclude', '_source_include', 'fields',
        'lang', 'parent', 'refresh', 'retry_on_conflict', 'routing', 'timeout',
        'timestamp', 'ttl', 'version', 'version_type', 'wait_for_active_shards')
    def update(self, index, doc_type, id, body=None, params=None):
        """
        Update a document based on a script or partial data provided.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-update.html>`_

        :arg index: The name of the index
        :arg doc_type: The type of the document
        :arg id: Document ID
        :arg body: The request definition using either `script` or partial `doc`
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg fields: A comma-separated list of fields to return in the response
        :arg lang: The script language (default: painless)
        :arg parent: ID of the parent document. Is is only used for routing and
            when for the upsert request
        :arg refresh: If `true` then refresh the effected shards to make this
            operation visible to search, if `wait_for` then wait for a refresh
            to make this operation visible to search, if `false` (the default)
            then do nothing with refreshes., valid choices are: 'true', 'false',
            'wait_for'
        :arg retry_on_conflict: Specify how many times should the operation be
            retried when a conflict occurs (default: 0)
        :arg routing: Specific routing value
        :arg timeout: Explicit operation timeout
        :arg timestamp: Explicit timestamp for the document
        :arg ttl: Expiration time for the document
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'force'
        :arg wait_for_active_shards: Sets the number of shard copies that must
            be active before proceeding with the update operation. Defaults to
            1, meaning the primary shard only. Set to `all` for all shard
            copies, otherwise set to any non-negative value less than or equal
            to the total number of copies for the shard (number of replicas + 1)
        """
        for param in (index, doc_type, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST', _make_path(index,
            doc_type, id, '_update'), params=params, body=body)

    @query_params('_source', '_source_exclude', '_source_include',
        'allow_no_indices', 'analyze_wildcard', 'analyzer',
        'batched_reduce_size', 'default_operator', 'df', 'docvalue_fields',
        'expand_wildcards', 'explain', 'fielddata_fields', 'from_',
        'ignore_unavailable', 'lenient', 'lowercase_expanded_terms',
        'pre_filter_shard_size', 'preference', 'q', 'request_cache', 'routing',
        'scroll', 'search_type', 'size', 'sort', 'stats', 'stored_fields',
        'suggest_field', 'suggest_mode', 'suggest_size', 'suggest_text',
        'terminate_after', 'timeout', 'track_scores', 'typed_keys', 'version')
    def search(self, index=None, doc_type=None, body=None, params=None):
        """
        Execute a search query and get back search hits that match the query.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-search.html>`_

        :arg index: A comma-separated list of index names to search; use `_all`
            or empty string to perform the operation on all indices
        :arg doc_type: A comma-separated list of document types to search; leave
            empty to perform the operation on all types
        :arg body: The search definition using the Query DSL
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg analyze_wildcard: Specify whether wildcard and prefix queries
            should be analyzed (default: false)
        :arg analyzer: The analyzer to use for the query string
        :arg batched_reduce_size: The number of shard results that should be
            reduced at once on the coordinating node. This value should be used
            as a protection mechanism to reduce the memory overhead per search
            request if the potential number of shards in the request can be
            large., default 512
        :arg default_operator: The default operator for query string query (AND
            or OR), default 'OR', valid choices are: 'AND', 'OR'
        :arg df: The field to use as default where no field prefix is given in
            the query string
        :arg docvalue_fields: A comma-separated list of fields to return as the
            docvalue representation of a field for each hit
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg explain: Specify whether to return detailed information about score
            computation as part of a hit
        :arg fielddata_fields: A comma-separated list of fields to return as the
            docvalue representation of a field for each hit
        :arg from\_: Starting offset (default: 0)
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg lenient: Specify whether format-based query failures (such as
            providing text to a numeric field) should be ignored
        :arg lowercase_expanded_terms: Specify whether query terms should be
            lowercased
        :arg pre_filter_shard_size: A threshold that enforces a pre-filter
            roundtrip to prefilter search shards based on query rewriting if
            the number of shards the search request expands to exceeds the
            threshold. This filter roundtrip can limit the number of shards
            significantly if for instance a shard can not match any documents based
            on it's rewrite method ie. if date filters are mandatory to match
            but the shard bounds and the query are disjoint. (default: 128)
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg q: Query in the Lucene query string syntax
        :arg request_cache: Specify if request cache should be used for this
            request or not, defaults to index level setting
        :arg routing: A comma-separated list of specific routing values
        :arg scroll: Specify how long a consistent view of the index should be
            maintained for scrolled search
        :arg search_type: Search operation type, valid choices are:
            'query_then_fetch', 'dfs_query_then_fetch'
        :arg size: Number of hits to return (default: 10)
        :arg sort: A comma-separated list of <field>:<direction> pairs
        :arg stats: Specific 'tag' of the request for logging and statistical
            purposes
        :arg stored_fields: A comma-separated list of stored fields to return as
            part of a hit
        :arg suggest_field: Specify which field to use for suggestions
        :arg suggest_mode: Specify suggest mode, default 'missing', valid
            choices are: 'missing', 'popular', 'always'
        :arg suggest_size: How many suggestions to return in response
        :arg suggest_text: The source text for which the suggestions should be
            returned
        :arg terminate_after: The maximum number of documents to collect for
            each shard, upon reaching which the query execution will terminate
            early.
        :arg timeout: Explicit operation timeout
        :arg track_scores: Whether to calculate and return scores even if they
            are not used for sorting
        :arg typed_keys: Specify whether aggregation and suggester names should
            be prefixed by their respective types in the response
        :arg version: Specify whether to return document version as part of a
            hit
        """
        # from is a reserved word so it cannot be used, use from_ instead
        if 'from_' in params:
            params['from'] = params.pop('from_')

        if doc_type and not index:
            index = '_all'
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_search'), params=params, body=body)

    @query_params('_source', '_source_exclude', '_source_include',
        'allow_no_indices', 'analyze_wildcard', 'analyzer', 'conflicts',
        'default_operator', 'df', 'docvalue_fields', 'expand_wildcards',
        'explain', 'fielddata_fields', 'from_', 'ignore_unavailable', 'lenient',
        'lowercase_expanded_terms', 'pipeline', 'preference', 'q', 'refresh',
        'request_cache', 'requests_per_second', 'routing', 'scroll',
        'scroll_size', 'search_timeout', 'search_type', 'size', 'sort', 'stats',
        'stored_fields', 'suggest_field', 'suggest_mode', 'suggest_size',
        'suggest_text', 'terminate_after', 'timeout', 'track_scores', 'version',
        'version_type', 'wait_for_active_shards', 'wait_for_completion')
    def update_by_query(self, index, doc_type=None, body=None, params=None):
        """
        Perform an update on all documents matching a query.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-update-by-query.html>`_

        :arg index: A comma-separated list of index names to search; use `_all`
            or empty string to perform the operation on all indices
        :arg doc_type: A comma-separated list of document types to search; leave
            empty to perform the operation on all types
        :arg body: The search definition using the Query DSL
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg analyze_wildcard: Specify whether wildcard and prefix queries
            should be analyzed (default: false)
        :arg analyzer: The analyzer to use for the query string
        :arg conflicts: What to do when the reindex hits version conflicts?,
            default 'abort', valid choices are: 'abort', 'proceed'
        :arg default_operator: The default operator for query string query (AND
            or OR), default 'OR', valid choices are: 'AND', 'OR'
        :arg df: The field to use as default where no field prefix is given in
            the query string
        :arg docvalue_fields: A comma-separated list of fields to return as the
            docvalue representation of a field for each hit
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg explain: Specify whether to return detailed information about score
            computation as part of a hit
        :arg fielddata_fields: A comma-separated list of fields to return as the
            docvalue representation of a field for each hit
        :arg from\_: Starting offset (default: 0)
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg lenient: Specify whether format-based query failures (such as
            providing text to a numeric field) should be ignored
        :arg lowercase_expanded_terms: Specify whether query terms should be
            lowercased
        :arg pipeline: Ingest pipeline to set on index requests made by this
            action. (default: none)
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg q: Query in the Lucene query string syntax
        :arg refresh: Should the effected indexes be refreshed?
        :arg request_cache: Specify if request cache should be used for this
            request or not, defaults to index level setting
        :arg requests_per_second: The throttle to set on this request in sub-
            requests per second. -1 means set no throttle as does "unlimited"
            which is the only non-float this accepts., default 0
        :arg routing: A comma-separated list of specific routing values
        :arg scroll: Specify how long a consistent view of the index should be
            maintained for scrolled search
        :arg scroll_size: Size on the scroll request powering the
            update_by_query
        :arg search_timeout: Explicit timeout for each search request. Defaults
            to no timeout.
        :arg search_type: Search operation type, valid choices are:
            'query_then_fetch', 'dfs_query_then_fetch'
        :arg size: Number of hits to return (default: 10)
        :arg slices: The number of slices this task should be divided into.
            Defaults to 1 meaning the task isn't sliced into subtasks., default
            1
        :arg sort: A comma-separated list of <field>:<direction> pairs
        :arg stats: Specific 'tag' of the request for logging and statistical
            purposes
        :arg stored_fields: A comma-separated list of stored fields to return as
            part of a hit
        :arg suggest_field: Specify which field to use for suggestions
        :arg suggest_mode: Specify suggest mode, default 'missing', valid
            choices are: 'missing', 'popular', 'always'
        :arg suggest_size: How many suggestions to return in response
        :arg suggest_text: The source text for which the suggestions should be
            returned
        :arg terminate_after: The maximum number of documents to collect for
            each shard, upon reaching which the query execution will terminate
            early.
        :arg timeout: Time each individual bulk request should wait for shards
            that are unavailable., default '1m'
        :arg track_scores: Whether to calculate and return scores even if they
            are not used for sorting
        :arg version: Specify whether to return document version as part of a
            hit
        :arg version_type: Should the document increment the version number
            (internal) on hit or not (reindex)
        :arg wait_for_active_shards: Sets the number of shard copies that must
            be active before proceeding with the update by query operation.
            Defaults to 1, meaning the primary shard only. Set to `all` for all
            shard copies, otherwise set to any non-negative value less than or
            equal to the total number of copies for the shard (number of
            replicas + 1)
        :arg wait_for_completion: Should the request should block until the
            reindex is complete., default True
        """
        if index in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'index'.")
        return self.transport.perform_request('POST', _make_path(index,
            doc_type, '_update_by_query'), params=params, body=body)

    @query_params('refresh', 'requests_per_second', 'slices', 'timeout',
        'wait_for_active_shards', 'wait_for_completion')
    def reindex(self, body, params=None):
        """
        Reindex all documents from one index to another.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-reindex.html>`_

        :arg body: The search definition using the Query DSL and the prototype
            for the index request.
        :arg refresh: Should the effected indexes be refreshed?
        :arg requests_per_second: The throttle to set on this request in sub-
            requests per second. -1 means set no throttle as does "unlimited"
            which is the only non-float this accepts., default 0
        :arg slices: The number of slices this task should be divided into.
            Defaults to 1 meaning the task isn't sliced into subtasks., default
            1
        :arg timeout: Time each individual bulk request should wait for shards
            that are unavailable., default '1m'
        :arg wait_for_active_shards: Sets the number of shard copies that must
            be active before proceeding with the reindex operation. Defaults to
            1, meaning the primary shard only. Set to `all` for all shard
            copies, otherwise set to any non-negative value less than or equal
            to the total number of copies for the shard (number of replicas + 1)
        :arg wait_for_completion: Should the request should block until the
            reindex is complete., default True
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('POST', '/_reindex',
            params=params, body=body)

    @query_params('requests_per_second')
    def reindex_rethrottle(self, task_id=None, params=None):
        """
        Change the value of ``requests_per_second`` of a running ``reindex`` task.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-reindex.html>`_

        :arg task_id: The task id to rethrottle
        :arg requests_per_second: The throttle to set on this request in
            floating sub-requests per second. -1 means set no throttle.
        """
        return self.transport.perform_request('POST', _make_path('_reindex',
            task_id, '_rethrottle'), params=params)

    @query_params('_source', '_source_exclude', '_source_include',
        'allow_no_indices', 'analyze_wildcard', 'analyzer', 'conflicts',
        'default_operator', 'df', 'docvalue_fields', 'expand_wildcards',
        'explain', 'from_', 'ignore_unavailable', 'lenient',
        'lowercase_expanded_terms', 'preference', 'q', 'refresh',
        'request_cache', 'requests_per_second', 'routing', 'scroll', 'slices',
        'scroll_size', 'search_timeout', 'search_type', 'size', 'sort', 'stats',
        'stored_fields', 'suggest_field', 'suggest_mode', 'suggest_size',
        'suggest_text', 'terminate_after', 'timeout', 'track_scores', 'version',
        'wait_for_active_shards', 'wait_for_completion')
    def delete_by_query(self, index, body, doc_type=None, params=None):
        """
        Delete all documents matching a query.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-delete-by-query.html>`_

        :arg index: A comma-separated list of index names to search; use `_all`
            or empty string to perform the operation on all indices
        :arg body: The search definition using the Query DSL
        :arg doc_type: A comma-separated list of document types to search; leave
            empty to perform the operation on all types
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg analyze_wildcard: Specify whether wildcard and prefix queries
            should be analyzed (default: false)
        :arg analyzer: The analyzer to use for the query string
        :arg conflicts: What to do when the delete-by-query hits version
            conflicts?, default 'abort', valid choices are: 'abort', 'proceed'
        :arg default_operator: The default operator for query string query (AND
            or OR), default 'OR', valid choices are: 'AND', 'OR'
        :arg df: The field to use as default where no field prefix is given in
            the query string
        :arg docvalue_fields: A comma-separated list of fields to return as the
            docvalue representation of a field for each hit
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg explain: Specify whether to return detailed information about score
            computation as part of a hit
        :arg from\_: Starting offset (default: 0)
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg lenient: Specify whether format-based query failures (such as
            providing text to a numeric field) should be ignored
        :arg lowercase_expanded_terms: Specify whether query terms should be
            lowercased
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg q: Query in the Lucene query string syntax
        :arg refresh: Should the effected indexes be refreshed?
        :arg request_cache: Specify if request cache should be used for this
            request or not, defaults to index level setting
        :arg requests_per_second: The throttle for this request in sub-requests
            per second. -1 means no throttle., default 0
        :arg routing: A comma-separated list of specific routing values
        :arg scroll: Specify how long a consistent view of the index should be
            maintained for scrolled search
        :arg scroll_size: Size on the scroll request powering the
            update_by_query
        :arg search_timeout: Explicit timeout for each search request. Defaults
            to no timeout.
        :arg search_type: Search operation type, valid choices are:
            'query_then_fetch', 'dfs_query_then_fetch'
        :arg size: Number of hits to return (default: 10)
        :arg slices: The number of slices this task should be divided into.
            Defaults to 1 meaning the task isn't sliced into subtasks., default
            1
        :arg sort: A comma-separated list of <field>:<direction> pairs
        :arg stats: Specific 'tag' of the request for logging and statistical
            purposes
        :arg stored_fields: A comma-separated list of stored fields to return as
            part of a hit
        :arg suggest_field: Specify which field to use for suggestions
        :arg suggest_mode: Specify suggest mode, default 'missing', valid
            choices are: 'missing', 'popular', 'always'
        :arg suggest_size: How many suggestions to return in response
        :arg suggest_text: The source text for which the suggestions should be
            returned
        :arg terminate_after: The maximum number of documents to collect for
            each shard, upon reaching which the query execution will terminate
            early.
        :arg timeout: Time each individual bulk request should wait for shards
            that are unavailable., default '1m'
        :arg track_scores: Whether to calculate and return scores even if they
            are not used for sorting
        :arg version: Specify whether to return document version as part of a
            hit
        :arg wait_for_active_shards: Sets the number of shard copies that must
            be active before proceeding with the delete by query operation.
            Defaults to 1, meaning the primary shard only. Set to `all` for all
            shard copies, otherwise set to any non-negative value less than or
            equal to the total number of copies for the shard (number of
            replicas + 1)
        :arg wait_for_completion: Should the request should block until the
            delete-by-query is complete., default True
        """
        for param in (index, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('POST', _make_path(index,
            doc_type, '_delete_by_query'), params=params, body=body)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'local', 'preference', 'routing')
    def search_shards(self, index=None, doc_type=None, params=None):
        """
        The search shards api returns the indices and shards that a search
        request would be executed against. This can give useful feedback for working
        out issues or planning optimizations with routing and shard preferences.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-shards.html>`_

        :arg index: A comma-separated list of index names to search; use `_all`
            or empty string to perform the operation on all indices
        :arg doc_type: A comma-separated list of document types to search; leave
            empty to perform the operation on all types
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg routing: Specific routing value
        """
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_search_shards'), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'explain',
        'ignore_unavailable', 'preference', 'profile', 'routing', 'scroll',
        'search_type', 'typed_keys')
    def search_template(self, index=None, doc_type=None, body=None, params=None):
        """
        A query that accepts a query template and a map of key/value pairs to
        fill in template parameters.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-template.html>`_

        :arg index: A comma-separated list of index names to search; use `_all`
            or empty string to perform the operation on all indices
        :arg doc_type: A comma-separated list of document types to search; leave
            empty to perform the operation on all types
        :arg body: The search definition template and its params
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg explain: Specify whether to return detailed information about score
            computation as part of a hit
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg profile: Specify whether to profile the query execution
        :arg routing: A comma-separated list of specific routing values
        :arg scroll: Specify how long a consistent view of the index should be
            maintained for scrolled search
        :arg search_type: Search operation type, valid choices are:
            'query_then_fetch', 'query_and_fetch', 'dfs_query_then_fetch',
            'dfs_query_and_fetch'
        :arg typed_keys: Specify whether aggregation and suggester names should
            be prefixed by their respective types in the response
        """
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_search', 'template'), params=params, body=body)

    @query_params('_source', '_source_exclude', '_source_include',
        'analyze_wildcard', 'analyzer', 'default_operator', 'df', 'lenient',
        'lowercase_expanded_terms', 'parent', 'preference', 'q', 'routing',
        'stored_fields')
    def explain(self, index, doc_type, id, body=None, params=None):
        """
        The explain api computes a score explanation for a query and a specific
        document. This can give useful feedback whether a document matches or
        didn't match a specific query.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-explain.html>`_

        :arg index: The name of the index
        :arg doc_type: The type of the document
        :arg id: The document ID
        :arg body: The query definition using the Query DSL
        :arg _source: True or false to return the _source field or not, or a
            list of fields to return
        :arg _source_exclude: A list of fields to exclude from the returned
            _source field
        :arg _source_include: A list of fields to extract and return from the
            _source field
        :arg analyze_wildcard: Specify whether wildcards and prefix queries in
            the query string query should be analyzed (default: false)
        :arg analyzer: The analyzer for the query string query
        :arg default_operator: The default operator for query string query (AND
            or OR), default 'OR', valid choices are: 'AND', 'OR'
        :arg df: The default field for query string query (default: _all)
        :arg lenient: Specify whether format-based query failures (such as
            providing text to a numeric field) should be ignored
        :arg lowercase_expanded_terms: Specify whether query terms should be
            lowercased
        :arg parent: The ID of the parent document
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg q: Query in the Lucene query string syntax
        :arg routing: Specific routing value
        :arg stored_fields: A comma-separated list of stored fields to return in
            the response
        """
        for param in (index, doc_type, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, id, '_explain'), params=params, body=body)

    @query_params('scroll')
    def scroll(self, scroll_id=None, body=None, params=None):
        """
        Scroll a search request created by specifying the scroll parameter.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-scroll.html>`_

        :arg scroll_id: The scroll ID
        :arg body: The scroll ID if not passed by URL or query parameter.
        :arg scroll: Specify how long a consistent view of the index should be
            maintained for scrolled search
        """
        if scroll_id in SKIP_IN_PATH and body in SKIP_IN_PATH:
            raise ValueError("You need to supply scroll_id or body.")
        elif scroll_id and not body:
            body = {'scroll_id':scroll_id}
        elif scroll_id:
            params['scroll_id'] = scroll_id

        return self.transport.perform_request('GET', '/_search/scroll',
            params=params, body=body)

    @query_params()
    def clear_scroll(self, scroll_id=None, body=None, params=None):
        """
        Clear the scroll request created by specifying the scroll parameter to
        search.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-scroll.html>`_

        :arg scroll_id: A comma-separated list of scroll IDs to clear
        :arg body: A comma-separated list of scroll IDs to clear if none was
            specified via the scroll_id parameter
        """
        if scroll_id in SKIP_IN_PATH and body in SKIP_IN_PATH:
            raise ValueError("You need to supply scroll_id or body.")
        elif scroll_id and not body:
            body = {'scroll_id':[scroll_id]}
        elif scroll_id:
            params['scroll_id'] = scroll_id

        return self.transport.perform_request('DELETE', '/_search/scroll',
            params=params, body=body)

    @query_params('parent', 'refresh', 'routing', 'timeout', 'version',
        'version_type', 'wait_for_active_shards')
    def delete(self, index, doc_type, id, params=None):
        """
        Delete a typed JSON document from a specific index based on its id.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-delete.html>`_

        :arg index: The name of the index
        :arg doc_type: The type of the document
        :arg id: The document ID
        :arg parent: ID of parent document
        :arg refresh: If `true` then refresh the effected shards to make this
            operation visible to search, if `wait_for` then wait for a refresh
            to make this operation visible to search, if `false` (the default)
            then do nothing with refreshes., valid choices are: 'true', 'false',
            'wait_for'
        :arg routing: Specific routing value
        :arg timeout: Explicit operation timeout
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        :arg wait_for_active_shards: Sets the number of shard copies that must
            be active before proceeding with the delete operation. Defaults to
            1, meaning the primary shard only. Set to `all` for all shard
            copies, otherwise set to any non-negative value less than or equal
            to the total number of copies for the shard (number of replicas + 1)
        """
        for param in (index, doc_type, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('DELETE', _make_path(index,
            doc_type, id), params=params)

    @query_params('allow_no_indices', 'analyze_wildcard', 'analyzer',
        'default_operator', 'df', 'expand_wildcards', 'ignore_unavailable',
        'lenient', 'lowercase_expanded_terms', 'min_score', 'preference', 'q',
        'routing')
    def count(self, index=None, doc_type=None, body=None, params=None):
        """
        Execute a query and get the number of matches for that query.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-count.html>`_

        :arg index: A comma-separated list of indices to restrict the results
        :arg doc_type: A comma-separated list of types to restrict the results
        :arg body: A query to restrict the results specified with the Query DSL
            (optional)
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg analyze_wildcard: Specify whether wildcard and prefix queries
            should be analyzed (default: false)
        :arg analyzer: The analyzer to use for the query string
        :arg default_operator: The default operator for query string query (AND
            or OR), default 'OR', valid choices are: 'AND', 'OR'
        :arg df: The field to use as default where no field prefix is given in
            the query string
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg lenient: Specify whether format-based query failures (such as
            providing text to a numeric field) should be ignored
        :arg lowercase_expanded_terms: Specify whether query terms should be
            lowercased
        :arg min_score: Include only documents with a specific `_score` value in
            the result
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg q: Query in the Lucene query string syntax
        :arg routing: Specific routing value
        """
        if doc_type and not index:
            index = '_all'

        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_count'), params=params, body=body)

    @query_params('_source', '_source_exclude', '_source_include', 'fields',
        'pipeline', 'refresh', 'routing', 'timeout', 'wait_for_active_shards')
    def bulk(self, body, index=None, doc_type=None, params=None):
        """
        Perform many index/delete operations in a single API call.

        See the :func:`~elasticsearch.helpers.bulk` helper function for a more
        friendly API.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-bulk.html>`_

        :arg body: The operation definition and data (action-data pairs),
            separated by newlines
        :arg index: Default index for items which don't provide one
        :arg doc_type: Default document type for items which don't provide one
        :arg _source: True or false to return the _source field or not, or
            default list of fields to return, can be overridden on each sub-
            request
        :arg _source_exclude: Default list of fields to exclude from the
            returned _source field, can be overridden on each sub-request
        :arg _source_include: Default list of fields to extract and return from
            the _source field, can be overridden on each sub-request
        :arg fields: Default comma-separated list of fields to return in the
            response for updates, can be overridden on each sub-request
        :arg pipeline: The pipeline id to preprocess incoming documents with
        :arg refresh: If `true` then refresh the effected shards to make this
            operation visible to search, if `wait_for` then wait for a refresh
            to make this operation visible to search, if `false` (the default)
            then do nothing with refreshes., valid choices are: 'true', 'false',
            'wait_for'
        :arg routing: Specific routing value
        :arg timeout: Explicit operation timeout
        :arg wait_for_active_shards: Sets the number of shard copies that must
            be active before proceeding with the bulk operation. Defaults to 1,
            meaning the primary shard only. Set to `all` for all shard copies,
            otherwise set to any non-negative value less than or equal to the
            total number of copies for the shard (number of replicas + 1)
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('POST', _make_path(index,
            doc_type, '_bulk'), params=params, body=self._bulk_body(body))

    @query_params('max_concurrent_searches', 'search_type', 'typed_keys')
    def msearch(self, body, index=None, doc_type=None, params=None):
        """
        Execute several search requests within the same API.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-multi-search.html>`_

        :arg body: The request definitions (metadata-search request definition
            pairs), separated by newlines
        :arg index: A comma-separated list of index names to use as default
        :arg doc_type: A comma-separated list of document types to use as
            default
        :arg max_concurrent_searches: Controls the maximum number of concurrent
            searches the multi search api will execute
        :arg search_type: Search operation type, valid choices are:
            'query_then_fetch', 'query_and_fetch', 'dfs_query_then_fetch',
            'dfs_query_and_fetch'
        :arg typed_keys: Specify whether aggregation and suggester names should
            be prefixed by their respective types in the response
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_msearch'), params=params, body=self._bulk_body(body))

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'preference', 'routing')
    def suggest(self, body, index=None, params=None):
        """
        The suggest feature suggests similar looking terms based on a provided
        text by using a suggester.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters.html>`_

        :arg body: The request definition
        :arg index: A comma-separated list of index names to restrict the
            operation; use `_all` or empty string to perform the operation on
            all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg routing: Specific routing value
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('POST', _make_path(index,
            '_suggest'), params=params, body=body)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'percolate_format', 'percolate_index', 'percolate_preference',
        'percolate_routing', 'percolate_type', 'preference', 'routing',
        'version', 'version_type')
    def percolate(self, index, doc_type, id=None, body=None, params=None):
        """
        The percolator allows to register queries against an index, and then
        send percolate requests which include a doc, and getting back the
        queries that match on that doc out of the set of registered queries.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-percolate.html>`_

        :arg index: The index of the document being percolated.
        :arg doc_type: The type of the document being percolated.
        :arg id: Substitute the document in the request body with a document
            that is known by the specified id. On top of the id, the index and
            type parameter will be used to retrieve the document from within the
            cluster.
        :arg body: The percolator request definition using the percolate DSL
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg percolate_format: Return an array of matching query IDs instead of
            objects, valid choices are: 'ids'
        :arg percolate_index: The index to percolate the document into. Defaults
            to index.
        :arg percolate_preference: Which shard to prefer when executing the
            percolate request.
        :arg percolate_routing: The routing value to use when percolating the
            existing document.
        :arg percolate_type: The type to percolate document into. Defaults to
            type.
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg routing: A comma-separated list of specific routing values
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        """
        for param in (index, doc_type):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, id, '_percolate'), params=params, body=body)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable')
    def mpercolate(self, body, index=None, doc_type=None, params=None):
        """
        The percolator allows to register queries against an index, and then
        send percolate requests which include a doc, and getting back the
        queries that match on that doc out of the set of registered queries.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-percolate.html>`_

        :arg body: The percolate request definitions (header & body pair),
            separated by newlines
        :arg index: The index of the document being count percolated to use as
            default
        :arg doc_type: The type of the document being percolated to use as
            default.
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_mpercolate'), params=params, body=self._bulk_body(body))

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'percolate_index', 'percolate_type', 'preference', 'routing', 'version',
        'version_type')
    def count_percolate(self, index, doc_type, id=None, body=None, params=None):
        """
        The percolator allows to register queries against an index, and then
        send percolate requests which include a doc, and getting back the
        queries that match on that doc out of the set of registered queries.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-percolate.html>`_

        :arg index: The index of the document being count percolated.
        :arg doc_type: The type of the document being count percolated.
        :arg id: Substitute the document in the request body with a document
            that is known by the specified id. On top of the id, the index and
            type parameter will be used to retrieve the document from within the
            cluster.
        :arg body: The count percolator request definition using the percolate
            DSL
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg percolate_index: The index to count percolate the document into.
            Defaults to index.
        :arg percolate_type: The type to count percolate document into. Defaults
            to type.
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random)
        :arg routing: A comma-separated list of specific routing values
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        """
        for param in (index, doc_type):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, id, '_percolate', 'count'), params=params, body=body)

    @query_params('field_statistics', 'fields', 'offsets', 'parent', 'payloads',
        'positions', 'preference', 'realtime', 'routing', 'term_statistics',
        'version', 'version_type')
    def termvectors(self, index, doc_type, id=None, body=None, params=None):
        """
        Returns information and statistics on terms in the fields of a
        particular document. The document could be stored in the index or
        artificially provided by the user (Added in 1.4). Note that for
        documents stored in the index, this is a near realtime API as the term
        vectors are not available until the next refresh.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-termvectors.html>`_

        :arg index: The index in which the document resides.
        :arg doc_type: The type of the document.
        :arg id: The id of the document, when not specified a doc param should
            be supplied.
        :arg body: Define parameters and or supply a document to get termvectors
            for. See documentation.
        :arg field_statistics: Specifies if document count, sum of document
            frequencies and sum of total term frequencies should be returned.,
            default True
        :arg fields: A comma-separated list of fields to return.
        :arg offsets: Specifies if term offsets should be returned., default
            True
        :arg parent: Parent id of documents.
        :arg payloads: Specifies if term payloads should be returned., default
            True
        :arg positions: Specifies if term positions should be returned., default
            True
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random).
        :arg realtime: Specifies if request is real-time as opposed to near-
            real-time (default: true).
        :arg routing: Specific routing value.
        :arg term_statistics: Specifies if total term frequency and document
            frequency should be returned., default False
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        """
        for param in (index, doc_type):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, id, '_termvectors'), params=params, body=body)

    @query_params('field_statistics', 'fields', 'ids', 'offsets', 'parent',
        'payloads', 'positions', 'preference', 'realtime', 'routing',
        'term_statistics', 'version', 'version_type')
    def mtermvectors(self, index=None, doc_type=None, body=None, params=None):
        """
        Multi termvectors API allows to get multiple termvectors based on an
        index, type and id.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/docs-multi-termvectors.html>`_

        :arg index: The index in which the document resides.
        :arg doc_type: The type of the document.
        :arg body: Define ids, documents, parameters or a list of parameters per
            document here. You must at least provide a list of document ids. See
            documentation.
        :arg field_statistics: Specifies if document count, sum of document
            frequencies and sum of total term frequencies should be returned.
            Applies to all returned documents unless otherwise specified in body
            "params" or "docs"., default True
        :arg fields: A comma-separated list of fields to return. Applies to all
            returned documents unless otherwise specified in body "params" or
            "docs".
        :arg ids: A comma-separated list of documents ids. You must define ids
            as parameter or set "ids" or "docs" in the request body
        :arg offsets: Specifies if term offsets should be returned. Applies to
            all returned documents unless otherwise specified in body "params"
            or "docs"., default True
        :arg parent: Parent id of documents. Applies to all returned documents
            unless otherwise specified in body "params" or "docs".
        :arg payloads: Specifies if term payloads should be returned. Applies to
            all returned documents unless otherwise specified in body "params"
            or "docs"., default True
        :arg positions: Specifies if term positions should be returned. Applies
            to all returned documents unless otherwise specified in body
            "params" or "docs"., default True
        :arg preference: Specify the node or shard the operation should be
            performed on (default: random) .Applies to all returned documents
            unless otherwise specified in body "params" or "docs".
        :arg realtime: Specifies if requests are real-time as opposed to near-
            real-time (default: true).
        :arg routing: Specific routing value. Applies to all returned documents
            unless otherwise specified in body "params" or "docs".
        :arg term_statistics: Specifies if total term frequency and document
            frequency should be returned. Applies to all returned documents
            unless otherwise specified in body "params" or "docs"., default
            False
        :arg version: Explicit version number for concurrency control
        :arg version_type: Specific version type, valid choices are: 'internal',
            'external', 'external_gte', 'force'
        """
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_mtermvectors'), params=params, body=body)

    @query_params()
    def put_script(self, lang, id, body, params=None):
        """
        Create a script in given language with specified ID.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-scripting.html>`_

        :arg lang: Script language
        :arg id: Script ID
        :arg body: The document
        """
        for param in (lang, id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_scripts',
            lang, id), params=params, body=body)

    @query_params()
    def get_script(self, lang, id, params=None):
        """
        Retrieve a script from the API.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-scripting.html>`_

        :arg lang: Script language
        :arg id: Script ID
        """
        for param in (lang, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('GET', _make_path('_scripts',
            lang, id), params=params)

    @query_params()
    def delete_script(self, lang, id, params=None):
        """
        Remove a stored script from elasticsearch.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/modules-scripting.html>`_

        :arg lang: Script language
        :arg id: Script ID
        """
        for param in (lang, id):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('DELETE',
            _make_path('_scripts', lang, id), params=params)

    @query_params()
    def put_template(self, id, body, params=None):
        """
        Create a search template.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-template.html>`_

        :arg id: Template ID
        :arg body: The document
        """
        for param in (id, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_search',
            'template', id), params=params, body=body)

    @query_params()
    def get_template(self, id, params=None):
        """
        Retrieve a search template.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-template.html>`_

        :arg id: Template ID
        """
        if id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'id'.")
        return self.transport.perform_request('GET', _make_path('_search',
            'template', id), params=params)

    @query_params()
    def delete_template(self, id, params=None):
        """
        Delete a search template.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-template.html>`_

        :arg id: Template ID
        """
        if id in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'id'.")
        return self.transport.perform_request('DELETE', _make_path('_search',
            'template', id), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'fields',
        'ignore_unavailable', 'level')
    def field_stats(self, index=None, body=None, params=None):
        """
        The field stats api allows one to find statistical properties of a
        field without executing a search, but looking up measurements that are
        natively available in the Lucene index.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-field-stats.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg body: Field json objects containing the name and optionally a range
            to filter out indices result, that have results outside the defined
            bounds
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg fields: A comma-separated list of fields for to get field
            statistics for (min value, max value, and more)
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg level: Defines if field stats should be returned on a per index
            level or on a cluster wide level, default 'cluster', valid choices
            are: 'indices', 'cluster'
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_field_stats'), params=params, body=body)

    @query_params()
    def render_search_template(self, id=None, body=None, params=None):
        """
        `<http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/search-template.html>`_

        :arg id: The id of the stored search template
        :arg body: The search definition template and its params
        """
        return self.transport.perform_request('GET', _make_path('_render',
            'template', id), params=params, body=body)

    @query_params('search_type')
    def msearch_template(self, body, index=None, doc_type=None, params=None):
        """
        The /_search/template endpoint allows to use the mustache language to
        pre render search requests, before they are executed and fill existing
        templates with template parameters.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-template.html>`_

        :arg body: The request definitions (metadata-search request definition
            pairs), separated by newlines
        :arg index: A comma-separated list of index names to use as default
        :arg doc_type: A comma-separated list of document types to use as
            default
        :arg search_type: Search operation type, valid choices are:
            'query_then_fetch', 'query_and_fetch', 'dfs_query_then_fetch',
            'dfs_query_and_fetch'
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('GET', _make_path(index, doc_type,
            '_msearch', 'template'), params=params, body=self._bulk_body(body))

    @query_params('allow_no_indices', 'expand_wildcards', 'fields',
        'ignore_unavailable')
    def field_caps(self, index=None, body=None, params=None):
        """
        The field capabilities API allows to retrieve the capabilities of fields among multiple indices.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-field-caps.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg body: Field json objects containing an array of field names
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg fields: A comma-separated list of field names
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_field_caps'), params=params, body=body)

