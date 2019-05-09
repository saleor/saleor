from .utils import NamespacedClient, query_params, _make_path, SKIP_IN_PATH

class CatClient(NamespacedClient):
    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def aliases(self, name=None, params=None):
        """

        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-alias.html>`_

        :arg name: A comma-separated list of alias names to return
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'aliases', name), params=params)

    @query_params('bytes', 'format', 'h', 'help', 'local', 'master_timeout',
        's', 'v')
    def allocation(self, node_id=None, params=None):
        """
        Allocation provides a snapshot of how shards have located around the
        cluster and the state of disk usage.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-allocation.html>`_

        :arg node_id: A comma-separated list of node IDs or names to limit the
            returned information
        :arg bytes: The unit in which to display byte values, valid choices are:
            'b', 'k', 'kb', 'm', 'mb', 'g', 'gb', 't', 'tb', 'p', 'pb'
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'allocation', node_id), params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def count(self, index=None, params=None):
        """
        Count provides quick access to the document count of the entire cluster,
        or individual indices.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-count.html>`_

        :arg index: A comma-separated list of index names to limit the returned
            information
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat', 'count',
            index), params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'ts',
        'v')
    def health(self, params=None):
        """
        health is a terse, one-line representation of the same information from
        :meth:`~elasticsearch.client.cluster.ClusterClient.health` API
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-health.html>`_

        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg ts: Set to false to disable timestamping, default True
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', '/_cat/health',
            params=params)

    @query_params('help', 's')
    def help(self, params=None):
        """
        A simple help for the cat api.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat.html>`_

        :arg help: Return help information, default False
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        """
        return self.transport.perform_request('GET', '/_cat', params=params)

    @query_params('bytes', 'format', 'h', 'health', 'help', 'local',
        'master_timeout', 'pri', 's', 'v')
    def indices(self, index=None, params=None):
        """
        The indices command provides a cross-section of each index.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-indices.html>`_

        :arg index: A comma-separated list of index names to limit the returned
            information
        :arg bytes: The unit in which to display byte values, valid choices are:
            'b', 'k', 'm', 'g'
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg health: A health status ("green", "yellow", or "red" to filter only
            indices matching the specified health status, default None, valid
            choices are: 'green', 'yellow', 'red'
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg pri: Set to true to return stats only for primary shards, default
            False
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'indices', index), params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def master(self, params=None):
        """
        Displays the master's node ID, bound IP address, and node name.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-master.html>`_

        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', '/_cat/master',
            params=params)

    @query_params('format', 'full_id', 'h', 'help', 'local', 'master_timeout',
        's', 'v')
    def nodes(self, params=None):
        """
        The nodes command shows the cluster topology.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-nodes.html>`_

        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg full_id: Return the full node ID instead of the shortened version
            (default: false)
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', '/_cat/nodes',
            params=params)

    @query_params('bytes', 'format', 'h', 'help', 'master_timeout', 's', 'v')
    def recovery(self, index=None, params=None):
        """
        recovery is a view of shard replication.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-recovery.html>`_

        :arg index: A comma-separated list of index names to limit the returned
            information
        :arg bytes: The unit in which to display byte values, valid choices are:
            'b', 'k', 'kb', 'm', 'mb', 'g', 'gb', 't', 'tb', 'p', 'pb'
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'recovery', index), params=params)

    @query_params('bytes', 'format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def shards(self, index=None, params=None):
        """
        The shards command is the detailed view of what nodes contain which shards.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-shards.html>`_

        :arg index: A comma-separated list of index names to limit the returned
            information
        :arg bytes: The unit in which to display byte values, valid choices are:
            'b', 'k', 'kb', 'm', 'mb', 'g', 'gb', 't', 'tb', 'p', 'pb'
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'shards', index), params=params)

    @query_params('bytes', 'format', 'h', 'help', 's', 'v')
    def segments(self, index=None, params=None):
        """
        The segments command is the detailed view of Lucene segments per index.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-segments.html>`_

        :arg index: A comma-separated list of index names to limit the returned
            information
        :arg bytes: The unit in which to display byte values, valid choices are:
            'b', 'k', 'kb', 'm', 'mb', 'g', 'gb', 't', 'tb', 'p', 'pb'
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'segments', index), params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def pending_tasks(self, params=None):
        """
        pending_tasks provides the same information as the
        :meth:`~elasticsearch.client.cluster.ClusterClient.pending_tasks` API
        in a convenient tabular format.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-pending-tasks.html>`_

        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', '/_cat/pending_tasks',
            params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'size',
        'v')
    def thread_pool(self, thread_pool_patterns=None, params=None):
        """
        Get information about thread pools.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-thread-pool.html>`_

        :arg thread_pool_patterns: A comma-separated list of regular-expressions
            to filter the thread pools in the output
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg size: The multiplier in which to display values, valid choices are:
            '', 'k', 'm', 'g', 't', 'p'
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'thread_pool', thread_pool_patterns), params=params)

    @query_params('bytes', 'format', 'h', 'help', 'local', 'master_timeout',
        's', 'v')
    def fielddata(self, fields=None, params=None):
        """
        Shows information about currently loaded fielddata on a per-node basis.
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-fielddata.html>`_

        :arg fields: A comma-separated list of fields to return the fielddata
            size
        :arg bytes: The unit in which to display byte values, valid choices are:
            'b', 'k', 'kb', 'm', 'mb', 'g', 'gb', 't', 'tb', 'p', 'pb'
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'fielddata', fields), params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def plugins(self, params=None):
        """

        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-plugins.html>`_

        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', '/_cat/plugins',
            params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def nodeattrs(self, params=None):
        """

        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-nodeattrs.html>`_

        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', '/_cat/nodeattrs',
            params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def repositories(self, params=None):
        """

        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-repositories.html>`_

        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node, default False
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', '/_cat/repositories',
            params=params)

    @query_params('format', 'h', 'help', 'ignore_unavailable', 'master_timeout',
        's', 'v')
    def snapshots(self, repository, params=None):
        """

        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-snapshots.html>`_

        :arg repository: Name of repository from which to fetch the snapshot
            information
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg ignore_unavailable: Set to true to ignore unavailable snapshots,
            default False
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        if repository in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'repository'.")
        return self.transport.perform_request('GET', _make_path('_cat',
            'snapshots', repository), params=params)

    @query_params('actions', 'detailed', 'format', 'h', 'help', 'nodes',
        'parent_task_id', 's', 'v')
    def tasks(self, params=None):
        """

        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/tasks.html>`_

        :arg actions: A comma-separated list of actions that should be returned.
            Leave empty to return all.
        :arg detailed: Return detailed task information (default: false)
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg nodes: A comma-separated list of node IDs or names to limit the
            returned information; use `_local` to return information from the
            node you're connecting to, leave empty to get information from all
            nodes
        :arg parent_task_id: Return tasks with specified parent task id. Set to -1
            to return all.
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', '/_cat/tasks',
            params=params)

    @query_params('format', 'h', 'help', 'local', 'master_timeout', 's', 'v')
    def templates(self, name=None, params=None):
        """
        `<https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-templates.html>`_

        :arg name: A pattern that returned template names must match
        :arg format: a short version of the Accept header, e.g. json, yaml
        :arg h: Comma-separated list of column names to display
        :arg help: Return help information, default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        :arg s: Comma-separated list of column names or column aliases to sort
            by
        :arg v: Verbose mode. Display column headers, default False
        """
        return self.transport.perform_request('GET', _make_path('_cat',
            'templates', name), params=params)

