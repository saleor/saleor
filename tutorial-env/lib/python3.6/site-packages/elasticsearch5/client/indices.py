from .utils import NamespacedClient, query_params, _make_path, SKIP_IN_PATH

class IndicesClient(NamespacedClient):
    @query_params('analyzer', 'attributes', 'char_filter', 'explain', 'field',
        'filter', 'format', 'prefer_local', 'text', 'tokenizer')
    def analyze(self, index=None, body=None, params=None):
        """
        Perform the analysis process on a text and return the tokens breakdown of the text.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-analyze.html>`_

        :arg index: The name of the index to scope the operation
        :arg body: The text on which the analysis should be performed
        :arg analyzer: The name of the analyzer to use
        :arg attributes: A comma-separated list of token attributes to output,
            this parameter works only with `explain=true`
        :arg char_filter: A comma-separated list of character filters to use for
            the analysis
        :arg explain: With `true`, outputs more advanced details. (default:
            false)
        :arg field: Use the analyzer configured for this field (instead of
            passing the analyzer name)
        :arg filter: A comma-separated list of filters to use for the analysis
        :arg format: Format of the output, default 'detailed', valid choices
            are: 'detailed', 'text'
        :arg prefer_local: With `true`, specify that a local shard should be
            used if available, with `false`, use a random shard (default: true)
        :arg text: The text on which the analysis should be performed (when
            request body is not used)
        :arg tokenizer: The name of the tokenizer to use for the analysis
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_analyze'), params=params, body=body)

    @query_params('allow_no_indices', 'expand_wildcards', 'force',
        'ignore_unavailable', 'operation_threading')
    def refresh(self, index=None, params=None):
        """
        Explicitly refresh one or more index, making all operations performed
        since the last refresh available for search.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-refresh.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg force: Force a refresh even if not required, default False
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg operation_threading: TODO: ?
        """
        return self.transport.perform_request('POST', _make_path(index,
            '_refresh'), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'force',
        'ignore_unavailable', 'wait_if_ongoing')
    def flush(self, index=None, params=None):
        """
        Explicitly flush one or more indices.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-flush.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string for all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg force: Whether a flush should be forced even if it is not
            necessarily needed ie. if no changes will be committed to the index.
            This is useful if transaction log IDs should be incremented even if
            no uncommitted changes are present. (This setting can be considered
            as internal)
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg wait_if_ongoing: If set to true the flush operation will block
            until the flush can be executed if another flush operation is
            already executing. The default is true. If set to false the flush
            will be skipped iff if another flush operation is already running.
        """
        return self.transport.perform_request('POST', _make_path(index,
            '_flush'), params=params)

    @query_params('master_timeout', 'timeout', 'update_all_types',
        'wait_for_active_shards')
    def create(self, index, body=None, params=None):
        """
        Create an index in Elasticsearch.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-create-index.html>`_

        :arg index: The name of the index
        :arg body: The configuration for the index (`settings` and `mappings`)
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit operation timeout
        :arg update_all_types: Whether to update the mapping for all fields with
            the same name across all types or not
        :arg wait_for_active_shards: Set the number of active shards to wait for
            before the operation returns.
        """
        if index in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'index'.")
        return self.transport.perform_request('PUT', _make_path(index),
            params=params, body=body)

    @query_params('allow_no_indices', 'expand_wildcards', 'flat_settings',
        'human', 'ignore_unavailable', 'include_defaults', 'local')
    def get(self, index, feature=None, params=None):
        """
        The get index API allows to retrieve information about one or more indexes.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-get-index.html>`_

        :arg index: A comma-separated list of index names
        :arg feature: A comma-separated list of features
        :arg allow_no_indices: Ignore if a wildcard expression resolves to no
            concrete indices (default: false)
        :arg expand_wildcards: Whether wildcard expressions should get expanded
            to open or closed indices (default: open), default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg flat_settings: Return settings in flat format (default: false)
        :arg human: Whether to return version and creation date values in human-
            readable format., default False
        :arg ignore_unavailable: Ignore unavailable indexes (default: false)
        :arg include_defaults: Whether to return all default setting for each of
            the indices., default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        """
        if index in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'index'.")
        return self.transport.perform_request('GET', _make_path(index,
            feature), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'master_timeout', 'timeout')
    def open(self, index, params=None):
        """
        Open a closed index to make it available for search.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-open-close.html>`_

        :arg index: The name of the index
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'closed', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit operation timeout
        """
        if index in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'index'.")
        return self.transport.perform_request('POST', _make_path(index,
            '_open'), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'master_timeout', 'timeout')
    def close(self, index, params=None):
        """
        Close an index to remove it's overhead from the cluster. Closed index
        is blocked for read/write operations.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-open-close.html>`_

        :arg index: The name of the index
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit operation timeout
        """
        if index in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'index'.")
        return self.transport.perform_request('POST', _make_path(index,
            '_close'), params=params)

    @query_params('master_timeout', 'timeout')
    def delete(self, index, params=None):
        """
        Delete an index in Elasticsearch
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-delete-index.html>`_

        :arg index: A comma-separated list of indices to delete; use `_all` or
            `*` string to delete all indices
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit operation timeout
        """
        if index in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'index'.")
        return self.transport.perform_request('DELETE', _make_path(index),
            params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'local')
    def exists(self, index, params=None):
        """
        Return a boolean indicating whether given index exists.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-exists.html>`_

        :arg index: A comma-separated list of indices to check
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
        """
        if index in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'index'.")
        return self.transport.perform_request('HEAD', _make_path(index),
                params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'local')
    def exists_type(self, index, doc_type, params=None):
        """
        Check if a type/types exists in an index/indices.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-types-exists.html>`_

        :arg index: A comma-separated list of index names; use `_all` to check
            the types across all indices
        :arg doc_type: A comma-separated list of document types to check
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
        """
        for param in (index, doc_type):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('HEAD', _make_path(index,
            '_mapping', doc_type), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'master_timeout', 'timeout', 'update_all_types')
    def put_mapping(self, doc_type, body, index=None, params=None):
        """
        Register specific mapping definition for a specific type.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-put-mapping.html>`_

        :arg doc_type: The name of the document type
        :arg body: The mapping definition
        :arg index: A comma-separated list of index names the mapping should be
            added to (supports wildcards); use `_all` or omit to add the mapping
            on all indices.
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit operation timeout
        :arg update_all_types: Whether to update the mapping for all fields with
            the same name across all types or not
        """
        for param in (doc_type, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path(index,
            '_mapping', doc_type), params=params, body=body)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'local')
    def get_mapping(self, index=None, doc_type=None, params=None):
        """
        Retrieve mapping definition of index or index/type.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-get-mapping.html>`_

        :arg index: A comma-separated list of index names
        :arg doc_type: A comma-separated list of document types
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
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_mapping', doc_type), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'include_defaults', 'local')
    def get_field_mapping(self, fields, index=None, doc_type=None, params=None):
        """
        Retrieve mapping definition of a specific field.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-get-field-mapping.html>`_

        :arg fields: A comma-separated list of fields
        :arg index: A comma-separated list of index names
        :arg doc_type: A comma-separated list of document types
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg include_defaults: Whether the default mapping values should be
            returned as well
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        """
        if fields in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'fields'.")
        return self.transport.perform_request('GET', _make_path(index,
            '_mapping', doc_type, 'field', fields), params=params)

    @query_params('master_timeout', 'timeout')
    def put_alias(self, index, name, body=None, params=None):
        """
        Create an alias for a specific index/indices.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html>`_

        :arg index: A comma-separated list of index names the alias should point
            to (supports wildcards); use `_all` to perform the operation on all
            indices.
        :arg name: The name of the alias to be created or updated
        :arg body: The settings for the alias, such as `routing` or `filter`
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit timeout for the operation
        """
        for param in (index, name):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path(index,
            '_alias', name), params=params, body=body)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'local')
    def exists_alias(self, index=None, name=None, params=None):
        """
        Return a boolean indicating whether given alias exists.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html>`_

        :arg index: A comma-separated list of index names to filter aliases
        :arg name: A comma-separated list of alias names to return
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default ['open', 'closed'],
            valid choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        """
        return self.transport.perform_request('HEAD', _make_path(index, '_alias',
                name), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'local')
    def get_alias(self, index=None, name=None, params=None):
        """
        Retrieve a specified alias.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html>`_

        :arg index: A comma-separated list of index names to filter aliases
        :arg name: A comma-separated list of alias names to return
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'all', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_alias', name), params=params)

    @query_params('master_timeout', 'timeout')
    def update_aliases(self, body, params=None):
        """
        Update specified aliases.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html>`_

        :arg body: The definition of `actions` to perform
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Request timeout
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('POST', '/_aliases',
            params=params, body=body)

    @query_params('master_timeout', 'timeout')
    def delete_alias(self, index, name, params=None):
        """
        Delete specific alias.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-aliases.html>`_

        :arg index: A comma-separated list of index names (supports wildcards);
            use `_all` for all indices
        :arg name: A comma-separated list of aliases to delete (supports
            wildcards); use `_all` to delete all aliases for the specified
            indices.
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit timeout for the operation
        """
        for param in (index, name):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('DELETE', _make_path(index,
            '_alias', name), params=params)

    @query_params('create', 'flat_settings', 'master_timeout', 'order',
        'timeout')
    def put_template(self, name, body, params=None):
        """
        Create an index template that will automatically be applied to new
        indices created.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-templates.html>`_

        :arg name: The name of the template
        :arg body: The template definition
        :arg create: Whether the index template should only be added if new or
            can also replace an existing one, default False
        :arg flat_settings: Return settings in flat format (default: false)
        :arg master_timeout: Specify timeout for connection to master
        :arg order: The order for this template when merging multiple matching
            ones (higher numbers are merged later, overriding the lower numbers)
        :arg timeout: Explicit operation timeout
        """
        for param in (name, body):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path('_template',
            name), params=params, body=body)

    @query_params('local', 'master_timeout')
    def exists_template(self, name, params=None):
        """
        Return a boolean indicating whether given template exists.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-templates.html>`_

        :arg name: The name of the template
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        """
        if name in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'name'.")
        return self.transport.perform_request('HEAD', _make_path('_template',
                name), params=params)

    @query_params('flat_settings', 'local', 'master_timeout')
    def get_template(self, name=None, params=None):
        """
        Retrieve an index template by its name.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-templates.html>`_

        :arg name: The name of the template
        :arg flat_settings: Return settings in flat format (default: false)
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        :arg master_timeout: Explicit operation timeout for connection to master
            node
        """
        return self.transport.perform_request('GET', _make_path('_template',
            name), params=params)

    @query_params('master_timeout', 'timeout')
    def delete_template(self, name, params=None):
        """
        Delete an index template by its name.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-templates.html>`_

        :arg name: The name of the template
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit operation timeout
        """
        if name in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'name'.")
        return self.transport.perform_request('DELETE',
            _make_path('_template', name), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'flat_settings',
        'human', 'ignore_unavailable', 'include_defaults', 'local')
    def get_settings(self, index=None, name=None, params=None):
        """
        Retrieve settings for one or more (or all) indices.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-get-settings.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg name: The name of the settings that should be included
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default ['open', 'closed'],
            valid choices are: 'open', 'closed', 'none', 'all'
        :arg flat_settings: Return settings in flat format (default: false)
        :arg human: Whether to return version and creation date values in human-
            readable format., default False
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg include_defaults: Whether to return all default setting for each of
            the indices., default False
        :arg local: Return local information, do not retrieve the state from
            master node (default: false)
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_settings', name), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'flat_settings',
        'ignore_unavailable', 'master_timeout', 'preserve_existing')
    def put_settings(self, body, index=None, params=None):
        """
        Change specific index level settings in real time.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-update-settings.html>`_

        :arg body: The index settings to be updated
        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg flat_settings: Return settings in flat format (default: false)
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg master_timeout: Specify timeout for connection to master
        :arg preserve_existing: Whether to update existing settings. If set to
            `true` existing settings on an index remain unchanged, the default
            is `false`
        """
        if body in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'body'.")
        return self.transport.perform_request('PUT', _make_path(index,
            '_settings'), params=params, body=body)

    @query_params('completion_fields', 'fielddata_fields', 'fields', 'groups',
        'include_segment_file_sizes', 'level', 'types')
    def stats(self, index=None, metric=None, params=None):
        """
        Retrieve statistics on different operations happening on an index.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-stats.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg metric: Limit the information returned the specific metrics.
        :arg completion_fields: A comma-separated list of fields for `fielddata`
            and `suggest` index metric (supports wildcards)
        :arg fielddata_fields: A comma-separated list of fields for `fielddata`
            index metric (supports wildcards)
        :arg fields: A comma-separated list of fields for `fielddata` and
            `completion` index metric (supports wildcards)
        :arg groups: A comma-separated list of search groups for `search` index
            metric
        :arg include_segment_file_sizes: Whether to report the aggregated disk
            usage of each one of the Lucene index files (only applies if segment
            stats are requested), default False
        :arg level: Return stats aggregated at cluster, index or shard level,
            default 'indices', valid choices are: 'cluster', 'indices', 'shards'
        :arg types: A comma-separated list of document types for the `indexing`
            index metric
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_stats', metric), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'operation_threading', 'verbose')
    def segments(self, index=None, params=None):
        """
        Provide low level segments information that a Lucene index (shard level) is built with.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-segments.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg operation_threading: TODO: ?
        :arg verbose: Includes detailed memory usage by Lucene., default False
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_segments'), params=params)

    @query_params('allow_no_indices', 'analyze_wildcard', 'analyzer',
        'default_operator', 'df', 'expand_wildcards', 'explain',
        'ignore_unavailable', 'lenient', 'lowercase_expanded_terms',
        'operation_threading', 'q', 'rewrite')
    def validate_query(self, index=None, doc_type=None, body=None, params=None):
        """
        Validate a potentially expensive query without executing it.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/search-validate.html>`_

        :arg index: A comma-separated list of index names to restrict the
            operation; use `_all` or empty string to perform the operation on
            all indices
        :arg doc_type: A comma-separated list of document types to restrict the
            operation; leave empty to perform the operation on all types
        :arg body: The query definition specified with the Query DSL
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
        :arg explain: Return detailed information about the error
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg lenient: Specify whether format-based query failures (such as
            providing text to a numeric field) should be ignored
        :arg lowercase_expanded_terms: Specify whether query terms should be
            lowercased
        :arg operation_threading: TODO: ?
        :arg q: Query in the Lucene query string syntax
        :arg rewrite: Provide a more detailed explanation showing the actual
            Lucene query that will be executed.
        """
        return self.transport.perform_request('GET', _make_path(index,
            doc_type, '_validate', 'query'), params=params, body=body)

    @query_params('allow_no_indices', 'expand_wildcards', 'field_data',
        'fielddata', 'fields', 'ignore_unavailable', 'query', 'recycler',
        'request')
    def clear_cache(self, index=None, params=None):
        """
        Clear either all caches or specific cached associated with one ore more indices.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-clearcache.html>`_

        :arg index: A comma-separated list of index name to limit the operation
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg field_data: Clear field data
        :arg fielddata: Clear field data
        :arg fields: A comma-separated list of fields to clear when using the
            `field_data` parameter (default: all)
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg query: Clear query caches
        :arg recycler: Clear the recycler cache
        :arg request: Clear request cache
        """
        return self.transport.perform_request('POST', _make_path(index,
            '_cache', 'clear'), params=params)

    @query_params('active_only', 'detailed')
    def recovery(self, index=None, params=None):
        """
        The indices recovery API provides insight into on-going shard
        recoveries. Recovery status may be reported for specific indices, or
        cluster-wide.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-recovery.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg active_only: Display only those recoveries that are currently on-
            going, default False
        :arg detailed: Whether to display detailed information about shard
            recovery, default False
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_recovery'), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'only_ancient_segments', 'wait_for_completion')
    def upgrade(self, index=None, params=None):
        """
        Upgrade one or more indices to the latest format through an API.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-upgrade.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg only_ancient_segments: If true, only ancient (an older Lucene major
            release) segments will be upgraded
        :arg wait_for_completion: Specify whether the request should block until
            the all segments are upgraded (default: false)
        """
        return self.transport.perform_request('POST', _make_path(index,
            '_upgrade'), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable')
    def get_upgrade(self, index=None, params=None):
        """
        Monitor how much of one or more index is upgraded.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-upgrade.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_upgrade'), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable')
    def flush_synced(self, index=None, params=None):
        """
        Perform a normal flush, then add a generated unique marker (sync_id) to all shards.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-synced-flush.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string for all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        """
        return self.transport.perform_request('POST', _make_path(index,
            '_flush', 'synced'), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'ignore_unavailable',
        'operation_threading', 'status')
    def shard_stores(self, index=None, params=None):
        """
        Provides store information for shard copies of indices. Store
        information reports on which nodes shard copies exist, the shard copy
        version, indicating how recent they are, and any exceptions encountered
        while opening the shard index or from earlier engine failure.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-shards-stores.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg operation_threading: TODO: ?
        :arg status: A comma-separated list of statuses used to filter on shards
            to get store information for, valid choices are: 'green', 'yellow',
            'red', 'all'
        """
        return self.transport.perform_request('GET', _make_path(index,
            '_shard_stores'), params=params)

    @query_params('allow_no_indices', 'expand_wildcards', 'flush',
        'ignore_unavailable', 'max_num_segments', 'only_expunge_deletes',
        'operation_threading', 'wait_for_merge')
    def forcemerge(self, index=None, params=None):
        """
        The force merge API allows to force merging of one or more indices
        through an API. The merge relates to the number of segments a Lucene
        index holds within each shard. The force merge operation allows to
        reduce the number of segments by merging them.

        This call will block until the merge is complete. If the http
        connection is lost, the request will continue in the background, and
        any new requests will block until the previous force merge is complete.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-forcemerge.html>`_

        :arg index: A comma-separated list of index names; use `_all` or empty
            string to perform the operation on all indices
        :arg allow_no_indices: Whether to ignore if a wildcard indices
            expression resolves into no concrete indices. (This includes `_all`
            string or when no indices have been specified)
        :arg expand_wildcards: Whether to expand wildcard expression to concrete
            indices that are open, closed or both., default 'open', valid
            choices are: 'open', 'closed', 'none', 'all'
        :arg flush: Specify whether the index should be flushed after performing
            the operation (default: true)
        :arg ignore_unavailable: Whether specified concrete indices should be
            ignored when unavailable (missing or closed)
        :arg max_num_segments: The number of segments the index should be merged
            into (default: dynamic)
        :arg only_expunge_deletes: Specify whether the operation should only
            expunge deleted documents
        :arg operation_threading: TODO: ?
        :arg wait_for_merge: Specify whether the request should block until the
            merge process is finished (default: true)
        """
        return self.transport.perform_request('POST', _make_path(index,
            '_forcemerge'), params=params)

    @query_params('master_timeout', 'timeout', 'wait_for_active_shards')
    def shrink(self, index, target, body=None, params=None):
        """
        The shrink index API allows you to shrink an existing index into a new
        index with fewer primary shards. The number of primary shards in the
        target index must be a factor of the shards in the source index. For
        example an index with 8 primary shards can be shrunk into 4, 2 or 1
        primary shards or an index with 15 primary shards can be shrunk into 5,
        3 or 1. If the number of shards in the index is a prime number it can
        only be shrunk into a single primary shard. Before shrinking, a
        (primary or replica) copy of every shard in the index must be present
        on the same node.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-shrink-index.html>`_

        :arg index: The name of the source index to shrink
        :arg target: The name of the target index to shrink into
        :arg body: The configuration for the target index (`settings` and
            `aliases`)
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit operation timeout
        :arg wait_for_active_shards: Set the number of active shards to wait for
            on the shrunken index before the operation returns.
        """
        for param in (index, target):
            if param in SKIP_IN_PATH:
                raise ValueError("Empty value passed for a required argument.")
        return self.transport.perform_request('PUT', _make_path(index,
            '_shrink', target), params=params, body=body)

    @query_params('dry_run', 'master_timeout', 'timeout',
        'wait_for_active_shards')
    def rollover(self, alias, new_index=None, body=None, params=None):
        """
        The rollover index API rolls an alias over to a new index when the
        existing index is considered to be too large or too old.

        The API accepts a single alias name and a list of conditions. The alias
        must point to a single index only. If the index satisfies the specified
        conditions then a new index is created and the alias is switched to
        point to the new alias.
        `<http://www.elastic.co/guide/en/elasticsearch/reference/current/indices-rollover-index.html>`_

        :arg alias: The name of the alias to rollover
        :arg new_index: The name of the rollover index
        :arg body: The conditions that needs to be met for executing rollover
        :arg dry_run: If set to true the rollover action will only be validated
            but not actually performed even if a condition matches. The default
            is false
        :arg master_timeout: Specify timeout for connection to master
        :arg timeout: Explicit operation timeout
        :arg wait_for_active_shards: Set the number of active shards to wait for
            on the newly created rollover index before the operation returns.
        """
        if alias in SKIP_IN_PATH:
            raise ValueError("Empty value passed for a required argument 'alias'.")
        return self.transport.perform_request('POST', _make_path(alias,
            '_rollover', new_index), params=params, body=body)
