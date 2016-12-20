from __future__ import absolute_import, unicode_literals

import copy
import json

from django.db import models
from django.utils.crypto import get_random_string
from django.utils.six.moves.urllib.parse import urlparse
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk

from .base import (
    BaseSearchBackend, BaseSearchQuery, BaseSearchResults)
from ..index import (
    FilterField, Indexed, RelatedFields, SearchField, class_is_indexed)


class ElasticsearchMapping(object):
    type_map = {
        'AutoField': 'integer',
        'BinaryField': 'binary',
        'BooleanField': 'boolean',
        'CharField': 'string',
        'CommaSeparatedIntegerField': 'string',
        'DateField': 'date',
        'DateTimeField': 'date',
        'DecimalField': 'double',
        'FileField': 'string',
        'FilePathField': 'string',
        'FloatField': 'double',
        'IntegerField': 'integer',
        'BigIntegerField': 'long',
        'IPAddressField': 'string',
        'GenericIPAddressField': 'string',
        'NullBooleanField': 'boolean',
        'OneToOneField': 'integer',
        'PositiveIntegerField': 'integer',
        'PositiveSmallIntegerField': 'integer',
        'SlugField': 'string',
        'SmallIntegerField': 'integer',
        'TextField': 'string',
        'TimeField': 'date',
    }

    keyword_type = 'string'
    text_type = 'string'
    set_index_not_analyzed_on_filter_fields = True

    # Contains the configuration required to use the edgengram_analyzer
    # on a field. It's different in Elasticsearch 2 so it's been put in
    # an attribute here to make it easier to override in a subclass.
    edgengram_analyzer_config = {
        'index_analyzer': 'edgengram_analyzer',
    }

    def __init__(self, model):
        self.model = model

    def get_parent(self):
        for base in self.model.__bases__:
            if issubclass(base, Indexed) and issubclass(base, models.Model):
                return type(self)(base)

    def get_document_type(self):
        return self.model.indexed_get_content_type()

    def get_field_column_name(self, field):
        if isinstance(field, FilterField):
            return field.get_attname(self.model) + '_filter'
        elif isinstance(field, SearchField):
            return field.get_attname(self.model)
        elif isinstance(field, RelatedFields):
            return field.field_name

    def get_field_mapping(self, field):
        if isinstance(field, RelatedFields):
            mapping = {'type': 'nested', 'properties': {}}
            nested_model = field.get_field(self.model).related_model
            nested_mapping = type(self)(nested_model)

            for sub_field in field.fields:
                sub_field_name, sub_field_mapping = nested_mapping.get_field_mapping(sub_field)
                mapping['properties'][sub_field_name] = sub_field_mapping

            return self.get_field_column_name(field), mapping
        else:
            mapping = {'type': self.type_map.get(field.get_type(self.model), 'string')}

            if isinstance(field, SearchField):
                if mapping['type'] == 'string':
                    mapping['type'] = self.text_type

                if field.boost:
                    mapping['boost'] = field.boost

                if field.partial_match:
                    mapping.update(self.edgengram_analyzer_config)

                mapping['include_in_all'] = True

            elif isinstance(field, FilterField):
                if mapping['type'] == 'string':
                    mapping['type'] = self.keyword_type

                if self.set_index_not_analyzed_on_filter_fields:
                    # Not required on ES5 as that uses the "keyword" type for
                    # filtered string fields
                    mapping['index'] = 'not_analyzed'

                mapping['include_in_all'] = False

            if 'es_extra' in field.kwargs:
                for key, value in field.kwargs['es_extra'].items():
                    mapping[key] = value

            return self.get_field_column_name(field), mapping

    def get_mapping(self):
        # Make field list
        fields = {
            'pk': dict(type=self.keyword_type, store=True, include_in_all=False),
            'content_type': dict(type=self.keyword_type, include_in_all=False),
            '_partials': dict(type=self.text_type, include_in_all=False),
        }
        fields['_partials'].update(self.edgengram_analyzer_config)

        if self.set_index_not_analyzed_on_filter_fields:
            # Not required on ES5 as that uses the "keyword" type for
            # filtered string fields
            fields['pk']['index'] = 'not_analyzed'
            fields['content_type']['index'] = 'not_analyzed'

        fields.update(dict(
            self.get_field_mapping(field) for field in self.model.get_search_fields()
        ))
        return {
            self.get_document_type(): {
                'properties': fields,
            }
        }

    def get_document_id(self, obj):
        return obj.indexed_get_toplevel_content_type() + ':' + str(obj.pk)

    def _get_nested_document(self, fields, obj):
        doc = {}
        partials = []
        model = type(obj)
        mapping = type(self)(model)

        for field in fields:
            value = field.get_value(obj)
            doc[mapping.get_field_column_name(field)] = value

            # Check if this field should be added into _partials
            if isinstance(field, SearchField) and field.partial_match:
                partials.append(value)

        return doc, partials

    def get_document(self, obj):
        # Build document
        doc = dict(pk=str(obj.pk), content_type=self.model.indexed_get_content_type())
        partials = []
        for field in self.model.get_search_fields():
            value = field.get_value(obj)

            if isinstance(field, RelatedFields):
                if isinstance(value, models.Manager):
                    nested_docs = []

                    for nested_obj in value.all():
                        nested_doc, extra_partials = self._get_nested_document(field.fields, nested_obj)
                        nested_docs.append(nested_doc)
                        partials.extend(extra_partials)

                    value = nested_docs
                elif isinstance(value, models.Model):
                    value, extra_partials = self._get_nested_document(field.fields, value)
                    partials.extend(extra_partials)

            doc[self.get_field_column_name(field)] = value

            # Check if this field should be added into _partials
            if isinstance(field, SearchField) and field.partial_match:
                partials.append(value)

        # Add partials to document
        doc['_partials'] = partials

        return doc

    def __repr__(self):
        return '<ElasticsearchMapping: %s>' % (self.model.__name__, )


class ElasticsearchSearchQuery(BaseSearchQuery):
    mapping_class = ElasticsearchMapping
    DEFAULT_OPERATOR = 'or'

    def __init__(self, *args, **kwargs):
        super(ElasticsearchSearchQuery, self).__init__(*args, **kwargs)
        self.mapping = self.mapping_class(self.queryset.model)

        # Convert field names into index column names
        if self.fields:
            fields = []
            searchable_fields = {f.field_name: f for f in self.queryset.model.get_searchable_search_fields()}
            for field_name in self.fields:
                if field_name in searchable_fields:
                    field_name = self.mapping.get_field_column_name(searchable_fields[field_name])

                fields.append(field_name)

            self.fields = fields

    def _process_lookup(self, field, lookup, value):
        column_name = self.mapping.get_field_column_name(field)

        if lookup == 'exact':
            if value is None:
                return {
                    'missing': {
                        'field': column_name,
                    }
                }
            else:
                return {
                    'term': {
                        column_name: value,
                    }
                }

        if lookup == 'isnull':
            if value:
                return {
                    'missing': {
                        'field': column_name,
                    }
                }
            else:
                return {
                    'exists': {
                        'field': column_name,
                    }
                }

        if lookup in ['startswith', 'prefix']:
            return {
                'prefix': {
                    column_name: value,
                }
            }

        if lookup in ['gt', 'gte', 'lt', 'lte']:
            return {
                'range': {
                    column_name: {
                        lookup: value,
                    }
                }
            }

        if lookup == 'range':
            lower, upper = value

            return {
                'range': {
                    column_name: {
                        'gte': lower,
                        'lte': upper,
                    }
                }
            }

        if lookup == 'in':
            return {
                'terms': {
                    column_name: list(value),
                }
            }

    def _connect_filters(self, filters, connector, negated):
        if filters:
            if len(filters) == 1:
                filter_out = filters[0]
            else:
                filter_out = {
                    connector.lower(): [
                        fil for fil in filters if fil is not None
                    ]
                }

            if negated:
                filter_out = {
                    'not': filter_out
                }

            return filter_out

    def get_inner_query(self):
        if self.query_string is not None:
            fields = self.fields or ['_all', '_partials']

            if len(fields) == 1:
                if self.operator == 'or':
                    query = {
                        'match': {
                            fields[0]: self.query_string,
                        }
                    }
                else:
                    query = {
                        'match': {
                            fields[0]: {
                                'query': self.query_string,
                                'operator': self.operator,
                            }
                        }
                    }
            else:
                query = {
                    'multi_match': {
                        'query': self.query_string,
                        'fields': fields,
                    }
                }

                if self.operator != 'or':
                    query['multi_match']['operator'] = self.operator
        else:
            query = {
                'match_all': {}
            }

        return query

    def get_content_type_filter(self):
        return {
            'prefix': {
                'content_type': self.queryset.model.indexed_get_content_type()
            }
        }

    def get_filters(self):
        filters = []

        # Filter by content type
        filters.append(self.get_content_type_filter())

        # Apply filters from queryset
        queryset_filters = self._get_filters_from_queryset()
        if queryset_filters:
            filters.append(queryset_filters)

        return filters

    def get_query(self):
        inner_query = self.get_inner_query()
        filters = self.get_filters()

        if len(filters) == 1:
            return {
                'filtered': {
                    'query': inner_query,
                    'filter': filters[0],
                }
            }
        elif len(filters) > 1:
            return {
                'filtered': {
                    'query': inner_query,
                    'filter': {
                        'and': filters,
                    }
                }
            }
        else:
            return inner_query

    def get_sort(self):
        # Ordering by relevance is the default in Elasticsearch
        if self.order_by_relevance:
            return

        # Get queryset and make sure its ordered
        if self.queryset.ordered:
            order_by_fields = self.queryset.query.order_by
            sort = []

            for order_by_field in order_by_fields:
                reverse = False
                field_name = order_by_field

                if order_by_field.startswith('-'):
                    reverse = True
                    field_name = order_by_field[1:]

                field = self._get_filterable_field(field_name)
                column_name = self.mapping.get_field_column_name(field)

                sort.append({
                    column_name: 'desc' if reverse else 'asc'
                })

            return sort

        else:
            # Order by pk field
            return ['pk']

    def __repr__(self):
        return json.dumps(self.get_query())


class ElasticsearchSearchResults(BaseSearchResults):
    fields_param_name = 'fields'

    def _get_es_body(self, for_count=False):
        body = {
            'query': self.query.get_query()
        }

        if not for_count:
            sort = self.query.get_sort()

            if sort is not None:
                body['sort'] = sort

        return body

    def _do_search(self):
        # Params for elasticsearch query
        params = dict(
            index=self.backend.get_index_for_model(self.query.queryset.model).name,
            body=self._get_es_body(),
            _source=False,
            from_=self.start,
        )

        params[self.fields_param_name] = 'pk'

        # Add size if set
        if self.stop is not None:
            params['size'] = self.stop - self.start
        # Send to Elasticsearch
        hits = self.backend.es.search(**params)

        # Get pks from results
        pks = [hit['fields']['pk'][0] for hit in hits['hits']['hits']]
        scores = {str(hit['fields']['pk'][0]): hit['_score'] for hit in hits['hits']['hits']}

        # Initialise results dictionary
        results = dict((str(pk), None) for pk in pks)

        # Find objects in database and add them to dict
        queryset = self.query.queryset.filter(pk__in=pks)
        for obj in queryset:
            results[str(obj.pk)] = obj

            if self._score_field:
                setattr(obj, self._score_field, scores.get(str(obj.pk)))

        # Return results in order given by Elasticsearch
        return [results[str(pk)] for pk in pks if results[str(pk)]]

    def _do_count(self):
        # Get count
        hit_count = self.backend.es.count(
            index=self.backend.get_index_for_model(self.query.queryset.model).name,
            body=self._get_es_body(for_count=True),
        )['count']
        # Add limits
        hit_count -= self.start
        if self.stop is not None:
            hit_count = min(hit_count, self.stop - self.start)

        return max(hit_count, 0)


class ElasticsearchIndex(object):
    def __init__(self, backend, name):
        self.backend = backend
        self.es = backend.es
        self.mapping_class = backend.mapping_class
        self.name = name

    def put(self):
        self.es.indices.create(self.name, self.backend.settings)

    def delete(self):
        try:
            self.es.indices.delete(self.name)
        except NotFoundError:
            pass

    def exists(self):
        return self.es.indices.exists(self.name)

    def is_alias(self):
        return self.es.indices.exists_alias(self.name)

    def aliased_indices(self):
        """
        If this index object represents an alias (which appear the same in the
        Elasticsearch API), this method can be used to fetch the list of indices
        the alias points to.

        Use the is_alias method if you need to find out if this an alias. This
        returns an empty list if called on an index.
        """
        return [
            self.backend.index_class(self.backend, index_name)
            for index_name in self.es.indices.get_alias(name=self.name).keys()
        ]

    def put_alias(self, name):
        """
        Creates a new alias to this index. If the alias already exists it will
        be repointed to this index.
        """
        self.es.indices.put_alias(name=name, index=self.name)

    def add_model(self, model):
        # Get mapping
        mapping = self.mapping_class(model)

        # Put mapping
        self.es.indices.put_mapping(
            index=self.name, doc_type=mapping.get_document_type(), body=mapping.get_mapping()
        )

    def add_item(self, item):
        # Make sure the object can be indexed
        if not class_is_indexed(item.__class__):
            return

        # Get mapping
        mapping = self.mapping_class(item.__class__)

        # Add document to index
        self.es.index(
            self.name, mapping.get_document_type(), mapping.get_document(item), id=mapping.get_document_id(item)
        )

    def add_items(self, model, items):
        if not class_is_indexed(model):
            return

        # Get mapping
        mapping = self.mapping_class(model)
        doc_type = mapping.get_document_type()

        # Create list of actions
        actions = []
        for item in items:
            # Create the action
            action = {
                '_index': self.name,
                '_type': doc_type,
                '_id': mapping.get_document_id(item),
            }
            action.update(mapping.get_document(item))
            actions.append(action)

        # Run the actions
        bulk(self.es, actions)

    def delete_item(self, item):
        # Make sure the object can be indexed
        if not class_is_indexed(item.__class__):
            return

        # Get mapping
        mapping = self.mapping_class(item.__class__)

        # Delete document
        try:
            self.es.delete(
                self.name,
                mapping.get_document_type(),
                mapping.get_document_id(item),
            )
        except NotFoundError:
            pass  # Document doesn't exist, ignore this exception

    def refresh(self):
        self.es.indices.refresh(self.name)

    def reset(self):
        # Delete old index
        self.delete()

        # Create new index
        self.put()


class ElasticsearchIndexRebuilder(object):
    def __init__(self, index):
        self.index = index

    def reset_index(self):
        self.index.reset()

    def start(self):
        # Reset the index
        self.reset_index()

        return self.index

    def finish(self):
        self.index.refresh()


class ElasticsearchAtomicIndexRebuilder(ElasticsearchIndexRebuilder):
    def __init__(self, index):
        self.alias = index
        self.index = index.backend.index_class(
            index.backend,
            self.alias.name + '_' + get_random_string(7).lower()
        )

    def reset_index(self):
        # Delete old index using the alias
        # This should delete both the alias and the index
        self.alias.delete()

        # Create new index
        self.index.put()

        # Create a new alias
        self.index.put_alias(self.alias.name)

    def start(self):
        # Create the new index
        self.index.put()

        return self.index

    def finish(self):
        self.index.refresh()

        if self.alias.is_alias():
            # Update existing alias, then delete the old index

            # Find index that alias currently points to, we'll delete it after
            # updating the alias
            old_index = self.alias.aliased_indices()

            # Update alias to point to new index
            self.index.put_alias(self.alias.name)

            # Delete old index
            # aliased_indices() can return multiple indices. Delete them all
            for index in old_index:
                if index.name != self.index.name:
                    index.delete()

        else:
            # self.alias doesn't currently refer to an alias in Elasticsearch.
            # This means that either nothing exists in ES with that name or
            # there is currently an index with the that name

            # Run delete on the alias, just in case it is currently an index.
            # This happens on the first rebuild after switching ATOMIC_REBUILD on
            self.alias.delete()

            # Create the alias
            self.index.put_alias(self.alias.name)


class ElasticsearchSearchBackend(BaseSearchBackend):
    index_class = ElasticsearchIndex
    query_class = ElasticsearchSearchQuery
    results_class = ElasticsearchSearchResults
    mapping_class = ElasticsearchMapping
    basic_rebuilder_class = ElasticsearchIndexRebuilder
    atomic_rebuilder_class = ElasticsearchAtomicIndexRebuilder

    settings = {
        'settings': {
            'analysis': {
                'analyzer': {
                    'ngram_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'lowercase',
                        'filter': ['asciifolding', 'ngram']
                    },
                    'edgengram_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'lowercase',
                        'filter': ['asciifolding', 'edgengram']
                    }
                },
                'tokenizer': {
                    'ngram_tokenizer': {
                        'type': 'nGram',
                        'min_gram': 3,
                        'max_gram': 15,
                    },
                    'edgengram_tokenizer': {
                        'type': 'edgeNGram',
                        'min_gram': 2,
                        'max_gram': 15,
                        'side': 'front'
                    }
                },
                'filter': {
                    'ngram': {
                        'type': 'nGram',
                        'min_gram': 3,
                        'max_gram': 15
                    },
                    'edgengram': {
                        'type': 'edgeNGram',
                        'min_gram': 1,
                        'max_gram': 15
                    }
                }
            }
        }
    }

    def __init__(self, params):
        super(ElasticsearchSearchBackend, self).__init__(params)

        # Get settings
        self.hosts = params.pop('HOSTS', None)
        self.index_name = params.pop('INDEX', 'wagtail')
        self.timeout = params.pop('TIMEOUT', 10)

        if params.pop('ATOMIC_REBUILD', False):
            self.rebuilder_class = self.atomic_rebuilder_class
        else:
            self.rebuilder_class = self.basic_rebuilder_class

        # If HOSTS is not set, convert URLS setting to HOSTS
        es_urls = params.pop('URLS', ['http://localhost:9200'])
        if self.hosts is None:
            self.hosts = []

            for url in es_urls:
                parsed_url = urlparse(url)

                use_ssl = parsed_url.scheme == 'https'
                port = parsed_url.port or (443 if use_ssl else 80)

                http_auth = None
                if parsed_url.username is not None and parsed_url.password is not None:
                    http_auth = (parsed_url.username, parsed_url.password)

                self.hosts.append({
                    'host': parsed_url.hostname,
                    'port': port,
                    'url_prefix': parsed_url.path,
                    'use_ssl': use_ssl,
                    'verify_certs': use_ssl,
                    'http_auth': http_auth,
                })

        self.settings = copy.deepcopy(self.settings)

        # Get Elasticsearch interface
        # Any remaining params are passed into the Elasticsearch constructor
        options = params.pop('OPTIONS', {})
        self.es = Elasticsearch(
            hosts=self.hosts,
            timeout=self.timeout,
            **options)

    def get_index_for_model(self, model):
        return self.index_class(self, self.index_name)

    def get_index(self):
        return self.index_class(self, self.index_name)

    def get_rebuilder(self):
        return self.rebuilder_class(self.get_index())

    def reset_index(self):
        # Use the rebuilder to reset the index
        self.get_rebuilder().reset_index()

    def add_type(self, model):
        self.get_index_for_model(model).add_model(model)

    def refresh_index(self):
        self.get_index().refresh()

    def add(self, obj):
        self.get_index_for_model(type(obj)).add_item(obj)

    def add_bulk(self, model, obj_list):
        self.get_index_for_model(model).add_items(model, obj_list)

    def delete(self, obj):
        self.get_index_for_model(type(obj)).delete_item(obj)


SearchBackend = ElasticsearchSearchBackend
