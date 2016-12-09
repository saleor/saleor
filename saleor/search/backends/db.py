from __future__ import absolute_import, unicode_literals

from django.db import models
from django.db.models.expressions import Value

from .base import (
    BaseSearchBackend, BaseSearchQuery, BaseSearchResults)


class DatabaseSearchQuery(BaseSearchQuery):
    DEFAULT_OPERATOR = 'and'

    def _process_lookup(self, field, lookup, value):
        return models.Q(**{field.get_attname(self.queryset.model) + '__' + lookup: value})

    def _connect_filters(self, filters, connector, negated):
        if connector == 'AND':
            q = models.Q(*filters)
        elif connector == 'OR':
            q = models.Q(filters[0])
            for fil in filters[1:]:
                q |= fil
        else:
            return

        if negated:
            q = ~q

        return q

    def get_extra_q(self):
        # Run _get_filters_from_queryset to test that no fields that are not
        # a FilterField have been used in the query.
        self._get_filters_from_queryset()

        q = models.Q()
        model = self.queryset.model

        if self.query_string is not None:
            # Get fields
            fields = self.fields or [field.field_name for field in model.get_searchable_search_fields()]

            # Get terms
            terms = self.query_string.split()
            if not terms:
                return model.objects.none()

            # Filter by terms
            for term in terms:
                term_query = models.Q()
                for field_name in fields:
                    # Check if the field exists (this will filter out indexed callables)
                    try:
                        model._meta.get_field(field_name)
                    except models.fields.FieldDoesNotExist:
                        continue

                    # Filter on this field
                    term_query |= models.Q(**{'%s__icontains' % field_name: term})

                if self.operator == 'or':
                    q |= term_query
                elif self.operator == 'and':
                    q &= term_query

        return q


class DatabaseSearchResults(BaseSearchResults):
    def get_queryset(self):
        queryset = self.query.queryset
        q = self.query.get_extra_q()

        return queryset.filter(q).distinct()[self.start:self.stop]

    def _do_search(self):
        queryset = self.get_queryset()

        if self._score_field:
            queryset = queryset.annotate(**{self._score_field: Value(None, output_field=models.FloatField())})

        return queryset

    def _do_count(self):
        return self.get_queryset().count()


class DatabaseSearchBackend(BaseSearchBackend):
    query_class = DatabaseSearchQuery
    results_class = DatabaseSearchResults

    def __init__(self, params):
        super(DatabaseSearchBackend, self).__init__(params)

    def reset_index(self):
        pass  # Not needed

    def add_type(self, model):
        pass  # Not needed

    def refresh_index(self):
        pass  # Not needed

    def add(self, obj):
        pass  # Not needed

    def add_bulk(self, model, obj_list):
        return  # Not needed

    def delete(self, obj):
        pass  # Not needed


SearchBackend = DatabaseSearchBackend
