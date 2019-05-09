from .connections import connections
from .search import Search
from .exceptions import IllegalOperation

class IndexBody(object):
    def __init__(self, name, using='default'):
        """
        :arg name: name of the index
        :arg using: connection alias to use, defaults to ``'default'``
        """
        self._name = name
        self._doc_types = {}
        self._mappings = {}
        self._using = using
        self._settings = {}
        self._aliases = {}
        self._analysis = {}

    def clone(self, name, using=None):
        """
        Create a copy of the instance with another name or connection alias.
        Useful for creating multiple indices with shared configuration::

            i = Index('base-index')
            i.settings(number_of_shards=1)
            i.create()

            i2 = i.clone('other-index')
            i2.create()

        :arg name: name of the index
        :arg using: connection alias to use, defaults to ``'default'``
        """
        i = Index(name, using=using or self._using)
        for attr in ('_doc_types', '_mappings', '_settings', '_aliases',
                     '_analysis'):
            setattr(i, attr, getattr(self, attr).copy())
        return i

    def _get_connection(self):
        return connections.get_connection(self._using)
    connection = property(_get_connection)

    def mapping(self, mapping):
        """
        Associate a mapping (an instance of
        :class:`~elasticsearch_dsl.Mapping`) with this index.
        This means that, when this index is created, it will contain the
        mappings for the document type defined by those mappings.
        """
        self._mappings[mapping.doc_type] = mapping

    def doc_type(self, doc_type):
        """
        Associate a :class:`~elasticsearch_dsl.DocType` subclass with an index.
        This means that, when this index is created, it will contain the
        mappings for the ``DocType``. If the ``DocType`` class doesn't have a
        default index yet, name of the ``Index`` instance will be used. Can be
        used as a decorator::

            i = Index('blog')

            @i.doc_type
            class Post(DocType):
                title = Text()

            # create the index, including Post mappings
            i.create()

            # .search() will now return a Search object that will return
            # properly deserialized Post instances
            s = i.search()
        """
        name = doc_type._doc_type.name
        self._doc_types[name] = doc_type
        self._mappings[name] = doc_type._doc_type.mapping

        if not doc_type._doc_type.index:
            doc_type._doc_type.index = self._name
        return doc_type  # to use as decorator???

    def settings(self, **kwargs):
        """
        Add settings to the index::

            i = Index('i')
            i.settings(number_of_shards=1, number_of_replicas=0)

        Multiple calls to ``settings`` will merge the keys, later overriding
        the earlier.
        """
        self._settings.update(kwargs)
        return self

    def aliases(self, **kwargs):
        """
        Add aliases to the index definition::

            i = Index('blog-v2')
            i.aliases(blog={}, published={'filter': Q('term', published=True)})
        """
        self._aliases.update(kwargs)
        return self

    def analyzer(self, analyzer):
        """
        Explicitly add an analyzer to an index. Note that all custom analyzers
        defined in mappings will also be created. This is useful for search analyzers.

        Example::

            from elasticsearch_dsl import analyzer, tokenizer

            my_analyzer = analyzer('my_analyzer',
                tokenizer=tokenizer('trigram', 'nGram', min_gram=3, max_gram=3),
                filter=['lowercase']
            )

            i = Index('blog')
            i.analyzer(my_analyzer)

        """
        d = analyzer.get_analysis_definition()
        # empty custom analyzer, probably already defined out of our control
        if not d:
            return

        # merge the definition
        # TODO: conflict detection/resolution
        for key in d:
            self._analysis.setdefault(key, {}).update(d[key])

    def _get_mappings(self):
        analysis, mappings = {}, {}
        for mapping in self._mappings.values():
            mappings.update(mapping.to_dict())
            a = mapping._collect_analysis()
            # merge the definition
            # TODO: conflict detection/resolution
            for key in a:
                analysis.setdefault(key, {}).update(a[key])

        return mappings, analysis

    def to_dict(self):
        out = {}
        if self._settings:
            out['settings'] = self._settings
        if self._aliases:
            out['aliases'] = self._aliases
        mappings, analysis = self._get_mappings()
        if mappings:
            out['mappings'] = mappings
        if analysis or self._analysis:
            for key in self._analysis:
                analysis.setdefault(key, {}).update(self._analysis[key])
            out.setdefault('settings', {})['analysis'] = analysis
        return out

class IndexTemplate(IndexBody):
    def __init__(self, name, template, **kwargs):
        super(IndexTemplate, self).__init__(name, **kwargs)
        self._template = template

    def to_dict(self):
        d = super(IndexTemplate, self).to_dict()
        d['template'] = self._template
        return d

    def save(self):
        self.connection.indices.put_template(name=self._name, body=self.to_dict())

    def search(self):
        """
        Return a :class:`~elasticsearch_dsl.Search` object searching over all
        the indices belonging to this template and its ``DocType``\s.
        """
        return Search(
            using=self._using,
            index=self._template,
            doc_type=[self._doc_types.get(k, k) for k in self._mappings]
        )

class Index(IndexBody):
    def search(self):
        """
        Return a :class:`~elasticsearch_dsl.Search` object searching over this
        index and its ``DocType``\s.
        """
        return Search(
            using=self._using,
            index=self._name,
            doc_type=[self._doc_types.get(k, k) for k in self._mappings]
        )

    def create(self, **kwargs):
        """
        Creates the index in elasticsearch.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.create`` unchanged.
        """
        self.connection.indices.create(index=self._name, body=self.to_dict(), **kwargs)

    def is_closed(self):
        state = self.connection.cluster.state(index=self._name, metric='metadata')
        return state['metadata']['indices'][self._name]['state'] == 'close'

    def save(self):
        """
        Sync the index definition with elasticsearch, creating the index if it
        doesn't exist and updating its settings and mappings if it does.

        Note some settings and mapping changes cannot be done on an open
        index (or at all on an existing index) and for those this method will
        fail with the underlying exception.
        """
        if not self.exists():
            return self.create()

        body = self.to_dict()
        settings = body.pop('settings', {})
        analysis = settings.pop('analysis', None)
        if analysis:
            if self.is_closed():
                # closed index, update away
                settings['analysis'] = analysis
            else:
                # compare analysis definition, if all analysis objects are
                # already defined as requested, skip analysis update and
                # proceed, otherwise raise IllegalOperation
                existing_analysis = self.get_settings()[self._name]['settings']['index'].get('analysis', {})
                if any(
                    existing_analysis.get(section, {}).get(k, None) != analysis[section][k]
                    for section in analysis
                    for k in analysis[section]
                ):
                    raise IllegalOperation(
                        'You cannot update analysis configuration on an open index, you need to close index %s first.' % self._name)

        # try and update the settings
        if settings:
            self.put_settings(body=settings)

        # update the mappings, any conflict in the mappings will result in an
        # exception
        mappings = body.pop('mappings', {})
        if mappings:
            for doc_type in mappings:
                self.put_mapping(doc_type=doc_type, body=mappings[doc_type])

    def analyze(self, **kwargs):
        """
        Perform the analysis process on a text and return the tokens breakdown
        of the text.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.analyze`` unchanged.
        """
        return self.connection.indices.analyze(index=self._name, **kwargs)

    def refresh(self, **kwargs):
        """
        Preforms a refresh operation on the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.refresh`` unchanged.
        """
        return self.connection.indices.refresh(index=self._name, **kwargs)

    def flush(self, **kwargs):
        """
        Preforms a flush operation on the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.flush`` unchanged.
        """
        return self.connection.indices.flush(index=self._name, **kwargs)

    def get(self, **kwargs):
        """
        The get index API allows to retrieve information about the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.get`` unchanged.
        """
        return self.connection.indices.get(index=self._name, **kwargs)

    def open(self, **kwargs):
        """
        Opens the index in elasticsearch.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.open`` unchanged.
        """
        return self.connection.indices.open(index=self._name, **kwargs)

    def close(self, **kwargs):
        """
        Closes the index in elasticsearch.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.close`` unchanged.
        """
        return self.connection.indices.close(index=self._name, **kwargs)

    def delete(self, **kwargs):
        """
        Deletes the index in elasticsearch.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.delete`` unchanged.
        """
        return self.connection.indices.delete(index=self._name, **kwargs)

    def exists(self, **kwargs):
        """
        Returns ``True`` if the index already exists in elasticsearch.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.exists`` unchanged.
        """
        return self.connection.indices.exists(index=self._name, **kwargs)

    def exists_type(self, **kwargs):
        """
        Check if a type/types exists in the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.exists_type`` unchanged.
        """
        return self.connection.indices.exists_type(index=self._name, **kwargs)

    def put_mapping(self, **kwargs):
        """
        Register specific mapping definition for a specific type.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.put_mapping`` unchanged.
        """
        return self.connection.indices.put_mapping(index=self._name, **kwargs)

    def get_mapping(self, **kwargs):
        """
        Retrieve specific mapping definition for a specific type.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.get_mapping`` unchanged.
        """
        return self.connection.indices.get_mapping(index=self._name, **kwargs)

    def get_field_mapping(self, **kwargs):
        """
        Retrieve mapping definition of a specific field.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.get_field_mapping`` unchanged.
        """
        return self.connection.indices.get_field_mapping(index=self._name, **kwargs)

    def put_alias(self, **kwargs):
        """
        Create an alias for the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.put_alias`` unchanged.
        """
        return self.connection.indices.put_alias(index=self._name, **kwargs)

    def exists_alias(self, **kwargs):
        """
        Return a boolean indicating whether given alias exists for this index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.exists_alias`` unchanged.
        """
        return self.connection.indices.exists_alias(index=self._name, **kwargs)

    def get_alias(self, **kwargs):
        """
        Retrieve a specified alias.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.get_alias`` unchanged.
        """
        return self.connection.indices.get_alias(index=self._name, **kwargs)

    def delete_alias(self, **kwargs):
        """
        Delete specific alias.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.delete_alias`` unchanged.
        """
        return self.connection.indices.delete_alias(index=self._name, **kwargs)

    def get_settings(self, **kwargs):
        """
        Retrieve settings for the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.get_settings`` unchanged.
        """
        return self.connection.indices.get_settings(index=self._name, **kwargs)

    def put_settings(self, **kwargs):
        """
        Change specific index level settings in real time.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.put_settings`` unchanged.
        """
        return self.connection.indices.put_settings(index=self._name, **kwargs)

    def stats(self, **kwargs):
        """
        Retrieve statistics on different operations happening on the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.stats`` unchanged.
        """
        return self.connection.indices.stats(index=self._name, **kwargs)

    def segments(self, **kwargs):
        """
        Provide low level segments information that a Lucene index (shard
        level) is built with.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.segments`` unchanged.
        """
        return self.connection.indices.segments(index=self._name, **kwargs)

    def validate_query(self, **kwargs):
        """
        Validate a potentially expensive query without executing it.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.validate_query`` unchanged.
        """
        return self.connection.indices.validate_query(index=self._name, **kwargs)

    def clear_cache(self, **kwargs):
        """
        Clear all caches or specific cached associated with the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.clear_cache`` unchanged.
        """
        return self.connection.indices.clear_cache(index=self._name, **kwargs)

    def recovery(self, **kwargs):
        """
        The indices recovery API provides insight into on-going shard
        recoveries for the index.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.recovery`` unchanged.
        """
        return self.connection.indices.recovery(index=self._name, **kwargs)

    def upgrade(self, **kwargs):
        """
        Upgrade the index to the latest format.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.upgrade`` unchanged.
        """
        return self.connection.indices.upgrade(index=self._name, **kwargs)

    def get_upgrade(self, **kwargs):
        """
        Monitor how much of the index is upgraded.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.get_upgrade`` unchanged.
        """
        return self.connection.indices.get_upgrade(index=self._name, **kwargs)

    def flush_synced(self, **kwargs):
        """
        Perform a normal flush, then add a generated unique marker (sync_id) to
        all shards.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.flush_synced`` unchanged.
        """
        return self.connection.indices.flush_synced(index=self._name, **kwargs)

    def shard_stores(self, **kwargs):
        """
        Provides store information for shard copies of the index. Store
        information reports on which nodes shard copies exist, the shard copy
        version, indicating how recent they are, and any exceptions encountered
        while opening the shard index or from earlier engine failure.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.shard_stores`` unchanged.
        """
        return self.connection.indices.shard_stores(index=self._name, **kwargs)

    def forcemerge(self, **kwargs):
        """
        The force merge API allows to force merging of the index through an
        API. The merge relates to the number of segments a Lucene index holds
        within each shard. The force merge operation allows to reduce the
        number of segments by merging them.

        This call will block until the merge is complete. If the http
        connection is lost, the request will continue in the background, and
        any new requests will block until the previous force merge is complete.

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.forcemerge`` unchanged.
        """
        return self.connection.indices.forcemerge(index=self._name, **kwargs)

    def shrink(self, **kwargs):
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

        Any additional keyword arguments will be passed to
        ``Elasticsearch.indices.shrink`` unchanged.
        """
        return self.connection.indices.shrink(index=self._name, **kwargs)
