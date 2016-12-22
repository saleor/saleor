
from __future__ import absolute_import, unicode_literals

from django.db.models.lookups import Lookup
from django.db.models.query import QuerySet
from django.db.models.sql.where import SubqueryConstraint, WhereNode
from django.utils.six import text_type


class FilterError(Exception):
    pass


class FieldError(Exception):
    pass


class BaseSearchQuery(object):
    DEFAULT_OPERATOR = 'or'

    def __init__(self, queryset, query_string, fields=None, operator=None, order_by_relevance=True):
        self.queryset = queryset
        self.query_string = query_string
        self.fields = fields
        self.operator = operator or self.DEFAULT_OPERATOR
        self.order_by_relevance = order_by_relevance

    def _get_filterable_field(self, field_attname):
        # Get field
        field = dict(
            (field.get_attname(self.queryset.model), field)
            for field in self.queryset.model.get_filterable_search_fields()
        ).get(field_attname, None)

        return field

    def _process_lookup(self, field, lookup, value):
        raise NotImplementedError

    def _connect_filters(self, filters, connector, negated):
        raise NotImplementedError

    def _process_filter(self, field_attname, lookup, value):
        # Get the field
        field = self._get_filterable_field(field_attname)

        if field is None:
            raise FieldError(
                'Cannot filter search results with field "' + field_attname + '". Please add index.FilterField(\'' +
                field_attname + '\') to ' + self.queryset.model.__name__ + '.search_fields.'
            )

        # Process the lookup
        result = self._process_lookup(field, lookup, value)

        if result is None:
            raise FilterError(
                'Could not apply filter on search results: "' + field_attname + '__' +
                lookup + ' = ' + text_type(value) + '". Lookup "' + lookup + '"" not recognised.'
            )

        return result

    def _get_filters_from_where_node(self, where_node):
        # Check if this is a leaf node
        if isinstance(where_node, Lookup):
            field_attname = where_node.lhs.target.attname
            lookup = where_node.lookup_name
            value = where_node.rhs

            # Ignore pointer fields that show up in specific page type queries
            if field_attname.endswith('_ptr_id'):
                return

            # Process the filter
            return self._process_filter(field_attname, lookup, value)

        elif isinstance(where_node, SubqueryConstraint):
            raise FilterError('Could not apply filter on search results: Subqueries are not allowed.')

        elif isinstance(where_node, WhereNode):
            # Get child filters
            connector = where_node.connector
            child_filters = [self._get_filters_from_where_node(child) for child in where_node.children]
            child_filters = [child_filter for child_filter in child_filters if child_filter]

            return self._connect_filters(child_filters, connector, where_node.negated)

        else:
            raise FilterError('Could not apply filter on search results: Unknown where node: ' + str(type(where_node)))

    def _get_filters_from_queryset(self):
        return self._get_filters_from_where_node(self.queryset.query.where)


class BaseSearchResults(object):
    def __init__(self, backend, query, prefetch_related=None):
        self.backend = backend
        self.query = query
        self.prefetch_related = prefetch_related
        self.start = 0
        self.stop = None
        self._results_cache = None
        self._count_cache = None
        self._score_field = None

    def _set_limits(self, start=None, stop=None):
        if stop is not None:
            if self.stop is not None:
                self.stop = min(self.stop, self.start + stop)
            else:
                self.stop = self.start + stop

        if start is not None:
            if self.stop is not None:
                self.start = min(self.stop, self.start + start)
            else:
                self.start = self.start + start

    def _clone(self):
        klass = self.__class__
        new = klass(self.backend, self.query, prefetch_related=self.prefetch_related)
        new.start = self.start
        new.stop = self.stop
        return new

    def _do_search(self):
        raise NotImplementedError

    def _do_count(self):
        raise NotImplementedError

    def results(self):
        if self._results_cache is None:
            self._results_cache = self._do_search()
        return self._results_cache

    def count(self):
        if self._count_cache is None:
            if self._results_cache is not None:
                self._count_cache = len(self._results_cache)
            else:
                self._count_cache = self._do_count()
        return self._count_cache

    def __getitem__(self, key):
        new = self._clone()

        if isinstance(key, slice):
            # Set limits
            start = int(key.start) if key.start else None
            stop = int(key.stop) if key.stop else None
            new._set_limits(start, stop)

            # Copy results cache
            if self._results_cache is not None:
                new._results_cache = self._results_cache[key]

            return new
        else:
            if self._results_cache is not None:
                return self._results_cache[key]

            new.start = self.start + key
            new.stop = self.start + key + 1
            return list(new)[0]

    def __iter__(self):
        return iter(self.results())

    def __len__(self):
        return len(self.results())

    def __repr__(self):
        data = list(self[:21])
        if len(data) > 20:
            data[-1] = "...(remaining elements truncated)..."
        return '<SearchResults %r>' % data

    def annotate_score(self, field_name):
        clone = self._clone()
        clone._score_field = field_name
        return clone


class BaseSearchBackend(object):
    query_class = None
    results_class = None
    rebuilder_class = None

    def __init__(self, params):
        pass

    def get_index_for_model(self, model):
        return None

    def get_rebuilder(self):
        return None

    def reset_index(self):
        raise NotImplementedError

    def add_type(self, model):
        raise NotImplementedError

    def refresh_index(self):
        raise NotImplementedError

    def add(self, obj):
        raise NotImplementedError

    def add_bulk(self, model, obj_list):
        raise NotImplementedError

    def delete(self, obj):
        raise NotImplementedError

    def search(self, query_string, model_or_queryset, fields=None, filters=None,
               prefetch_related=None, operator=None, order_by_relevance=True):
        # Find model/queryset
        if isinstance(model_or_queryset, QuerySet):
            model = model_or_queryset.model
            queryset = model_or_queryset
        else:
            model = model_or_queryset
            queryset = model_or_queryset.objects.all()

        # # Model must be a class that is in the index
        # if not class_is_indexed(model):
        #     return []

        # Check that theres still a query string after the clean up
        if query_string == "":
            return []

        # Only fields that are indexed as a SearchField can be passed in fields
        if fields:
            allowed_fields = {field.field_name for field in model.get_searchable_search_fields()}

            for field_name in fields:
                if field_name not in allowed_fields:
                    raise FieldError(
                        'Cannot search with field "' + field_name + '". Please add index.SearchField(\'' +
                        field_name + '\') to ' + model.__name__ + '.search_fields.'
                    )

        # Apply filters to queryset
        if filters:
            queryset = queryset.filter(**filters)

        # Prefetch related
        if prefetch_related:
            for prefetch in prefetch_related:
                queryset = queryset.prefetch_related(prefetch)

        # Check operator
        if operator is not None:
            operator = operator.lower()
            if operator not in ['or', 'and']:
                raise ValueError("operator must be either 'or' or 'and'")

        # Search
        search_query = self.query_class(
            queryset, query_string, fields=fields, operator=operator, order_by_relevance=order_by_relevance
        )
        return self.results_class(self, search_query)
