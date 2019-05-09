import collections
from fnmatch import fnmatch

from elasticsearch.exceptions import NotFoundError, RequestError
from six import iteritems, add_metaclass

from .field import Field
from .mapping import Mapping
from .utils import ObjectBase, AttrDict, merge, DOC_META_FIELDS, META_FIELDS
from .response import HitMeta
from .search import Search
from .connections import connections
from .exceptions import ValidationException, IllegalOperation


class MetaField(object):
    def __init__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs


class DocTypeMeta(type):
    def __new__(cls, name, bases, attrs):
        # DocTypeMeta filters attrs in place
        attrs['_doc_type'] = DocTypeOptions(name, bases, attrs)
        return super(DocTypeMeta, cls).__new__(cls, name, bases, attrs)


class DocTypeOptions(object):
    def __init__(self, name, bases, attrs):
        meta = attrs.pop('Meta', None)

        # default index, if not overriden by doc.meta
        self.index = getattr(meta, 'index', None)

        # default cluster alias, can be overriden in doc.meta
        self._using = getattr(meta, 'using', None)

        # get doc_type name, if not defined use 'doc'
        doc_type = getattr(meta, 'doc_type', 'doc')

        # create the mapping instance
        self.mapping = getattr(meta, 'mapping', Mapping(doc_type))

        # register all declared fields into the mapping
        for name, value in list(iteritems(attrs)):
            if isinstance(value, Field):
                self.mapping.field(name, value)
                del attrs[name]

        # add all the mappings for meta fields
        for name in dir(meta):
            if isinstance(getattr(meta, name, None), MetaField):
                params = getattr(meta, name)
                self.mapping.meta(name, *params.args, **params.kwargs)

        # document inheritance - include the fields from parents' mappings and
        # index/using values
        for b in bases:
            if hasattr(b, '_doc_type') and hasattr(b._doc_type, 'mapping'):
                self.mapping.update(b._doc_type.mapping, update_only=True)
                self._using = self._using or b._doc_type._using
                self.index = self.index or b._doc_type.index

        # custom method to determine if a hit belongs to this DocType
        self._matches = getattr(meta, 'matches', None)

    @property
    def using(self):
        return self._using or 'default'

    @property
    def name(self):
        return self.mapping.properties.name

    @property
    def parent(self):
        if '_parent' in self.mapping._meta:
            return self.mapping._meta['_parent']['type']
        return

    def resolve_field(self, field_path):
        return self.mapping.resolve_field(field_path)

    def init(self, index=None, using=None):
        self.mapping.save(index or self.index, using=using or self.using)

    def refresh(self, index=None, using=None):
        self.mapping.update_from_es(index or self.index, using=using or self.using)

    def matches(self, hit):
        if self._matches is not None:
            return self._matches(hit)

        return (
                self.index is None or fnmatch(hit.get('_index', ''), self.index)
            ) and self.name == hit.get('_type')

@add_metaclass(DocTypeMeta)
class InnerDoc(ObjectBase):
    """
    Common class for inner documents like Object or Nested
    """


@add_metaclass(DocTypeMeta)
class DocType(ObjectBase):
    """
    Model-like class for persisting documents in elasticsearch.
    """
    def __init__(self, meta=None, **kwargs):
        meta = meta or {}
        for k in list(kwargs):
            if k.startswith('_') and k[1:] in META_FIELDS:
                meta[k] = kwargs.pop(k)

        if self._doc_type.index:
            meta.setdefault('_index', self._doc_type.index)
        super(AttrDict, self).__setattr__('meta', HitMeta(meta))

        super(DocType, self).__init__(**kwargs)

    def __getstate__(self):
        return (self.to_dict(), self.meta._d_)

    def __setstate__(self, state):
        data, meta = state
        super(AttrDict, self).__setattr__('_d_', data)
        super(AttrDict, self).__setattr__('meta', HitMeta(meta))

    def __getattr__(self, name):
        if name.startswith('_') and name[1:] in META_FIELDS:
            return getattr(self.meta, name[1:])
        return super(DocType, self).__getattr__(name)

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % (key, getattr(self.meta, key)) for key in
                      ('index', 'doc_type', 'id') if key in self.meta)
        )

    def __setattr__(self, name, value):
        if name.startswith('_') and name[1:] in META_FIELDS:
            return setattr(self.meta, name[1:], value)
        return super(DocType, self).__setattr__(name, value)

    @classmethod
    def init(cls, index=None, using=None):
        """
        Create the index and populate the mappings in elasticsearch.
        """
        cls._doc_type.init(index, using)

    @classmethod
    def search(cls, using=None, index=None):
        """
        Create an :class:`~elasticsearch_dsl.Search` instance that will search
        over this ``DocType``.
        """
        return Search(
            using=using or cls._doc_type.using,
            index=index or cls._doc_type.index,
            doc_type=[cls]
        )

    @classmethod
    def get(cls, id, using=None, index=None, **kwargs):
        """
        Retrieve a single document from elasticsearch using it's ``id``.

        :arg id: ``id`` of the document to be retireved
        :arg index: elasticsearch index to use, if the ``DocType`` is
            associated with an index this can be omitted.
        :arg using: connection alias to use, defaults to ``'default'``

        Any additional keyword arguments will be passed to
        ``Elasticsearch.get`` unchanged.
        """
        es = connections.get_connection(using or cls._doc_type.using)
        doc = es.get(
            index=index or cls._doc_type.index,
            doc_type=cls._doc_type.name,
            id=id,
            **kwargs
        )
        if not doc.get('found', False):
            return None
        return cls.from_es(doc)

    @classmethod
    def mget(cls, docs, using=None, index=None, raise_on_error=True,
             missing='none', **kwargs):
        """
        Retrieve multiple document by their ``id``\s. Returns a list of instances
        in the same order as requested.

        :arg docs: list of ``id``\s of the documents to be retireved or a list
            of document specifications as per
            https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-multi-get.html
        :arg index: elasticsearch index to use, if the ``DocType`` is
            associated with an index this can be omitted.
        :arg using: connection alias to use, defaults to ``'default'``
        :arg missing: what to do when one of the documents requested is not
            found. Valid options are ``'none'`` (use ``None``), ``'raise'`` (raise
            ``NotFoundError``) or ``'skip'`` (ignore the missing document).

        Any additional keyword arguments will be passed to
        ``Elasticsearch.mget`` unchanged.
        """
        if missing not in ('raise', 'skip', 'none'):
            raise ValueError("'missing' must be 'raise', 'skip', or 'none'.")
        es = connections.get_connection(using or cls._doc_type.using)
        body = {
            'docs': [
                doc if isinstance(doc, collections.Mapping) else {'_id': doc}
                for doc in docs
            ]
        }
        results = es.mget(
            body,
            index=index or cls._doc_type.index,
            doc_type=cls._doc_type.name,
            **kwargs
        )

        objs, error_docs, missing_docs = [], [], []
        for doc in results['docs']:
            if doc.get('found'):
                if error_docs or missing_docs:
                    # We're going to raise an exception anyway, so avoid an
                    # expensive call to cls.from_es().
                    continue

                objs.append(cls.from_es(doc))

            elif doc.get('error'):
                if raise_on_error:
                    error_docs.append(doc)
                if missing == 'none':
                    objs.append(None)

            # The doc didn't cause an error, but the doc also wasn't found.
            elif missing == 'raise':
                missing_docs.append(doc)
            elif missing == 'none':
                objs.append(None)

        if error_docs:
            error_ids = [doc['_id'] for doc in error_docs]
            message = 'Required routing/parent not provided for documents %s.'
            message %= ', '.join(error_ids)
            raise RequestError(400, message, error_docs)
        if missing_docs:
            missing_ids = [doc['_id'] for doc in missing_docs]
            message = 'Documents %s not found.' % ', '.join(missing_ids)
            raise NotFoundError(404, message, {'docs': missing_docs})
        return objs

    def _get_connection(self, using=None):
        return connections.get_connection(using or self._doc_type.using)
    connection = property(_get_connection)

    def _get_index(self, index=None):
        if index is None:
            index = getattr(self.meta, 'index', self._doc_type.index)
        if index is None:
            raise ValidationException('No index')
        return index

    def delete(self, using=None, index=None, **kwargs):
        """
        Delete the instance in elasticsearch.

        :arg index: elasticsearch index to use, if the ``DocType`` is
            associated with an index this can be omitted.
        :arg using: connection alias to use, defaults to ``'default'``

        Any additional keyword arguments will be passed to
        ``Elasticsearch.delete`` unchanged.
        """
        es = self._get_connection(using)
        # extract parent, routing etc from meta
        doc_meta = dict(
            (k, self.meta[k])
            for k in DOC_META_FIELDS
            if k in self.meta
        )
        doc_meta.update(kwargs)
        es.delete(
            index=self._get_index(index),
            doc_type=self._doc_type.name,
            **doc_meta
        )

    def to_dict(self, include_meta=False):
        """
        Serialize the instance into a dictionary so that it can be saved in elasticsearch.

        :arg include_meta: if set to ``True`` will include all the metadata
            (``_index``, ``_type``, ``_id`` etc). Otherwise just the document's
            data is serialized. This is useful when passing multiple instances into
            ``elasticsearch.helpers.bulk``.
        """
        d = super(DocType, self).to_dict()
        if not include_meta:
            return d

        meta = dict(
            ('_' + k, self.meta[k])
            for k in DOC_META_FIELDS
            if k in self.meta
        )

        # in case of to_dict include the index unlike save/update/delete
        if 'index' in self.meta:
            meta['_index'] = self.meta.index
        elif self._doc_type.index:
            meta['_index'] = self._doc_type.index

        meta['_type'] = self._doc_type.name
        meta['_source'] = d
        return meta

    def update(self, using=None, index=None,  detect_noop=True, doc_as_upsert=False, **fields):
        """
        Partial update of the document, specify fields you wish to update and
        both the instance and the document in elasticsearch will be updated::

            doc = MyDocument(title='Document Title!')
            doc.save()
            doc.update(title='New Document Title!')

        :arg index: elasticsearch index to use, if the ``DocType`` is
            associated with an index this can be omitted.
        :arg using: connection alias to use, defaults to ``'default'``

        Any additional keyword arguments will be passed to
        ``Elasticsearch.update`` unchanged.
        """
        if not fields:
            raise IllegalOperation('You cannot call update() without updating individual fields. '
                                   'If you wish to update the entire object use save().')

        es = self._get_connection(using)

        # update given fields locally
        merge(self, fields)

        # prepare data for ES
        values = self.to_dict()

        # if fields were given: partial update
        doc = dict(
            (k, values.get(k))
            for k in fields.keys()
        )

        # extract parent, routing etc from meta
        doc_meta = dict(
            (k, self.meta[k])
            for k in DOC_META_FIELDS
            if k in self.meta
        )
        body = {
            'doc': doc,
            'doc_as_upsert': doc_as_upsert,
            'detect_noop': detect_noop,
        }

        meta = es.update(
            index=self._get_index(index),
            doc_type=self._doc_type.name,
            body=body,
            **doc_meta
        )
        # update meta information from ES
        for k in META_FIELDS:
            if '_' + k in meta:
                setattr(self.meta, k, meta['_' + k])

    def save(self, using=None, index=None, validate=True, **kwargs):
        """
        Save the document into elasticsearch. If the document doesn't exist it
        is created, it is overwritten otherwise. Returns ``True`` if this
        operations resulted in new document being created.

        :arg index: elasticsearch index to use, if the ``DocType`` is
            associated with an index this can be omitted.
        :arg using: connection alias to use, defaults to ``'default'``
        :arg validate: set to ``False`` to skip validating the document

        Any additional keyword arguments will be passed to
        ``Elasticsearch.index`` unchanged.
        """
        if validate:
            self.full_clean()

        es = self._get_connection(using)
        # extract parent, routing etc from meta
        doc_meta = dict(
            (k, self.meta[k])
            for k in DOC_META_FIELDS
            if k in self.meta
        )
        doc_meta.update(kwargs)
        meta = es.index(
            index=self._get_index(index),
            doc_type=self._doc_type.name,
            body=self.to_dict(),
            **doc_meta
        )
        # update meta information from ES
        for k in META_FIELDS:
            if '_' + k in meta:
                setattr(self.meta, k, meta['_' + k])

        # return True/False if the document has been created/updated
        return meta['result'] == 'created'
